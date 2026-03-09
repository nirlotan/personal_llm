# Unit tests for feedback_service (attention check logic).
from __future__ import annotations

from app.services.feedback_service import check_attention, load_survey_questions


def test_attention_check_passes():
    assert check_attention({"Attention": 3}) is True


def test_attention_check_fails_wrong_value():
    assert check_attention({"Attention": 5}) is False


def test_attention_check_fails_missing():
    assert check_attention({"Perception": 4}) is False


def test_load_survey_questions():
    questions = load_survey_questions()
    assert len(questions) > 0
    # Verify expected fields
    for q in questions:
        assert "short_label" in q
        assert "label" in q
        assert "description" in q
    # Verify attention question exists
    labels = [q["short_label"] for q in questions]
    assert "Attention" in labels
