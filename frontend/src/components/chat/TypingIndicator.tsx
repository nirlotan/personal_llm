// TypingIndicator – animated dots during LLM response.
"use client";

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <span className="text-2xl flex-shrink-0 mt-1">🐼</span>
      <div className="chat-bubble-ai rounded-2xl px-5 py-3">
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
