import React, { useState, useRef, useEffect, useCallback } from "react";
import { useChat } from "./ChatProvider";
import "@site/src/css/chat.css";

export default function ChatWidget() {
  const {
    messages,
    isOpen,
    setIsOpen,
    isLoading,
    error,
    setError,
    selectedText,
    setSelectedText,
    sendMessage,
    startNewChat,
  } = useChat();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  // Text selection detection
  useEffect(() => {
    const handleMouseUp = () => {
      const sel = window.getSelection()?.toString().trim();
      if (sel && sel.length > 10) {
        setSelectedText(sel);
      }
    };

    document.addEventListener("mouseup", handleMouseUp);
    return () => document.removeEventListener("mouseup", handleMouseUp);
  }, [setSelectedText]);

  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!input.trim() || isLoading) return;
      if (input.length > 2000) {
        setError("Message exceeds 2000 character limit");
        return;
      }
      sendMessage(input.trim());
      setInput("");
    },
    [input, isLoading, sendMessage, setError]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <>
      {/* Floating chat bubble */}
      {!isOpen && (
        <button
          className="chat-bubble"
          onClick={() => setIsOpen(true)}
          aria-label="Open chat assistant"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="chat-panel">
          {/* Header */}
          <div className="chat-header">
            <span className="chat-title">Book Assistant</span>
            <div className="chat-header-actions">
              <button
                className="chat-header-btn"
                onClick={startNewChat}
                title="New chat"
                aria-label="Start new chat"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              <button
                className="chat-header-btn"
                onClick={() => setIsOpen(false)}
                title="Close"
                aria-label="Close chat"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Selected text indicator */}
          {selectedText && (
            <div className="chat-selected-text">
              <span className="chat-selected-label">Asking about selected text:</span>
              <p className="chat-selected-preview">
                {selectedText.length > 100
                  ? selectedText.slice(0, 100) + "..."
                  : selectedText}
              </p>
              <button
                className="chat-selected-clear"
                onClick={() => setSelectedText(null)}
              >
                Clear selection
              </button>
            </div>
          )}

          {/* Messages */}
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <p>Ask me anything about the book!</p>
                <p className="chat-empty-hint">
                  You can also highlight text on the page to ask about it.
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message chat-message-${msg.role}`}>
                <div className="chat-message-content">
                  {msg.content || (isLoading && i === messages.length - 1 ? "..." : "")}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div className="chat-sources">
                    <span className="chat-sources-label">Sources:</span>
                    {msg.sources.map((s, j) => (
                      <span key={j} className="chat-source-tag">
                        {s.section_title || s.source}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Error */}
          {error && (
            <div className="chat-error">
              {error.includes("503") || error.includes("unavailable")
                ? "Service temporarily unavailable. Please try again later."
                : error}
              <button onClick={() => setError(null)} className="chat-error-dismiss">
                Dismiss
              </button>
            </div>
          )}

          {/* Input */}
          <form className="chat-input-area" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedText
                  ? "Ask about the selected text..."
                  : "Ask about the book..."
              }
              rows={1}
              maxLength={2000}
              disabled={isLoading}
            />
            {input.length > 1800 && (
              <span className="chat-char-count" style={{
                position: "absolute",
                bottom: "48px",
                right: "16px",
                fontSize: "10px",
                color: input.length > 2000 ? "#c53030" : "#a0a0a0",
              }}>
                {input.length}/2000
              </span>
            )}
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || isLoading || input.length > 2000}
              aria-label="Send message"
            >
              {isLoading ? (
                <span className="chat-spinner" />
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </form>
        </div>
      )}
    </>
  );
}
