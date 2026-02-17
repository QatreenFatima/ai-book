"""Ingestion pipeline: read MDX docs, chunk by headings, embed via OpenRouter, upsert to Qdrant."""

import argparse
import os
import re
import uuid
from pathlib import Path

import frontmatter
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
COLLECTION_NAME = "physical-ai-book"
VECTOR_SIZE = None  # auto-detected from first embedding call
MAX_CHUNK_TOKENS = 600
OVERLAP_TOKENS = 100

encoder = tiktoken.get_encoding("cl100k_base")

openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def parse_mdx(file_path: Path) -> tuple[dict, str]:
    """Parse an MDX file and return (metadata, cleaned markdown content)."""
    post = frontmatter.load(str(file_path))
    content = post.content

    # Strip MDX import lines (import ... from '...')
    content = re.sub(r"^import\s+.+$", "", content, flags=re.MULTILINE)
    # Strip JSX component tags like <ComponentName ... /> or <Component>...</Component>
    content = re.sub(r"<[A-Z]\w+[^>]*/?>", "", content)
    content = re.sub(r"</[A-Z]\w+>", "", content)

    return dict(post.metadata), content.strip()


def split_by_headings(content: str) -> list[tuple[str, str]]:
    """Split markdown into (section_title, section_text) pairs by ## headings."""
    # Match ## or ### headings
    pattern = r"^(#{2,3})\s+(.+)$"
    sections: list[tuple[str, str]] = []
    current_title = "Introduction"
    current_text_parts: list[str] = []

    for line in content.split("\n"):
        match = re.match(pattern, line)
        if match:
            # Save previous section
            if current_text_parts:
                sections.append((current_title, "\n".join(current_text_parts).strip()))
            current_title = match.group(2).strip()
            current_text_parts = []
        else:
            current_text_parts.append(line)

    # Save last section
    if current_text_parts:
        sections.append((current_title, "\n".join(current_text_parts).strip()))

    return [(title, text) for title, text in sections if text]


def chunk_section(title: str, text: str) -> list[tuple[str, str]]:
    """Split a section into chunks of max MAX_CHUNK_TOKENS tokens with overlap."""
    tokens = count_tokens(text)
    if tokens <= MAX_CHUNK_TOKENS:
        return [(title, text)]

    # Split by paragraphs (double newline)
    paragraphs = re.split(r"\n\n+", text)
    chunks: list[tuple[str, str]] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if current_tokens + para_tokens > MAX_CHUNK_TOKENS and current_parts:
            chunk_text = "\n\n".join(current_parts)
            chunks.append((title, chunk_text))

            # Overlap: keep last paragraph(s) up to OVERLAP_TOKENS
            overlap_parts: list[str] = []
            overlap_count = 0
            for p in reversed(current_parts):
                p_tokens = count_tokens(p)
                if overlap_count + p_tokens > OVERLAP_TOKENS:
                    break
                overlap_parts.insert(0, p)
                overlap_count += p_tokens

            current_parts = overlap_parts + [para]
            current_tokens = overlap_count + para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    if current_parts:
        chunks.append((title, "\n\n".join(current_parts)))

    return chunks


