// useChat – manages chat state, message sending, and task tracking.
"use client";

import { useCallback, useState } from "react";
import {
  getChatMessages,
  getChatStatus,
  getFirstMessage,
  prepareChat,
  sendMessage as apiSendMessage,
} from "@/lib/api";
import type { ChatMessageResponse, ChatPrepareResponse, ChatStatusResponse } from "@/lib/types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function useChat(sessionId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatType, setChatType] = useState<string | null>(null);
  const [status, setStatus] = useState<ChatStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing messages and status from the backend (called on page mount).
  const initChat = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const [msgRes, st] = await Promise.all([
        getChatMessages(sessionId),
        getChatStatus(sessionId),
      ]);
      setMessages(msgRes.messages as ChatMessage[]);
      setStatus(st);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load chat";
      console.error("[chat:init] failed", { sessionId, error: e });
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const prepare = useCallback(
    async (personaIndex?: number): Promise<ChatPrepareResponse | null> => {
      if (!sessionId) return null;
      setLoading(true);
      setError(null);
      try {
        const res = await prepareChat(sessionId, personaIndex);
        setChatType(res.chat_type);

        // Fetch the auto-injected first message
        const firstMsg = await getFirstMessage(sessionId);
        if (firstMsg.message) {
          setMessages([{ role: "assistant", content: firstMsg.message }]);
        }

        // Fetch initial status
        const st = await getChatStatus(sessionId);
        setStatus(st);

        return res;
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Failed to prepare chat";
        console.error("[chat:prepare] failed", { sessionId, personaIndex, error: e });
        setError(msg);
        throw new Error(msg);
      } finally {
        setLoading(false);
      }
    },
    [sessionId]
  );

  const sendMessage = useCallback(
    async (content: string): Promise<ChatMessageResponse | null> => {
      if (!sessionId) return null;
      setSending(true);
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content }]);

      try {
        const res = await apiSendMessage(sessionId, content);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.content },
        ]);

        // Refresh status after each message
        const st = await getChatStatus(sessionId);
        setStatus(st);

        return res;
      } catch (e: unknown) {
        // Roll back the optimistic user message so the user can retry
        setMessages((prev) => prev.slice(0, -1));
        console.error("[chat:send] failed", { sessionId, content, error: e });
        setError(e instanceof Error ? e.message : "Failed to send message");
        return null;
      } finally {
        setSending(false);
      }
    },
    [sessionId]
  );

  const clearError = useCallback(() => setError(null), []);

  const refreshMessages = useCallback(async () => {
    if (!sessionId) return;
    const res = await getChatMessages(sessionId);
    setMessages(res.messages as ChatMessage[]);
  }, [sessionId]);

  return {
    messages,
    chatType,
    status,
    loading,
    sending,
    error,
    clearError,
    prepare,
    initChat,
    sendMessage,
    refreshMessages,
  };
}
