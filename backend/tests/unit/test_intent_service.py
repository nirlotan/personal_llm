# Unit tests for intent_service (augmentation logic, not the LLM call).
from __future__ import annotations

from app.services.session_service import SessionData


def _make_session(chat_type: str = "Personalized Like Me") -> SessionData:
    session = SessionData(session_id="test-intent")
    session.chat_type = chat_type
    session.selected_user_follow_list = ["@elonmusk", "@BillGates"]
    session.chat_status = {
        "Friendly Chat": 0,
        "Recommendation": 0,
        "Factual Information Request": 0,
    }
    return session


def test_vanilla_no_augmentation():
    """Vanilla chat type should return the prompt unchanged."""
    from app.services.intent_service import augment_prompt
    from unittest.mock import patch

    session = _make_session("vanilla")

    with patch("app.services.intent_service.classify_intent") as mock_classify:
        mock_classify.return_value = {"intent": "Friendly Chat", "topic": None}
        result, info = augment_prompt("Hello there!", session)

    assert result == "Hello there!"
    assert info["intent"] == "Friendly Chat"
    assert session.chat_status["Friendly Chat"] == 1


def test_recommendation_augmentation():
    """Recommendation intent should inject follow-list context."""
    from app.services.intent_service import augment_prompt
    from unittest.mock import patch

    session = _make_session("Personalized Like Me")

    with patch("app.services.intent_service.classify_intent") as mock_classify:
        mock_classify.return_value = {"intent": "Recommendation", "topic": "Film"}
        result, info = augment_prompt("What movies should I watch?", session)

    assert "._." in result
    assert "@elonmusk" in result
    assert "@BillGates" in result
    assert session.chat_status["Recommendation"] == 1
    assert "Film" in session.recommendation_topics


def test_factual_info_augmentation():
    """Factual info intent should inject perspective guidance."""
    from app.services.intent_service import augment_prompt
    from unittest.mock import patch

    session = _make_session("Personalized Like Me")

    with patch("app.services.intent_service.classify_intent") as mock_classify:
        mock_classify.return_value = {"intent": "Factual Information Request", "topic": None}
        result, info = augment_prompt("What is quantum computing?", session)

    assert "._." in result
    assert "personal perspective" in result
    assert session.chat_status["Factual Information Request"] == 1


def test_persona_ref_no_follow_list_in_recommendation():
    """PERSONA_ref should NOT inject follow list even on Recommendation."""
    from app.services.intent_service import augment_prompt
    from unittest.mock import patch

    session = _make_session("PERSONA_ref")

    with patch("app.services.intent_service.classify_intent") as mock_classify:
        mock_classify.return_value = {"intent": "Recommendation", "topic": "Film"}
        result, info = augment_prompt("Recommend a movie", session)

    assert "@elonmusk" not in result
    assert "._." in result
