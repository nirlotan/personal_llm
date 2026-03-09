# Feedback service – survey assembly and Firebase push.
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from app.firebase import get_feedback_ref
from app.services.session_service import SessionData


_QUESTIONNAIRE_PATH = Path(__file__).resolve().parents[1] / "data" / "questionnaire.csv"


def load_survey_questions() -> list[dict]:
    """Load survey questions from CSV."""
    df = pd.read_csv(_QUESTIONNAIRE_PATH)
    questions = []
    for i, row in df.iterrows():
        questions.append({
            "index": i,
            "short_label": row["short_label"],
            "label": row["label"],
            "description": row["description"],
        })
    return questions


def check_attention(ratings: dict[str, float]) -> bool:
    """
    The attention-check question (short_label='Attention') must equal 3.
    Returns True if passed.
    """
    return ratings.get("Attention") == 3


def submit_feedback(
    session: SessionData,
    ratings: dict[str, float],
    free_text: str = "",
) -> dict:
    """
    Assemble survey payload and push to Firebase.

    Returns the assembled payload.
    """
    # Determine the feedback path
    path_override = "/survey_results_friends" if session.friends else None
    ref = get_feedback_ref(path_override)

    # Format chat messages
    formatted_chat = []
    for msg in session.chat_messages:
        formatted_chat.append(f"{msg['role']}: {msg['content']}")

    payload = {
        "experiment_start_time": session.experiment_start_time,
        "date_time": str(datetime.now()),
        "unique_session_id": session.session_id,
        "user_selected_categories": session.selected_categories,
        "user_selected_accounts": session.selected_accounts,
        "user_selected_for_chat": session.user_for_the_chat,
        "chat_type": session.chat_type,
        "selected_user_similarity": session.selected_user_similarity,
        "system_message": session.system_message,
        "chat": formatted_chat,
        "messages_timing": session.messages_timing,
        "recommendation_topics": session.recommendation_topics,
        "user_feedback": ratings,
        "free_text_feedback": free_text,
    }

    ref.push(payload)
    session.number_of_feedbacks_provided += 1

    return payload
