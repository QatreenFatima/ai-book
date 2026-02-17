<!--
Sync Impact Report (2026-02-13)
===============================
Version change: [INITIAL] → 1.0.0
Created: Initial constitution for Physical AI & Humanoid Robotics Book project

Modified Principles:
- All principles newly defined for book authoring project

Added Sections:
- Core Principles (6 principles for technical book writing)
- Content Standards (quality gates for book content)
- Development Workflow (writing and review process)
- Governance (amendment and versioning policy)

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section compatible
✅ spec-template.md - User stories align with book chapters/modules
✅ tasks-template.md - Task structure supports book writing workflow

Follow-up TODOs:
- None - all placeholders resolved
-->

# Physical AI & Humanoid Robotics Book Constitution

## Core Principles

### I. Educational Clarity (NON-NEGOTIABLE)

Every section MUST be written for final-year university students with Python, basic AI/ML, and ROS knowledge. Content MUST:
- Use clear, jargon-free language (define technical terms on first use)
- Follow step-by-step progression (simple → complex)
- Include learning objectives at chapter start
- Provide "Common Pitfalls" warnings where students typically struggle
- End each major section with recap/summary

**Rationale**: Students learn best when material builds progressively without cognitive overload. Assumptions about prior knowledge must be explicit and limited to: Python 3.x, basic AI/ML concepts (supervised learning, neural networks), ROS 1/2 fundamentals.

### II. Docusaurus Markdown Compatibility (NON-NEGOTIABLE)

All content MUST use Docusaurus-compatible Markdown from initial drafting. This includes:
- Front matter with `id`, `title`, `sidebar_label`, `sidebar_position`
- Admonitions (`:::note`, `:::warning`, `:::tip`, `:::danger`) for callouts
- Code blocks with language tags and optional titles
- MDX support for interactive components (when needed)
- Proper heading hierarchy (h1 for title, h2 for major sections, etc.)

**Rationale**: Writing in the target format from the start prevents expensive conversion work and ensures technical features (syntax highlighting, live code demos) work correctly when published.

### III. Practical Code Examples (NON-NEGOTIABLE)

Every concept MUST include runnable, tested code with:
- Complete imports and dependencies listed
- Comments explaining non-obvious logic
- Expected output shown (console output, visualization, or behavior description)
- Environment requirements specified (ROS 2 Humble, Python 3.10+, GPU requirements, etc.)
- GitHub repository link for complete working examples

Code MUST NOT:
- Use placeholder values without explanation (e.g., `YOUR_API_KEY` must explain how to obtain)
- Skip error handling in production-oriented examples
- Assume undocumented dependencies

**Rationale**: Students need working code to learn by doing. Non-runnable pseudo-code creates frustration and blocks hands-on learning.

### IV. Visual Learning Through Diagrams

Complex concepts (system architecture, data flow, state machines, neural network layers) MUST include diagrams using:
- **Mermaid** for: flowcharts, sequence diagrams, state diagrams, class diagrams
- **PlantUML** for: component diagrams, deployment diagrams, complex UML
- **ASCII art** for: simple terminal-based visualizations in code comments

Diagrams MUST:
- Be embedded as code blocks (not image files) for version control and editability
- Include descriptive captions
- Reference specific code sections or system components
- Use consistent color/shape conventions throughout the book

**Rationale**: Robotics and AI systems are inherently multi-component and visual. Diagrams accelerate comprehension and provide mental models that text alone cannot.

### V. Module-Based Structure (NON-NEGOTIABLE)

Book organization MUST follow this exact quarter outline:
1. **Introduction**: Physical AI & Embodied Intelligence
2. **Module 1**: The Robotic Nervous System (ROS 2)
3. **Module 2**: The Digital Twin (Gazebo & Unity)
4. **Module 3**: The AI-Robot Brain (NVIDIA Isaac™)
5. **Module 4**: Vision-Language-Action (VLA)
6. **Capstone Project**: The Autonomous Humanoid

Each module MUST:
- Be independently completable (with clear prerequisites)
- Include hands-on exercises/labs
- Build toward the final capstone project
- Have estimated completion time (for student planning)

**Rationale**: Modular structure enables flexible teaching (semester/quarter/self-paced), allows students to focus on specific interests, and ensures each section delivers standalone value.

### VI. Technical Accuracy & Currency

All technical content MUST:
- Use current versions: ROS 2 Humble (LTS), Python 3.10+, NVIDIA Isaac Sim 4.x+, latest VLA models
- Cite official documentation and research papers where applicable
- Mark experimental/beta features explicitly
- Provide migration guidance when recommending newer tools over established ones
- Include version compatibility matrices for multi-tool setups

