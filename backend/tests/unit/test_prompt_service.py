# Unit tests for prompt_service.
from __future__ import annotations

from app.services.prompt_service import build_system_prompt, load_template
from app.services.session_service import SessionData


def test_load_template():
    content = load_template("base_message.txt")
    assert "{character_description}" in content
    assert "You are not a chatbot" in content


def test_build_system_prompt_vanilla():
    session = SessionData(session_id="test-1")
    session.chat_type = "vanilla"
    result = build_system_prompt(session, "Some description")
    assert result == ""
    assert session.system_message == ""


def test_build_system_prompt_personalized():
    session = SessionData(session_id="test-2")
    session.chat_type = "Personalized Like Me"
    desc = "A tech enthusiast from San Francisco"
    result = build_system_prompt(session, desc)
    assert "A tech enthusiast from San Francisco" in result
    assert "{character_description}" not in result
    assert session.system_message == result


def test_build_system_prompt_persona_ref():
    session = SessionData(session_id="test-3")
    session.chat_type = "PERSONA_ref"
    desc = "A creative writer who loves poetry"
    result = build_system_prompt(session, desc)
    assert "A creative writer who loves poetry" in result
