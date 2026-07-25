# Feedback / survey endpoints.
from __future__ import annotations

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.models.feedback import FeedbackSubmission, SurveyQuestion, SurveyQuestionsResponse
from app.services.feedback_service import check_attention, load_survey_questions, submit_feedback
from app.services.session_service import get_session

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PROLIFIC_APPROVAL_CODE = "C3KTZS0A"
PROLIFIC_COMPLETE_BASE_URL = "https://app.prolific.com/submissions/complete"


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
    if attention_passed:
        session.attention_checks_passed += 1
    else:
        session.attention_checks_failed += 1
        session.eligible_for_completion_credit = False

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
    """Return completion metadata without exposing approval codes in API responses."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.number_of_feedbacks_provided < session.required_feedback_rounds:
        raise HTTPException(status_code=403, detail="Survey not fully completed")
    if session.attention_checks_failed > 0 or not session.eligible_for_completion_credit:
        raise HTTPException(status_code=403, detail="Survey completion not eligible for credit")

    from_prolific = session.user_from_prolific
    if from_prolific:
        return {
            "redirect_url": f"/api/sessions/{session_id}/completion/redirect",
            "session_id": session_id,
        }
    return {
        "redirect_url": None,
        "session_id": session_id,
    }


@router.get("/sessions/{session_id}/completion/redirect")
async def redirect_completion_to_prolific(session_id: str):
    """Redirect eligible Prolific participants to Prolific complete URL."""
    session = get_session(session_id)
    settings = get_settings()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.number_of_feedbacks_provided < session.required_feedback_rounds:
        raise HTTPException(status_code=403, detail="Survey not fully completed")
    if session.attention_checks_failed > 0 or not session.eligible_for_completion_credit:
        raise HTTPException(status_code=403, detail="Survey completion not eligible for credit")

    if not session.user_from_prolific:
        raise HTTPException(status_code=400, detail="Session is not a Prolific session")

    approval_code = settings.prolific_approval.strip() or DEFAULT_PROLIFIC_APPROVAL_CODE
    redirect_target = f"{PROLIFIC_COMPLETE_BASE_URL}?{urlencode({'cc': approval_code})}"
    return RedirectResponse(url=redirect_target, status_code=307)
