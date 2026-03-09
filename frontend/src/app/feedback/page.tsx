// Feedback page (Step 3) – ported from pages/submit_feedback.py.
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import SurveyForm from "@/components/feedback/SurveyForm";
import Dialog from "@/components/ui/Dialog";
import { useSession } from "@/hooks/useSession";
import { resetChat, prepareChat, getSessionInfo } from "@/lib/api";
import type { FeedbackResponse } from "@/lib/types";

export default function FeedbackPage() {
  const router = useRouter();
  const { session, ready } = useSession();
  const [showDialog, setShowDialog] = useState(true);
  const [hasMoreChats, setHasMoreChats] = useState<boolean | null>(null);

  useEffect(() => {
    if (ready && !session) router.push("/");
  }, [ready, session, router]);

  // Fetch remaining chat count so we can conditionally show the dialog hint
  useEffect(() => {
    if (ready && session?.session_id) {
      getSessionInfo(session.session_id)
        .then((info) => setHasMoreChats(info.remaining_chat_types_count > 1))
        .catch(() => setHasMoreChats(false));
    }
  }, [ready, session?.session_id]);

  const handleSubmit = async (result: FeedbackResponse) => {
    if (!result.attention_passed) {
      router.push("/missed-attention");
      return;
    }

    if (result.remaining_chats > 0 && session) {
      // Reset chat and prepare for round 2
      await resetChat(session.session_id);
      await prepareChat(session.session_id);
      router.push("/chat");
    } else {
      // No more chats remaining — go straight to thank-you
      router.push("/thank-you");
    }
  };

  if (!ready || !session) return null;

  return (
    <>
      <header className="text-center mb-10 w-full max-w-3xl">
        <h1 className="text-[28px] font-bold text-brand-dark mb-2 tracking-tight">
          Share Your Feedback
        </h1>
        <p className="text-gray-600 text-base">
          Please rate your experience chatting with the language model.
        </p>
      </header>

      <Dialog
        open={showDialog}
        onClose={() => setShowDialog(false)}
        title="Feedback"
      >
        <p>Now please share with us your feedback about your experience chatting with <strong>the chatbot</strong>.</p>
        {hasMoreChats && (
          <p className="mt-2">After the feedback you&apos;ll be asked to chat with another (different) chatbot.</p>
        )}
      </Dialog>

      <SurveyForm sessionId={session.session_id} onSubmit={handleSubmit} />
    </>
  );
}