def detect_vector_size() -> int:
    """Detect embedding dimension by running a test embedding."""
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=["test"])
    return len(response.data[0].embedding)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via OpenRouter embeddings endpoint."""
    # OpenRouter may have batch limits; process in groups of 20
    all_embeddings: list[list[float]] = []
    batch_size = 20

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def ensure_collection(reset: bool = False) -> None:
    """Create Qdrant collection if it does not exist. Recreate if reset=True."""
    collections = [c.name for c in qdrant_client.get_collections().collections]

    if reset and COLLECTION_NAME in collections:
        print(f"  Deleting existing collection '{COLLECTION_NAME}'...")
        qdrant_client.delete_collection(COLLECTION_NAME)
        collections.remove(COLLECTION_NAME)

    if COLLECTION_NAME not in collections:
        print(f"  Creating collection '{COLLECTION_NAME}' (vector_size={VECTOR_SIZE}, distance=COSINE)...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    else:
        print(f"  Collection '{COLLECTION_NAME}' already exists (use --reset to recreate)")


def upsert_chunks(
    chunks: list[tuple[str, str]],
    embeddings: list[list[float]],
    source: str,
    page_title: str,
) -> int:
    """Upsert chunk vectors to Qdrant with metadata payload."""
    points = []
    for idx, ((section_title, text), embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": text,
                "source": source,
                "section_title": section_title,
                "page_title": page_title,
                "chunk_index": idx,
            },
        )
        points.append(point)

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return len(points)


def ingest_file(file_path: Path, docs_root: Path) -> tuple[int, list[str]]:
    """Process a single MDX file: parse, chunk, embed, upsert. Returns (chunks_created, errors)."""
    errors: list[str] = []
    relative_path = str(file_path.relative_to(docs_root))

    metadata, content = parse_mdx(file_path)
    page_title = metadata.get("title", file_path.stem)

    sections = split_by_headings(content)
    if not sections:
        return 0, [f"No sections found in {relative_path}"]

    # Chunk all sections
    all_chunks: list[tuple[str, str]] = []
    for title, text in sections:
        all_chunks.extend(chunk_section(title, text))

    if not all_chunks:
        return 0, [f"No chunks produced from {relative_path}"]

    # Embed all chunk texts
    chunk_texts = [text for _, text in all_chunks]
    try:
        embeddings = embed_texts(chunk_texts)
    except Exception as e:
        return 0, [f"Embedding failed for {relative_path}: {e}"]

    if len(embeddings) != len(all_chunks):
        return 0, [f"Embedding count mismatch for {relative_path}: {len(embeddings)} vs {len(all_chunks)}"]

    # Upsert to Qdrant
    try:
        count = upsert_chunks(all_chunks, embeddings, relative_path, page_title)
    except Exception as e:
        return 0, [f"Qdrant upsert failed for {relative_path}: {e}"]

    return count, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest book MDX files into Qdrant vector database")
    parser.add_argument("--docs-path", required=True, help="Path to docs/ directory containing .mdx files")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the Qdrant collection before ingesting")
    args = parser.parse_args()

    docs_path = Path(args.docs_path).resolve()
    if not docs_path.is_dir():
        print(f"Error: '{docs_path}' is not a directory")
        return

    mdx_files = sorted(docs_path.glob("*.mdx"))
    if not mdx_files:
        print(f"No .mdx files found in {docs_path}")
        return

    print(f"Found {len(mdx_files)} MDX files in {docs_path}")
    print(f"Embedding model: {EMBEDDING_MODEL}")

    # Auto-detect vector size
    global VECTOR_SIZE
    print("Detecting embedding dimension...", end=" ")
    VECTOR_SIZE = detect_vector_size()
    print(f"{VECTOR_SIZE}")
    print(f"Collection: {COLLECTION_NAME} (vector_size={VECTOR_SIZE})")
    print()

    # Ensure Qdrant collection exists
    print("[1/3] Setting up Qdrant collection...")
    ensure_collection(reset=args.reset)
    print()

    # Process each file
    print("[2/3] Processing files...")
    total_chunks = 0
    total_errors: list[str] = []

    for i, mdx_file in enumerate(mdx_files, 1):
        relative = mdx_file.relative_to(docs_path)
        print(f"  [{i}/{len(mdx_files)}] {relative}...", end=" ")

        chunks_created, errors = ingest_file(mdx_file, docs_path)
        total_chunks += chunks_created
        total_errors.extend(errors)

        if errors:
            print(f"ERRORS: {errors}")
        else:
            print(f"{chunks_created} chunks")

    # Summary
    print()
    print("[3/3] Ingestion complete!")
    print(f"  Files processed: {len(mdx_files)}")
    print(f"  Chunks created:  {total_chunks}")
    print(f"  Errors:          {len(total_errors)}")

    if total_errors:
        print("\nErrors:")
        for err in total_errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
