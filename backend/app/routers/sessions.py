# Session management endpoints.
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models import SessionCreate, SessionResponse
from app.services.session_service import create_session, get_session

router = APIRouter()


@router.post("", response_model=SessionResponse)
async def create_new_session(body: SessionCreate):
    """Create a new experiment session."""
    settings = get_settings()
    session = create_session(
        prolific_pid=body.prolific_pid,
        study_id=body.study_id,
        session_id_prolific=body.session_id_prolific,
        friends=body.friends,
        chat_types=settings.types_of_chat_list,
    )
    return SessionResponse(
        session_id=session.session_id,
        experiment_start_time=session.experiment_start_time,
        user_from_prolific=session.user_from_prolific,
    )


@router.get("/{session_id}")
async def get_session_info(session_id: str):
    """Return basic session metadata."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "experiment_start_time": session.experiment_start_time,
        "user_from_prolific": session.user_from_prolific,
        "remaining_chat_types_count": len(session.remaining_chat_types),
        "number_of_feedbacks_provided": session.number_of_feedbacks_provided,
    }

