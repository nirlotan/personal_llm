// Debug panel – researcher tool for direct chat-type selection.
// Ported from pages/debug_chat.py.
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import GradientButton from "@/components/ui/GradientButton";
import { useSession } from "@/hooks/useSession";

const CHAT_TYPES = [
  { type: "vanilla", emoji: "🤖", title: "Vanilla", desc: "Experience standard AI assistance." },
  { type: "Personalized Like Me", emoji: "🪞", title: "Personalized Like Me", desc: "Chat that mirrors your style." },
  { type: "Personalized Random", emoji: "🎲", title: "Personalized Random", desc: "Unexpected, varied responses." },
  { type: "PERSONA_ref", emoji: "🎭", title: "PERSONA_ref", desc: "Adopt a specific persona." },
  { type: "SPC_ref", emoji: "✨", title: "SPC_ref", desc: "Special reference mode." },
];

export default function DebugPage() {
  const router = useRouter();
  const { startSession, clearSession } = useSession();
  const [loading, setLoading] = useState(false);

  const handleSelect = async (chatType: string) => {
    setLoading(true);
    try {
      // Always create a fresh session for each debug run so we never
      // reference a stale session that no longer exists on the backend.
      clearSession();
      const s = await startSession();
      const sid = s.session_id;

      // Mark this browser tab as a debug session so the chat page
      // can show the system-prompt button regardless of navigation path.
      sessionStorage.setItem("plm_debug", "true");

      if (chatType === "Personalized Like Me") {
        // Needs cold start — go to profile page
        router.push("/profile");
      } else {
        // Call debug prepare endpoint
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/debug/prepare-chat/${sid}?chat_type=${encodeURIComponent(chatType)}`,
          { method: "POST" }
        );
        if (res.ok) {
          router.push("/chat");
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="text-3xl font-bold text-brand-dark mb-10 text-center">
        Welcome to PersonaChat (Debug)
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 w-full max-w-5xl">
        {CHAT_TYPES.map(({ type, emoji, title, desc }) => (
          <button
            key={type}
            onClick={() => handleSelect(type)}
            disabled={loading}
            className="glass-panel p-6 flex flex-col items-center text-center hover:scale-105 transition-all cursor-pointer"
          >
            <span className="text-4xl mb-4">{emoji}</span>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
            <p className="text-sm text-gray-500">{desc}</p>
          </button>
        ))}
      </div>
    </>
  );
}
