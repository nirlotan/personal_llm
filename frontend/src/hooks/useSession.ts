// useSession – manages session creation, storage, and Prolific parameter handling.
"use client";

import { useCallback, useEffect, useState } from "react";
import { createSession } from "@/lib/api";
import type { SessionResponse } from "@/lib/types";

const SESSION_KEY = "plm_session_id";

export function useSession() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      try {
        setSession(JSON.parse(stored));
      } catch {
        localStorage.removeItem(SESSION_KEY);
      }
    }
    setReady(true);
  }, []);

  const startSession = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Extract Prolific params from URL
      const params = new URLSearchParams(window.location.search);
      const prolific_pid = params.get("PROLIFIC_PID") ?? undefined;
      const study_id = params.get("STUDY_ID") ?? undefined;
      const session_id_prolific = params.get("SESSION_ID") ?? undefined;
      const friends = params.has("friends");

      const res = await createSession({
        prolific_pid,
        study_id,
        session_id_prolific,
        friends,
      });

      localStorage.setItem(SESSION_KEY, JSON.stringify(res));
      setSession(res);
      return res;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to create session";
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
  }, []);

  return { session, loading, ready, error, startSession, clearSession };
}
