# Unit tests for persona_service.
from __future__ import annotations

from unittest.mock import patch

import numpy as np

from app.services.persona_service import pick_random_chat_type
from app.services.session_service import SessionData


def test_pick_random_chat_type():
    session = SessionData(session_id="test-persona")
    session.remaining_chat_types = ["vanilla", "Personalized Like Me", "Personalized Random"]

    picked = pick_random_chat_type(session)
    assert picked in session.remaining_chat_types
    assert session.chat_type == picked


def test_pick_random_chat_type_empty_raises():
    session = SessionData(session_id="test-persona-empty")
    session.remaining_chat_types = []

    try:
        pick_random_chat_type(session)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
