# Unit tests for session_service.
from __future__ import annotations

from app.services.session_service import create_session, get_session, delete_session


def test_create_session_generates_uuid():
    session = create_session(chat_types=["vanilla"])
    assert session.session_id
    assert len(session.session_id) == 36  # UUID4 format
    assert not session.user_from_prolific


def test_create_session_prolific():
    session = create_session(
        prolific_pid="PID123",
        study_id="STU456",
        session_id_prolific="SES789",
        chat_types=["vanilla"],
    )
    assert session.session_id == "PID123__STU456__SES789"
    assert session.user_from_prolific


def test_get_session():
    session = create_session(chat_types=["vanilla"])
    retrieved = get_session(session.session_id)
    assert retrieved is session


def test_get_session_not_found():
    assert get_session("nonexistent-id") is None


def test_delete_session():
    session = create_session(chat_types=["vanilla"])
    sid = session.session_id
    delete_session(sid)
    assert get_session(sid) is None


def test_session_initial_chat_status():
    session = create_session(chat_types=["vanilla", "Personalized Like Me"])
    assert session.chat_status == {
        "Friendly Chat": 0,
        "Recommendation": 0,
        "Factual Information Request": 0,
    }
    assert session.remaining_chat_types == ["vanilla", "Personalized Like Me"]


def test_session_friends_flag():
    session = create_session(friends=True, chat_types=["vanilla"])
    assert session.friends is True
