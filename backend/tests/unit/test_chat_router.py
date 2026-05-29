from app.routers.chat import _sync_chat_types_for_unstarted_session
from app.services.session_service import SessionData


def test_sync_chat_types_for_unstarted_session_applies_runtime_settings(monkeypatch):
    session = SessionData(session_id="s1")
    session.remaining_chat_types = ["vanilla", "Personalized Like Me"]

    monkeypatch.setattr(
        "app.routers.chat.get_effective_types_of_chat_list",
        lambda: ["PERSONA_ref"],
    )

    _sync_chat_types_for_unstarted_session(session)

    assert session.remaining_chat_types == ["PERSONA_ref"]


def test_sync_chat_types_for_unstarted_session_does_not_change_started_chat(monkeypatch):
    session = SessionData(session_id="s2")
    session.remaining_chat_types = ["vanilla"]
    session.chat_messages = [{"role": "assistant", "content": "hello"}]

    monkeypatch.setattr(
        "app.routers.chat.get_effective_types_of_chat_list",
        lambda: ["PERSONA_ref"],
    )

    _sync_chat_types_for_unstarted_session(session)

    assert session.remaining_chat_types == ["vanilla"]
