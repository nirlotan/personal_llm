// Thank-you page – ported from pages/thank_you.py.
"use client";

import { useEffect, useState } from "react";
import { useSession } from "@/hooks/useSession";
import { getCompletionInfo } from "@/lib/api";

export default function ThankYouPage() {
  const { session } = useSession();
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);
  const [sessionCode, setSessionCode] = useState<string>("");

  useEffect(() => {
    if (!session) return;

    const fallbackRedirect = () => {
      // Prolific session IDs follow the pattern pid__study__session.
      // If the backend is unreachable we can still redirect the user.
      if (session.session_id.includes("__")) {
        setRedirectUrl(
          `https://app.prolific.com/submissions/complete?cc=${process.env.NEXT_PUBLIC_PROLIFIC_APPROVAL ?? "C3KTZS0A"}`
        );
      }
      setSessionCode(session.session_id);
    };

    getCompletionInfo(session.session_id)
      .then((info) => {
        setRedirectUrl(info.redirect_url);
        setSessionCode(info.session_id);
        // If backend returned null redirect_url but user is from Prolific, apply fallback
        if (!info.redirect_url && session.session_id.includes("__")) {
          fallbackRedirect();
        }
      })
      .catch(() => {
        fallbackRedirect();
      });
  }, [session]);

  return (
    <div className="text-center space-y-6">
      <h1 className="text-3xl font-bold text-brand-dark">
        Thank you very much for your participation! 🎉
      </h1>

      {redirectUrl ? (
        <a
          href={redirectUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-gradient inline-block text-white px-10 py-3.5 rounded-full font-semibold text-lg"
        >
          Click here to be redirected to Prolific to get your credit
        </a>
      ) : (
        <div className="glass-panel p-6 max-w-lg mx-auto">
          <p className="text-gray-700 mb-3">
            There was an issue crediting you on Prolific. Please send us this code to get credited:
          </p>
          <code className="block bg-white/50 p-3 rounded-lg text-purple-700 font-mono text-sm select-all">
            {sessionCode}
          </code>
        </div>
      )}
    </div>
  );
}
