// ChatWindow – message list + input.
"use client";

import { useRef, useEffect, useState, FormEvent } from "react";
import ChatBubble from "./ChatBubble";
import TypingIndicator from "./TypingIndicator";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWindowProps {
  messages: Message[];
  sending: boolean;
  onSend: (content: string) => void;
  disabled?: boolean;
}

export default function ChatWindow({
  messages,
  sending,
  onSend,
  disabled = false,
}: ChatWindowProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Re-focus input after bot finishes responding (sending flips false)
  useEffect(() => {
    if (!sending && !disabled) {
      inputRef.current?.focus();
    }
  }, [sending, disabled]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <div className="glass-panel flex flex-col h-[65vh] w-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <ChatBubble key={i} role={msg.role} content={msg.content} />
        ))}
        {sending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-white/20 p-4 flex gap-3"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={disabled || sending}
          className="flex-1 rounded-full px-5 py-3 bg-white/40 backdrop-blur-sm border border-white/50 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || sending || disabled}
          className="btn-gradient text-white px-6 py-3 rounded-full font-semibold disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