When trade-offs exist (e.g., simulation accuracy vs. performance), MUST:
- Present multiple valid approaches
- Explain trade-offs with concrete metrics (latency, memory, accuracy)
- Recommend default choice with clear reasoning

**Rationale**: Outdated content wastes student time and teaches bad practices. Robotics/AI fields evolve rapidly; the book must reflect production-ready, current best practices.

## Content Standards

### Code Quality

- All Python code follows PEP 8 style guide
- ROS 2 code follows ROS 2 style conventions
- C++ code (if any) follows Google C++ Style Guide
- Type hints required for Python functions with non-obvious signatures
- Docstrings for all public functions/classes (Google style)

### Diagram Standards

- Maximum diagram complexity: 10-12 nodes/components (split into multiple if larger)
- All nodes/components labeled clearly
- Data flow direction indicated with arrows
- Legend provided for color/shape meanings when not obvious
- Mermaid diagrams rendered and visually verified

### Warning Callouts

Use Docusaurus admonitions for:
- `:::warning` - Common mistakes, potential data loss, unsafe operations
- `:::caution` - Performance implications, resource requirements, compatibility issues
- `:::danger` - Security vulnerabilities, hardware damage risks, legal/ethical concerns
- `:::tip` - Best practices, optimization suggestions, pro tips
- `:::note` - Background information, related concepts, further reading

### Accessibility

- All diagrams include alt text descriptions
- Code examples include explanatory text before and after
- Avoid color-only differentiation (use shapes/patterns too)
- Keep sentences under 25 words where possible (readability)

## Development Workflow

### Writing Process

1. **Outline First**: Create detailed section outline with learning objectives
2. **Draft Core Content**: Write main explanatory text with placeholders for code/diagrams
3. **Add Code Examples**: Write, test, and document all code examples
4. **Create Diagrams**: Add Mermaid/PlantUML diagrams for visual concepts
5. **Review & Edit**: Self-review against constitution principles
6. **Validation**: Run all code examples, render all diagrams, check markdown validity

### Review Requirements

Before considering a chapter/module complete:
- [ ] All code examples tested and produce expected output
- [ ] All diagrams render correctly in Docusaurus
- [ ] Learning objectives stated and met
- [ ] Prerequisites clearly listed
- [ ] Estimated completion time provided
- [ ] Common pitfalls section included (where applicable)
- [ ] Cross-references to related chapters checked
- [ ] Markdown linting passed (no broken links, proper heading hierarchy)

### Quality Gates

- **Chapter Draft**: Learning objectives defined, outline complete
- **Chapter Alpha**: All sections written, code examples in place (may be untested)
- **Chapter Beta**: All code tested, diagrams complete, self-reviewed
- **Chapter Release**: External review passed, validation checklist complete

## Governance

### Amendment Procedure

This constitution can be amended when:
- Docusaurus version updates require markdown changes
- New tools/frameworks emerge as industry standards (e.g., ROS 3, new simulation platforms)
- Student feedback reveals systematic issues (e.g., unclear explanations, missing prerequisites)
- Technical reviewers identify accuracy issues

Amendments require:
1. Documented rationale for change
2. Version bump following semantic versioning
3. Update to this file with Sync Impact Report
4. Propagation to affected templates and content

### Versioning Policy

Constitution version follows MAJOR.MINOR.PATCH:
- **MAJOR**: Fundamental principle changes (e.g., change target audience, switch from Docusaurus)
- **MINOR**: Add new principle, expand existing principle with new requirements
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

All new book content (chapters, sections, code examples) MUST verify compliance with:
- Target audience appropriateness (final-year university students)
- Docusaurus markdown compatibility
- Code example completeness and runnability
- Diagram quality and clarity
- Module structure adherence

Non-compliance MUST be:
- Flagged immediately during writing/review
- Documented if intentional (with justification)
- Fixed before chapter moves to Beta stage

### Complexity Budget

To prevent scope creep:
- Maximum book length: 400 pages (estimated)
- Maximum module length: 60 pages
- Maximum code example length: 150 lines (split longer examples into multiple files)
- Maximum diagram complexity: 12 components per diagram

Exceeding these limits requires explicit justification and may indicate need to:
- Split into multiple sections
- Move detailed content to appendix
- Create supplementary GitHub repository with extended examples

**Version**: 1.0.0 | **Ratified**: 2026-02-13 | **Last Amended**: 2026-02-13
