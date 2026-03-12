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
import { getChatMessages } from "@/lib/api";
import { MIN_MESSAGES, API_URL } from "@/lib/constants";

export default function ChatPage() {
  const router = useRouter();
  const { session, ready } = useSession();
  const chat = useChat(session?.session_id);

  const [showDialog, setShowDialog] = useState(true);
  const [chatRound, setChatRound] = useState(1); // 1 or 2
  const [isPreparing, setIsPreparing] = useState(false);

  // Debug: system prompt viewer
  const [isDebug, setIsDebug] = useState(false);
  const [showPromptDialog, setShowPromptDialog] = useState(false);
  const [systemPromptInfo, setSystemPromptInfo] = useState<{ chat_type: string; system_message: string; user_for_the_chat: string | null } | null>(null);
  const [promptLoading, setPromptLoading] = useState(false);

  // Debug: friends-info viewer
  const [showFriendsDialog, setShowFriendsDialog] = useState(false);
  const [friendsInfo, setFriendsInfo] = useState<{ persona: string; similarity_score: number; selected_accounts: string[]; joint_accounts: string[] } | null>(null);
  const [friendsLoading, setFriendsLoading] = useState(false);
  const [friendsAvailable, setFriendsAvailable] = useState(false);

  // Redirect if no session (wait until localStorage is read first)
  useEffect(() => {
    if (ready && !session) {
      router.push("/");
    }
  }, [ready, session, router]);

  // On mount: prepare fresh chat or resume existing one
  useEffect(() => {
    if (!ready || !session?.session_id) return;
    const sessionId = session.session_id;
    getChatMessages(sessionId).then((msgRes) => {
      if (msgRes.messages.length === 0) {
        // Fresh start — prepare the chat (picks persona, builds prompt, injects first message)
        setIsPreparing(true);
        chat.prepare().finally(() => setIsPreparing(false));
      } else {
        // Resuming mid-conversation — hydrate existing state
        chat.initChat();
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, session?.session_id]);

  // Enable debug UI if the env var is set OR if the /debug page set the sessionStorage flag
  useEffect(() => {
    const envDebug = process.env.NEXT_PUBLIC_DEBUG_MODE === "true";
    const sessionDebug = sessionStorage.getItem("plm_debug") === "true";
    const debugOn = envDebug || sessionDebug;
    setIsDebug(debugOn);

    // Probe whether the friends-info endpoint is available (requires SIMILARITY_WITH_FRIENDS=true)
    if (debugOn && session?.session_id) {
      fetch(`${API_URL}/api/debug/friends-info/${session.session_id}`)
        .then((r) => setFriendsAvailable(r.status !== 403))
        .catch(() => setFriendsAvailable(false));
    }
  }, [session?.session_id]);

  const handleShowFriendsInfo = async () => {
    if (!session?.session_id) return;
    setFriendsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/debug/friends-info/${session.session_id}`);
      if (res.ok) {
        setFriendsInfo(await res.json());
        setShowFriendsDialog(true);
      }
    } finally {
      setFriendsLoading(false);
    }
  };

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

  if (isPreparing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
        <div className="w-16 h-16 rounded-full border-4 border-purple-200 border-t-purple-600 animate-spin" />
        <div className="text-center">
          <p className="text-xl font-semibold text-brand-dark mb-1">Preparing your chat...</p>
          <p className="text-gray-500 text-sm">This may take a few seconds. Please wait.</p>
        </div>
      </div>
    );
  }

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
              {friendsAvailable && (
                <button
                  onClick={handleShowFriendsInfo}
                  disabled={friendsLoading}
                  className="mt-2 w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-lg transition-colors font-mono disabled:opacity-50"
                >
                  {friendsLoading ? "Loading..." : "View Friends Overlap"}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Debug: friends overlap dialog */}
      {friendsInfo && (
        <Dialog open={showFriendsDialog} onClose={() => setShowFriendsDialog(false)} title="🛠 Friends Overlap">
          <div className="space-y-3 text-sm">
            <div className="flex gap-2">
              <span className="font-semibold text-gray-500 w-28 shrink-0">Persona:</span>
              <span className="font-mono text-purple-700">{friendsInfo.persona}</span>
            </div>
            <div className="flex gap-2">
              <span className="font-semibold text-gray-500 w-28 shrink-0">Similarity:</span>
              <span className="font-mono text-gray-700">{friendsInfo.similarity_score}</span>
            </div>
            <div>
              <p className="font-semibold text-gray-500 mb-1">
                Joint accounts ({friendsInfo.joint_accounts.length} of {friendsInfo.selected_accounts.length} selected):
              </p>
              {friendsInfo.joint_accounts.length === 0 ? (
                <p className="text-xs text-gray-400 italic">None – persona was selected from full set (fallback).</p>
              ) : (
                <ul className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-1 max-h-60 overflow-y-auto">
                  {friendsInfo.joint_accounts.map((acc) => (
                    <li key={acc} className="font-mono text-xs text-gray-800">@{acc}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </Dialog>
      )}

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
