// Shared TypeScript interfaces for the Personal LLM Research Platform.

export interface SessionResponse {
  session_id: string;
  experiment_start_time: string;
  user_from_prolific: boolean;
}

export interface Account {
  twitter_screen_name: string;
  twitter_name: string;
  display_name: string;
  description: string;
  category: string;
}

export interface ChatMessageResponse {
  role: string;
  content: string;
  intent: string | null;
  topic: string | null;
}

export interface TaskStatus {
  friendly_chat: boolean;
  recommendation: boolean;
  factual_information: boolean;
}

export interface ChatStatusResponse {
  message_count: number;
  tasks: TaskStatus;
  can_proceed: boolean;
}

export interface SurveyQuestion {
  index: number;
  short_label: string;
  label: string;
  description: string;
}

export interface ChatPrepareResponse {
  chat_type: string;
  system_message_preview: string;
}

export interface FeedbackResponse {
  status: string;
  attention_passed: boolean;
  remaining_chats: number;
}

export interface CompletionInfo {
  redirect_url: string | null;
  session_id: string;
}
