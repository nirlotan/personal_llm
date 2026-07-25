// Thank-you page – ported from pages/thank_you.py.
"use client";

import { useEffect, useState } from "react";
import { useSession } from "@/hooks/useSession";
import { getCompletionInfo } from "@/lib/api";

export default function ThankYouPage() {
  const { session } = useSession();
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);
  const [sessionCode, setSessionCode] = useState<string>("");
  const [creditError, setCreditError] = useState<string | null>(null);
  const [completionLoaded, setCompletionLoaded] = useState(false);

  useEffect(() => {
    if (!session) return;
    setSessionCode(session.session_id);
    setCreditError(null);
    setCompletionLoaded(false);

    getCompletionInfo(session.session_id)
      .then((info) => {
        setRedirectUrl(info.redirect_url);
        setSessionCode(info.session_id);
        setCompletionLoaded(true);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unable to retrieve completion status";
        setCreditError(message);
        setRedirectUrl(null);
        setCompletionLoaded(true);
      });
  }, [session]);

  const isLikelyProlific = sessionCode.includes("__");

  return (
    <div className="text-center space-y-6">
      <h1 className="text-3xl font-bold text-brand-dark">
        Thank you very much for your participation! 🎉
      </h1>

      {redirectUrl ? (
        <a
          href={redirectUrl}
          className="btn-gradient inline-block text-white px-10 py-3.5 rounded-full font-semibold text-lg"
        >
          Click here to be redirected to Prolific to get your credit
        </a>
      ) : (
        <div className="glass-panel p-6 max-w-lg mx-auto">
          {creditError ? (
            <>
              <p className="text-gray-700 mb-3">You are not currently eligible for Prolific credit.</p>
              <p className="text-sm text-gray-600 mb-3">{creditError}</p>
              <p className="text-sm text-gray-600">
                If you believe this is a mistake, please contact the research team with your session ID.
              </p>
              <code className="block mt-3 bg-white/50 p-3 rounded-lg text-purple-700 font-mono text-sm select-all">
                {sessionCode}
              </code>
            </>
          ) : completionLoaded && !isLikelyProlific ? (
            <>
              <p className="text-gray-700 mb-3">Your survey was submitted successfully.</p>
              <p className="text-sm text-gray-600">Thank you for participating.</p>
            </>
          ) : (
            <p className="text-gray-700">Preparing completion details...</p>
          )}
        </div>
      )}
    </div>
  );
}
