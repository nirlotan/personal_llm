# Session management service.
from __future__ import annotations

import uuid
from datetime import datetime


class SessionData:
    """In-memory representation of a single experiment session."""

    def __init__(
        self,
        session_id: str,
        user_from_prolific: bool = False,
        friends: bool = False,
    ):
        self.session_id = session_id
        self.experiment_start_time = str(datetime.now())
        self.user_from_prolific = user_from_prolific
        self.friends = friends

        # Profile
        self.selected_categories: list[str] = []
        self.selected_accounts: list[str] = []
        self.user_mean_vector = None

        # Chat
        self.remaining_chat_types: list[str] = []
        self.chat_type: str | None = None
        self.system_message: str = ""
        self.user_for_the_chat: str | None = None
        self.selected_user_similarity: float = 0.0
        self.user_embeddings = None
        self.selected_user_follow_list: list[str] = []
        self.recommendation_topics: list[str] = []
        self.chat_status: dict[str, int] = {
            "Friendly Chat": 0,
            "Recommendation": 0,
            "Factual Information Request": 0,
        }
        self.messages_timing: list[int] = []
        self.chat_messages: list[dict] = []           # [{role, content}, ...] – clean, for display
        self.augmented_chat_messages: list[dict] = [] # [{role, content}, ...] – with [Assistant Guidance], for Firebase
        self.langchain_messages: list = []            # raw LangChain message objects
        self.last_message_time: float = 0.0
        self.number_of_feedbacks_provided: int = 0


# ── In-memory session store ────────────────────────────────────────────────

_sessions: dict[str, SessionData] = {}


def create_session(
    prolific_pid: str | None = None,
    study_id: str | None = None,
    session_id_prolific: str | None = None,
    friends: bool = False,
    chat_types: list[str] | None = None,
) -> SessionData:
    """Create and store a new session."""
    if prolific_pid and study_id and session_id_prolific:
        sid = f"{prolific_pid}__{study_id}__{session_id_prolific}"
        from_prolific = True
    else:
        sid = str(uuid.uuid4())
        from_prolific = False

    session = SessionData(session_id=sid, user_from_prolific=from_prolific, friends=friends)

    if chat_types:
        session.remaining_chat_types = list(chat_types)  # copy

    _sessions[sid] = session
    return session


def get_session(session_id: str) -> SessionData | None:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
