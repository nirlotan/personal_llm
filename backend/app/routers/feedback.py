# Feedback / survey endpoints.
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.feedback import FeedbackSubmission, SurveyQuestion, SurveyQuestionsResponse
from app.services.feedback_service import check_attention, load_survey_questions, submit_feedback
from app.services.session_service import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/feedback/questions", response_model=SurveyQuestionsResponse)
async def get_survey_questions():
    """Return the survey questions."""
    questions = load_survey_questions()
    return SurveyQuestionsResponse(questions=[SurveyQuestion(**q) for q in questions])


@router.post("/sessions/{session_id}/feedback")
async def post_feedback(session_id: str, body: FeedbackSubmission):
    """Submit survey feedback. Returns attention_passed and whether more chats remain."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Push to Firebase
    try:
        submit_feedback(session, body.ratings, body.free_text)
    except Exception as exc:
        logger.error("Firebase push failed for session %s: %s", session_id, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Firebase write failed: {exc}")

    # Check attention
    attention_passed = check_attention(body.ratings)

    # remaining_chat_types still contains the just-finished type (it's removed on /chat/reset).
    # Subtract 1 to get the true number of chats still to be done after this submission.
    remaining = max(0, len(session.remaining_chat_types) - 1)

    return {
        "status": "submitted",
        "attention_passed": attention_passed,
        "remaining_chats": remaining,
    }


@router.get("/sessions/{session_id}/completion")
async def get_completion_info(session_id: str):
    """Return Prolific redirect URL or session code for crediting."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    settings = get_settings()

    if session.user_from_prolific and settings.prolific_approval:
        return {
            "redirect_url": f"https://app.prolific.com/submissions/complete?cc={settings.prolific_approval}",
            "session_id": session.session_id,
        }
    return {
        "redirect_url": None,
        "session_id": session.session_id,
    }
