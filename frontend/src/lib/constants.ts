// Application constants – mirroring backend config where needed on the client.

export const MIN_CATEGORIES = 3;
export const MAX_CATEGORIES = 5;
export const MIN_ACCOUNTS_PER_CATEGORY = 3;
export const MAX_ACCOUNTS_PER_CATEGORY = 5;
export const MIN_MESSAGES = 8;

export const STEPS = [
  { label: "Interests", path: "/profile" },
  { label: "Chat", path: "/chat" },
  { label: "Feedback", path: "/feedback" },
] as const;

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
