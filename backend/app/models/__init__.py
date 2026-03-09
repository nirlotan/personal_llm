# Pydantic schemas for session management.
from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request body when creating a new experiment session."""
    prolific_pid: str | None = None
    study_id: str | None = None
    session_id_prolific: str | None = None
    friends: bool = False


class SessionResponse(BaseModel):
    """Returned after session creation."""
    session_id: str
    experiment_start_time: str
    user_from_prolific: bool = False
