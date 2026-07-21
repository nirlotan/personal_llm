# Unit tests for persona_service.
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.dependencies import _normalize_persona_details
from app.services.persona_service import pick_random_chat_type, select_persona_for_session
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


def test_personalized_random_only_picks_personas_below_similarity_threshold():
    session = SessionData(session_id="test-random-threshold")
    session.chat_type = "Personalized Random"
    session.user_mean_vector = np.array([1.0, 0.0], dtype=float)

    personas = pd.DataFrame(
        {
            "screen_name": ["near_user", "far_user", "mid_user"],
            "description": ["", "", ""],
            "sv": [
                np.array([1.0, 0.0], dtype=float),
                np.array([0.0, 1.0], dtype=float),
                np.array([0.6, 0.8], dtype=float),
            ],
            "follows_list": [[], [], []],
        }
    )

    with (
        patch("app.services.persona_service.get_persona_details", return_value=personas),
        patch("app.services.persona_service.get_effective_random_persona_similarity_threshold", return_value=0.7),
        patch("app.services.persona_service.random.choice", side_effect=lambda items: items[0]),
    ):
        persona = select_persona_for_session(session)

    assert persona["screen_name"] == "far_user"
    assert session.selected_user_similarity < 0.7


def test_personalized_random_falls_back_to_least_similar_when_no_persona_is_below_threshold():
    session = SessionData(session_id="test-random-threshold-fallback")
    session.chat_type = "Personalized Random"
    session.user_mean_vector = np.array([1.0, 0.0], dtype=float)

    personas = pd.DataFrame(
        {
            "screen_name": ["almost_same", "less_same"],
            "description": ["", ""],
            "sv": [
                np.array([1.0, 0.0], dtype=float),
                np.array([0.8, 0.6], dtype=float),
            ],
            "follows_list": [[], []],
        }
    )

    with (
        patch("app.services.persona_service.get_persona_details", return_value=personas),
        patch("app.services.persona_service.get_effective_random_persona_similarity_threshold", return_value=0.7),
    ):
        persona = select_persona_for_session(session)

    assert persona["screen_name"] == "less_same"
    assert session.selected_user_similarity == pytest.approx(0.8)


def test_personalized_like_me_supports_persona_bank_without_follows_list():
    session = SessionData(session_id="test-like-me-v2-schema")
    session.chat_type = "Personalized Like Me"
    session.user_mean_vector = np.array([1.0, 0.0], dtype=float)
    session.selected_accounts = ["account_a"]

    personas = _normalize_persona_details(
        pd.DataFrame(
            {
                "screen_name": ["closest_match", "farther_match"],
                "description": ["", ""],
                "sv": [
                    np.array([1.0, 0.0], dtype=float),
                    np.array([0.0, 1.0], dtype=float),
                ],
            }
        )
    )
    accounts = pd.DataFrame(
        {
            "twitter_name": ["account_a"],
            "category": ["news"],
        }
    )

    with (
        patch("app.services.persona_service.get_persona_details", return_value=personas),
        patch("app.services.persona_service.get_accounts", return_value=accounts),
        patch("app.services.persona_service.get_effective_similarity_with_friends", return_value="friends"),
        patch("app.services.persona_service.get_effective_similarity_threshold", return_value=0.3),
    ):
        persona = select_persona_for_session(session)

    assert persona["screen_name"] == "closest_match"
    assert session.selected_user_follow_list == []
