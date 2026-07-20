from langchain_core.messages import HumanMessage

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


async def test_get_chat_status_uses_runtime_minimal_message_override(client, monkeypatch):
    session = SessionData(session_id="s3")
    session.chat_type = "vanilla"
    session.langchain_messages = [
        HumanMessage(content="one"),
        HumanMessage(content="two"),
        HumanMessage(content="three"),
        HumanMessage(content="four"),
    ]
    session.chat_status = {
        "Friendly Chat": True,
        "Recommendation": True,
        "Second Recommendation": True,
        "Stance Request": True,
        "Factual Information Request": True,
    }

    monkeypatch.setattr("app.routers.chat.get_session", lambda session_id: session)
    monkeypatch.setattr("app.routers.chat.get_effective_minimal_number_of_messages", lambda: 4)

    resp = await client.get("/api/sessions/s3/chat/status")

    assert resp.status_code == 200
    assert resp.json()["message_count"] == 4
    assert resp.json()["can_proceed"] is True
