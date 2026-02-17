import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { BACKEND_URL } from "@site/src/config";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: { source: string; section_title: string; score: number }[];
}

interface ChatContextType {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  sessionId: string | null;
  setSessionId: React.Dispatch<React.SetStateAction<string | null>>;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  isLoading: boolean;
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  selectedText: string | null;
  setSelectedText: React.Dispatch<React.SetStateAction<string | null>>;
  sendMessage: (text: string) => Promise<void>;
  startNewChat: () => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function useChat(): ChatContextType {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedText, setSelectedText] = useState<string | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("chat-session-id");
    if (stored) {
      setSessionId(stored);
      // Load history
      fetch(`${BACKEND_URL}/api/sessions/${stored}/messages`)
        .then((res) => {
          if (res.ok) return res.json();
          // Session expired — clear
          localStorage.removeItem("chat-session-id");
          return null;
        })
        .then((data) => {
          if (data?.messages?.length) {
            setMessages(
              data.messages.map((m: any) => ({
                role: m.role,
                content: m.content,
                sources: m.sources || undefined,
              }))
            );
          }
        })
        .catch(() => {});
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      setError(null);
      setIsLoading(true);

      // Add user message immediately
      const userMsg: ChatMessage = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);

      // Prepare request body
      const body: any = { message: text };
      if (sessionId) body.session_id = sessionId;
      if (selectedText) body.selected_text = selectedText;

      try {
        const res = await fetch(`${BACKEND_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error (${res.status})`);
        }

        // Save session ID from response header
        const newSessionId = res.headers.get("X-Session-Id");
        if (newSessionId && newSessionId !== sessionId) {
          setSessionId(newSessionId);
          localStorage.setItem("chat-session-id", newSessionId);
        }

        // Read SSE stream
        const reader = res.body?.getReader();
        if (!reader) throw new Error("No response stream");

        const decoder = new TextDecoder();
        let assistantContent = "";
        let sources: ChatMessage["sources"] = undefined;

        // Add empty assistant message to fill in
        setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const lines = text.split("\n");

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();

            if (payload === "[DONE]") continue;

            try {
              const data = JSON.parse(payload);
              if (data.content) {
                assistantContent += data.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: "assistant",
                    content: assistantContent,
                    sources,
                  };
                  return updated;
                });
              }
              if (data.sources) {
                sources = data.sources;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    sources,
                  };
                  return updated;
                });
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }

        // Clear selected text after sending
        setSelectedText(null);
      } catch (err: any) {
        setError(err.message || "Something went wrong");
        // Remove the empty assistant message on error
        setMessages((prev) => {
          if (
            prev.length > 0 &&
            prev[prev.length - 1].role === "assistant" &&
            !prev[prev.length - 1].content
          ) {
            return prev.slice(0, -1);
          }
          return prev;
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, selectedText, isLoading]
  );

  const startNewChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setSelectedText(null);
    setError(null);
    localStorage.removeItem("chat-session-id");
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        sessionId,
        setSessionId,
        isOpen,
        setIsOpen,
        isLoading,
        setIsLoading,
        error,
        setError,
        selectedText,
        setSelectedText,
        sendMessage,
        startNewChat,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
