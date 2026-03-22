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
  const [isProceedingToFeedback, setIsProceedingToFeedback] = useState(false);

  // Debug: system prompt viewer
  const [isDebug, setIsDebug] = useState(false);
  const [showPromptDialog, setShowPromptDialog] = useState(false);
  const [systemPromptInfo, setSystemPromptInfo] = useState<{ chat_type: string; system_message: string; user_for_the_chat: string | null } | null>(null);
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Debug: friends-info viewer
  const [showFriendsDialog, setShowFriendsDialog] = useState(false);
  const [friendsInfo, setFriendsInfo] = useState<{ persona: string; similarity_score: number; selected_accounts: string[]; joint_accounts: { account: string; category: string }[] } | null>(null);
  const [friendsLoading, setFriendsLoading] = useState(false);
  const [friendsAvailable, setFriendsAvailable] = useState(false);

  // Debug: top-5 similar personas viewer
  type TopPersona = { index: number; screen_name: string; description: string; similarity: number; joint_categories: number; joint_users: number };
  type PersonaPreview = { persona_index: number; screen_name: string; description: string; chat_type: string; system_prompt: string; selected_accounts: string[]; joint_accounts: { account: string; category: string }[] };
  const [showTopPersonasDialog, setShowTopPersonasDialog] = useState(false);
  const [topPersonas, setTopPersonas] = useState<TopPersona[]>([]);
  const [topPersonasLoading, setTopPersonasLoading] = useState(false);
  const [topPersonasError, setTopPersonasError] = useState<string | null>(null);
  const [showPersonaPreviewDialog, setShowPersonaPreviewDialog] = useState(false);
  const [personaPreview, setPersonaPreview] = useState<PersonaPreview | null>(null);
  const [personaPreviewLoading, setPersonaPreviewLoading] = useState<number | null>(null);

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
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Debug API error ${res.status}: ${err?.detail ?? res.statusText}`);
      }
    } catch (e) {
      alert(`Debug fetch failed: ${e}`);
    } finally {
      setFriendsLoading(false);
    }
  };

  const handleShowSystemPrompt = async () => {
    if (!session?.session_id) return;
    setPromptLoading(true);
    setPromptError(null);
    try {
      const res = await fetch(`${API_URL}/api/debug/system-prompt/${session.session_id}`);
      if (res.ok) {
        setSystemPromptInfo(await res.json());
        setShowPromptDialog(true);
      } else {
        const err = await res.json().catch(() => ({}));
        setPromptError(`Error ${res.status}: ${err?.detail ?? res.statusText}`);
      }
    } catch (e) {
      setPromptError(`Fetch failed: ${e}`);
    } finally {
      setPromptLoading(false);
    }
  };

  const handleShowTopPersonas = async () => {
    if (!session?.session_id) return;
    setTopPersonasLoading(true);
    setTopPersonasError(null);
    try {
      const res = await fetch(`${API_URL}/api/debug/personas/${session.session_id}?n=5`);
      if (res.ok) {
        const data = await res.json();
        setTopPersonas(data.personas);
        setShowTopPersonasDialog(true);
      } else {
        const err = await res.json().catch(() => ({}));
        setTopPersonasError(`Error ${res.status}: ${err?.detail ?? res.statusText}`);
      }
    } catch (e) {
      setTopPersonasError(`Fetch failed: ${e}`);
    } finally {
      setTopPersonasLoading(false);
    }
  };

  const handleViewPersonaPreview = async (personaIndex: number) => {
    if (!session?.session_id) return;
    setPersonaPreviewLoading(personaIndex);
    try {
      const res = await fetch(`${API_URL}/api/debug/persona-preview/${session.session_id}/${personaIndex}`);
      if (res.ok) {
        setPersonaPreview(await res.json());
        setShowPersonaPreviewDialog(true);
      }
    } finally {
      setPersonaPreviewLoading(null);
    }
  };

  const handleProceed = () => {
    if (isProceedingToFeedback) return;
    setIsProceedingToFeedback(true);
    router.push("/feedback");
  };

  if (!ready || !session) return null;

  if (isPreparing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
        <div className="w-16 h-16 rounded-full border-4 border-blue-200 border-t-blue-600 animate-spin" />
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
              <GradientButton
                onClick={handleProceed}
                className="w-full"
                disabled={isProceedingToFeedback}
              >
                {isProceedingToFeedback ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin inline-block" />
                    Preparing feedback...
                  </span>
                ) : (
                  "✨ Continue to Feedback"
                )}
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
            <div className="mt-6 pt-4 border-t border-dashed border-gray-400">
              <p className="text-xs text-gray-400 mb-2 font-mono">🛠 Debug</p>
              <button
                onClick={handleShowSystemPrompt}
                disabled={promptLoading}
                className="w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-[0.625rem] transition-colors font-mono disabled:opacity-50"
              >
                {promptLoading ? "Loading..." : "View System Prompt"}
              </button>
              {promptError && <p className="mt-1 text-xs text-red-500 font-mono break-all">{promptError}</p>}
              {friendsAvailable && (
                <button
                  onClick={handleShowFriendsInfo}
                  disabled={friendsLoading}
                  className="mt-2 w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-[0.625rem] transition-colors font-mono disabled:opacity-50"
                >
                  {friendsLoading ? "Loading..." : "View Friends Overlap"}
                </button>
              )}
              <button
                onClick={handleShowTopPersonas}
                disabled={topPersonasLoading}
                className="mt-2 w-full text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-2 rounded-[0.625rem] transition-colors font-mono disabled:opacity-50"
              >
                {topPersonasLoading ? "Loading..." : "View Top 5 Similar Personas"}
              </button>
              {topPersonasError && <p className="mt-1 text-xs text-red-500 font-mono break-all">{topPersonasError}</p>}
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
              <span className="font-mono text-blue-700">{friendsInfo.persona}</span>
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
                  {friendsInfo.joint_accounts.map((item) => (
                    <li key={item.account} className="flex items-center justify-between gap-3">
                      <span className="font-mono text-xs text-gray-800">@{item.account}</span>
                      <span className="text-xs text-gray-400 truncate max-w-[55%] text-right">{item.category}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </Dialog>
      )}

      {/* Debug: top-5 similar personas dialog */}
      <Dialog open={showTopPersonasDialog} onClose={() => setShowTopPersonasDialog(false)} title="🛠 Top 5 Similar Personas" className="max-w-3xl" confirmLabel="Close">
        <div className="space-y-2 text-sm">
          {topPersonas.length === 0 ? (
            <p className="text-xs text-gray-400 italic">No personas found.</p>
          ) : (
            <ul className="flex flex-col">
              {topPersonas.map((p, i) => (
                <li key={p.index}>
                  <button
                    onClick={() => handleViewPersonaPreview(p.index)}
                    disabled={personaPreviewLoading === p.index}
                    className="w-full text-left bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg px-3 py-2 transition-colors disabled:opacity-50"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-xs font-bold text-gray-400 w-4 shrink-0">#{i + 1}</span>
                        <span className="font-mono text-xs text-blue-700 truncate">@{p.screen_name}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 font-mono text-xs text-gray-500">
                        {personaPreviewLoading === p.index ? (
                          <span>…</span>
                        ) : (
                          <>
                            {p.joint_categories > 0 && (
                              <span title="joint categories / joint users" className="text-green-600">{p.joint_categories}cat/{p.joint_users}usr</span>
                            )}
                            <span>{p.similarity.toFixed(4)}</span>
                          </>
                        )}
                      </div>
                    </div>
                    {p.description && (
                      <p className="text-xs text-gray-500 mt-0.5 pl-6 line-clamp-1">{p.description}</p>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-gray-400 pt-1">Click a persona to view its system prompt and friends overlap.</p>
        </div>
      </Dialog>

      {/* Debug: persona preview dialog (system prompt + friends overlap) */}
      {personaPreview && (
        <Dialog open={showPersonaPreviewDialog} onClose={() => setShowPersonaPreviewDialog(false)} title={`🛠 Persona Preview — @${personaPreview.screen_name}`} className="max-w-3xl" confirmLabel="Close">
          <div className="space-y-3 text-sm">
            {personaPreview.description && (
              <div className="flex gap-2">
                <span className="font-semibold text-gray-500 w-24 shrink-0">Description:</span>
                <span className="text-gray-700">{personaPreview.description}</span>
              </div>
            )}
            <div className="flex gap-2">
              <span className="font-semibold text-gray-500 w-24 shrink-0">Chat type:</span>
              <span className="font-mono text-purple-700">{personaPreview.chat_type}</span>
            </div>
            <div>
              <p className="font-semibold text-gray-500 mb-1">System prompt:</p>
              {personaPreview.system_prompt ? (
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-800 whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
                  {personaPreview.system_prompt}
                </pre>
              ) : (
                <p className="text-xs text-gray-400 italic">(empty – vanilla mode)</p>
              )}
            </div>
            <div>
              <p className="font-semibold text-gray-500 mb-1">
                Joint accounts ({personaPreview.joint_accounts.length} of {personaPreview.selected_accounts.length} selected):
              </p>
              {personaPreview.joint_accounts.length === 0 ? (
                <p className="text-xs text-gray-400 italic">None</p>
              ) : (
                <ul className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-1 max-h-40 overflow-y-auto">
                  {personaPreview.joint_accounts.map((item) => (
                    <li key={item.account} className="flex items-center justify-between gap-3">
                      <span className="font-mono text-xs text-gray-800">@{item.account}</span>
                      <span className="text-xs text-gray-400 truncate max-w-[55%] text-right">{item.category}</span>
                    </li>
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
