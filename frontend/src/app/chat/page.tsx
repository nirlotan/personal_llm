// Chat page (Step 2) – ported from pages/chat.py.
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ChatWindow from "@/components/chat/ChatWindow";
import TaskChecklist from "@/components/chat/TaskChecklist";
import GradientButton from "@/components/ui/GradientButton";
import Dialog from "@/components/ui/Dialog";
import { useSession } from "@/hooks/useSession";
import { useChat } from "@/hooks/useChat";
import { MIN_MESSAGES, API_URL } from "@/lib/constants";

export default function ChatPage() {
  const router = useRouter();
  const { session, ready } = useSession();
  const chat = useChat(session?.session_id);

  const [showDialog, setShowDialog] = useState(true);
  const [chatRound, setChatRound] = useState(1); // 1 or 2

  // Debug: system prompt viewer
  const [isDebug, setIsDebug] = useState(false);
  const [showPromptDialog, setShowPromptDialog] = useState(false);
  const [systemPromptInfo, setSystemPromptInfo] = useState<{ chat_type: string; system_message: string; user_for_the_chat: string | null } | null>(null);
  const [promptLoading, setPromptLoading] = useState(false);

  // Redirect if no session (wait until localStorage is read first)
  useEffect(() => {
    if (ready && !session) {
      router.push("/");
    }
  }, [ready, session, router]);

  // Hydrate messages + status from backend on mount
  useEffect(() => {
    if (ready && session?.session_id) {
      chat.initChat();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, session?.session_id]);

  // Check debug flag from sessionStorage
  useEffect(() => {
    setIsDebug(sessionStorage.getItem("plm_debug") === "true");
  }, []);

  const handleShowSystemPrompt = async () => {
    if (!session?.session_id) return;
    setPromptLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/debug/system-prompt/${session.session_id}`);
      if (res.ok) {
        setSystemPromptInfo(await res.json());
        setShowPromptDialog(true);
      }
    } finally {
      setPromptLoading(false);
    }
  };

  const handleProceed = () => {
    router.push("/feedback");
  };

  if (!ready || !session) return null;

  return (
    <>
      <header className="text-center mb-6 w-full max-w-3xl">
        <h1 className="text-[28px] font-bold text-brand-dark mb-2 tracking-tight">
          Chat with the Language Model
        </h1>
        <p className="text-gray-600 text-sm">
          Complete all 3 task types and send at least {MIN_MESSAGES} messages to proceed.
        </p>
      </header>

      {/* First chat dialog */}
      <Dialog
        open={showDialog}
        onClose={() => setShowDialog(false)}
        title={chatRound === 1 ? "Conversation with a Language Model" : "We're almost there..."}
      >
        {chatRound === 1 ? (
          <>
            <p>Next, you&apos;ll chat with a large language model, exchanging a few messages.</p>
            <p className="mt-2 font-semibold">This is chatbot {chatRound} of 2.</p>
            <div className="mt-3 space-y-1 text-sm">
              <p>You <strong>need to</strong> complete these tasks:</p>
              <ol className="list-decimal list-inside">
                <li>Have a <strong>casual conversation</strong></li>
                <li>Ask for a <strong>recommendation</strong></li>
                <li>Request <strong>factual information</strong></li>
              </ol>
            </div>
            <div className="mt-3 text-xs bg-orange-50 p-2 rounded-lg">
              📌 The chatbot is <strong>not</strong> up-to-date with current events.
            </div>
            <div className="mt-2 text-xs bg-green-50 p-2 rounded-lg">
              💡 Read the messages. You&apos;ll be asked about the experience.
            </div>
          </>
        ) : (
          <p><strong>One more chat</strong> (with a different bot), and after getting your feedback on this bot — you are done!</p>
        )}
      </Dialog>

      <div className="flex gap-6 w-full max-w-5xl">
        {/* Chat window */}
        <div className="flex-1">
          <ChatWindow
            messages={chat.messages}
            sending={chat.sending}
            onSend={chat.sendMessage}
          />
        </div>

        {/* Sidebar: task checklist */}
        <div className="w-64 flex-shrink-0">
          {chat.status && (
            <TaskChecklist
              tasks={chat.status.tasks}
              messageCount={chat.status.message_count}
              minMessages={MIN_MESSAGES}
            />
          )}

          {chat.status?.can_proceed && (
            <div className="mt-4">
              <GradientButton onClick={handleProceed} className="w-full">
                ✨ Continue to Feedback
              </GradientButton>
            </div>
          )}

          {chat.status &&
            chat.status.message_count >= MIN_MESSAGES &&
            !chat.status.can_proceed && (
              <div className="mt-4 text-sm text-orange-600 bg-orange-50 p-3 rounded-xl">
                ⚠️ Complete all tasks before proceeding.
              </div>
            )}

          {/* Debug: system prompt viewer */}
          {isDebug && (
            <div className="mt-6 pt-4 border-t border-dashed border-gray-300">
              <p className="text-xs text-gray-400 mb-2 font-mono">🛠 Debug</p>
              <button
                onClick={handleShowSystemPrompt}
                disabled={promptLoading}
                className="w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-lg transition-colors font-mono disabled:opacity-50"
              >
                {promptLoading ? "Loading..." : "View System Prompt"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Debug: system prompt dialog */}
      {systemPromptInfo && (
        <Dialog open={showPromptDialog} onClose={() => setShowPromptDialog(false)} title="🛠 System Prompt">
          <div className="space-y-2 text-sm">
            <div className="flex gap-2">
              <span className="font-semibold text-gray-500 w-24 shrink-0">Chat type:</span>
              <span className="font-mono text-purple-700">{systemPromptInfo.chat_type}</span>
            </div>
            {systemPromptInfo.user_for_the_chat && (
              <div className="flex gap-2">
                <span className="font-semibold text-gray-500 w-24 shrink-0">Persona:</span>
                <span className="font-mono text-gray-700">{systemPromptInfo.user_for_the_chat}</span>
              </div>
            )}
            <div className="mt-3">
              <p className="font-semibold text-gray-500 mb-1">Prompt:</p>
              <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-800 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                {systemPromptInfo.system_message}
              </pre>
            </div>
          </div>
        </Dialog>
      )}
    </>
  );
}
