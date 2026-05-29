// Typed API client – thin fetch wrapper for the backend REST API.

import type {
  Account,
  ChatMessageResponse,
  ChatPrepareResponse,
  ChatStatusResponse,
  CompletionInfo,
  FeedbackResponse,
  SessionResponse,
  SurveyQuestion,
} from "./types";

import { API_URL } from "./constants";

// ── Helpers ────────────────────────────────────────────────────────────────

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  }).then((r) => json<T>(r));
}

function get<T>(path: string): Promise<T> {
  return fetch(`${API_URL}${path}`).then((r) => json<T>(r));
}

// ── Session ────────────────────────────────────────────────────────────────

export function createSession(params: {
  prolific_pid?: string;
  study_id?: string;
  session_id_prolific?: string;
  friends?: boolean;
}): Promise<SessionResponse> {
  return post("/api/sessions", params);
}

export function getSessionInfo(sessionId: string): Promise<{
  session_id: string;
  remaining_chat_types_count: number;
  number_of_feedbacks_provided: number;
}> {
  return get(`/api/sessions/${sessionId}`);
}

// ── Profile ────────────────────────────────────────────────────────────────

export function getCategories(): Promise<{ categories: string[] }> {
  return get("/api/categories");
}

export function getAccountsForCategory(
  category: string
): Promise<{ accounts: Account[] }> {
  return get(`/api/categories/${encodeURIComponent(category)}/accounts`);
}

export function submitProfile(
  sessionId: string,
  data: { selected_categories: string[]; selected_accounts: string[] }
): Promise<{ status: string }> {
  return post(`/api/sessions/${sessionId}/profile`, data);
}

// ── Chat ───────────────────────────────────────────────────────────────────

export function prepareChat(
  sessionId: string,
  personaIndex?: number
): Promise<ChatPrepareResponse> {
  const params = personaIndex != null ? `?persona_index=${personaIndex}` : "";
  return post(`/api/sessions/${sessionId}/chat/prepare${params}`);
}

export function sendMessage(
  sessionId: string,
  content: string
): Promise<ChatMessageResponse> {
  return post(`/api/sessions/${sessionId}/chat/message`, { content });
}

export function getChatStatus(
  sessionId: string
): Promise<ChatStatusResponse> {
  return get(`/api/sessions/${sessionId}/chat/status`);
}

export function getChatMessages(
  sessionId: string
): Promise<{ messages: { role: string; content: string }[] }> {
  return get(`/api/sessions/${sessionId}/chat/messages`);
}

export function getFirstMessage(
  sessionId: string
): Promise<{ message: string | null }> {
  return get(`/api/sessions/${sessionId}/chat/first-message`);
}

export function resetChat(
  sessionId: string
): Promise<{ status: string; remaining_chat_types: number }> {
  return post(`/api/sessions/${sessionId}/chat/reset`);
}

// ── Feedback ───────────────────────────────────────────────────────────────

export function getSurveyQuestions(): Promise<{
  questions: SurveyQuestion[];
}> {
  return get("/api/feedback/questions");
}

export function submitFeedback(
  sessionId: string,
  data: { ratings: Record<string, number>; free_text: string }
): Promise<FeedbackResponse> {
  return post(`/api/sessions/${sessionId}/feedback`, data);
}

export function getCompletionInfo(
  sessionId: string
): Promise<CompletionInfo> {
  return get(`/api/sessions/${sessionId}/completion`);
}

// ── Admin ──────────────────────────────────────────────────────────────────

export interface AdminSettings {
  types_of_chat_list: string[];
  similarity_with_friends: string;
  similarity_threshold: number;
  openai_model: string;
  debug: boolean;
  persona_bank: string;
}

export interface AdminOptions {
  allowed_chat_types: string[];
  allowed_models: string[];
  allowed_similarity_modes: string[];
  allowed_persona_banks: string[];
}

function putJson<T>(path: string, body: unknown, token: string): Promise<T> {
  return fetch(`${API_URL}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  }).then((r) => json<T>(r));
}

function getAuth<T>(path: string, token: string): Promise<T> {
  return fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => json<T>(r));
}

export function adminLogin(password: string): Promise<{ token: string }> {
  return post("/api/admin/login", { password });
}

export function adminGetOptions(token: string): Promise<AdminOptions> {
  return getAuth("/api/admin/options", token);
}

export function adminGetSettings(token: string): Promise<AdminSettings> {
  return getAuth("/api/admin/settings", token);
}

export function adminPutSettings(token: string, settings: AdminSettings): Promise<AdminSettings> {
  return putJson("/api/admin/settings", settings, token);
}

export function getDebugStatus(): Promise<{ debug: boolean }> {
  return get("/api/debug/status");
}
