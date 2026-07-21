# Unit tests for feedback_service (attention check logic).
from __future__ import annotations

import os

from app.services.feedback_service import check_attention, load_survey_questions, submit_feedback
from app.services.session_service import SessionData


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


def test_submit_feedback_pushes_without_proxy_env(monkeypatch):
    session = SessionData(session_id="session-1")
    session.chat_type = "Personalized Like Me"
    session.augmented_chat_messages = [{"role": "user", "content": "hello"}]

    observed = {}

    class FakeRef:
        def push(self, payload):
            observed["payload"] = payload
            observed["http_proxy"] = os.environ.get("HTTP_PROXY")
            observed["https_proxy"] = os.environ.get("HTTPS_PROXY")

    monkeypatch.setenv("HTTP_PROXY", "http://example-proxy")
    monkeypatch.setenv("HTTPS_PROXY", "http://example-proxy")
    monkeypatch.setattr(
        "app.services.feedback_service.get_feedback_ref",
        lambda path_override=None: FakeRef(),
    )

    payload = submit_feedback(session, {"Attention": 3}, "free text")

    assert payload == observed["payload"]
    assert observed["http_proxy"] is None
    assert observed["https_proxy"] is None
    assert session.number_of_feedbacks_provided == 1
