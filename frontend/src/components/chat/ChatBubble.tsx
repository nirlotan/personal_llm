// ChatBubble – individual message (human 🐨 / AI 🐼).
"use client";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
}

export default function ChatBubble({ role, content }: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <span className="text-2xl flex-shrink-0 mt-1">
        {isUser ? "🐨" : "🐼"}
      </span>
      <div
        className={`max-w-[75%] rounded-2xl px-5 py-3 ${
          isUser ? "chat-bubble-user" : "chat-bubble-ai"
        }`}
      >
        <p className="text-gray-800 whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}
