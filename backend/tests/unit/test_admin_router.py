# Unit tests for the admin router – settings retrieval, validation, and toggling.
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from app import runtime_settings as rs
from app.config import get_settings


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_runtime_overrides():
    """Reset all in-process runtime overrides before and after every test."""
    rs._overrides.types_of_chat_list = None
    rs._overrides.similarity_with_friends = None
    rs._overrides.similarity_threshold = None
    rs._overrides.openai_model = None
    rs._overrides.debug = None
    rs._overrides.persona_bank = None
    yield
    rs._overrides.types_of_chat_list = None
    rs._overrides.similarity_with_friends = None
    rs._overrides.similarity_threshold = None
    rs._overrides.openai_model = None
    rs._overrides.debug = None
    rs._overrides.persona_bank = None


async def _login(client) -> dict[str, str]:
    """Helper – log in and return the Authorization header."""
    password = get_settings().admin_password
    resp = await client.post("/api/admin/login", json={"password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ── Login ─────────────────────────────────────────────────────────────────────


async def test_login_success(client):
    resp = await client.post("/api/admin/login", json={"password": get_settings().admin_password})
    assert resp.status_code == 200
    assert "token" in resp.json()


async def test_login_wrong_password(client):
    resp = await client.post("/api/admin/login", json={"password": "definitely-wrong-password-xyz"})
    assert resp.status_code == 401


async def test_unauthenticated_request_rejected(client):
    resp = await client.get("/api/admin/settings")
    assert resp.status_code in (401, 403)  # HTTPBearer raises 401/403 with no token


# ── GET /options ───────────────────────────────────────────────────────────────


async def test_get_options_returns_allowed_lists(client):
    headers = await _login(client)
    resp = await client.get("/api/admin/options", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "allowed_chat_types" in data
    assert "allowed_models" in data
    assert "allowed_similarity_modes" in data
    assert "allowed_persona_banks" in data
    assert set(data["allowed_persona_banks"]) == {"v3", "v2"}


# ── GET /settings ─────────────────────────────────────────────────────────────


async def test_get_settings_returns_persona_bank_field(client):
    headers = await _login(client)
    resp = await client.get("/api/admin/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "persona_bank" in data
    # Default bank is v3
    assert data["persona_bank"] == "v3"


async def test_get_settings_returns_all_fields(client):
    headers = await _login(client)
    resp = await client.get("/api/admin/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    expected_fields = {
        "types_of_chat_list",
        "similarity_with_friends",
        "similarity_threshold",
        "openai_model",
        "debug",
        "persona_bank",
    }
    assert expected_fields == set(data.keys())


# ── PUT /settings – chat types ────────────────────────────────────────────────


async def test_toggle_chat_types(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["types_of_chat_list"] == ["vanilla"]
    # Runtime override should now reflect the change
    assert rs.get_effective_types_of_chat_list() == ["vanilla"]


async def test_toggle_chat_types_multiple(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla", "Personalized Like Me", "Personalized Random"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert set(resp.json()["types_of_chat_list"]) == {
        "vanilla", "Personalized Like Me", "Personalized Random"
    }


async def test_invalid_chat_type_rejected(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["not_a_real_type"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_empty_chat_types_rejected(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": [],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422


# ── PUT /settings – openai model ──────────────────────────────────────────────


async def test_toggle_openai_model(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-4o",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["openai_model"] == "gpt-4o"
    assert rs.get_effective_openai_model() == "gpt-4o"


async def test_invalid_openai_model_rejected(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-99-ultra",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422


# ── PUT /settings – similarity mode ──────────────────────────────────────────


async def test_toggle_similarity_mode(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "friends",
        "similarity_threshold": 0.7,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["similarity_with_friends"] == "friends"
    assert resp.json()["similarity_threshold"] == 0.7


async def test_invalid_similarity_mode_rejected(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "magic",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422


# ── PUT /settings – debug mode ────────────────────────────────────────────────


async def test_toggle_debug_on(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": True,
        "persona_bank": "v3",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["debug"] is True
    assert rs.get_effective_debug() is True


async def test_toggle_debug_off(client):
    # First switch on, then off
    headers = await _login(client)
    for debug_value in (True, False):
        payload = {
            "types_of_chat_list": ["vanilla"],
            "similarity_with_friends": "disabled",
            "similarity_threshold": 0.5,
            "openai_model": "gpt-5.4-mini",
            "debug": debug_value,
            "persona_bank": "v3",
        }
        resp = await client.put("/api/admin/settings", json=payload, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["debug"] is debug_value


# ── PUT /settings – persona bank ─────────────────────────────────────────────


async def test_toggle_persona_bank_to_v2(client):
    """Switching to v2 should hot-swap the DataFrame and persist the override."""
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v2",
    }
    with patch("app.routers.admin.reload_persona_details") as mock_reload:
        resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["persona_bank"] == "v2"
    mock_reload.assert_called_once_with("v2")
    assert rs.get_effective_persona_bank() == "v2"


async def test_same_persona_bank_does_not_reload(client):
    """If the bank hasn't changed, reload_persona_details must NOT be called."""
    headers = await _login(client)
    # Start with v3 (the default), then PUT v3 again
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    with patch("app.routers.admin.reload_persona_details") as mock_reload:
        resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    mock_reload.assert_not_called()


async def test_toggle_persona_bank_back_to_v3(client):
    """Can toggle from v2 → v3."""
    headers = await _login(client)
    # First set to v2
    rs._overrides.persona_bank = "v2"

    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v3",
    }
    with patch("app.routers.admin.reload_persona_details") as mock_reload:
        resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["persona_bank"] == "v3"
    mock_reload.assert_called_once_with("v3")


async def test_invalid_persona_bank_rejected(client):
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v99",
    }
    resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_missing_persona_bank_file_returns_422(client):
    """If the pkl file doesn't exist, the endpoint must return 422, not 500."""
    headers = await _login(client)
    payload = {
        "types_of_chat_list": ["vanilla"],
        "similarity_with_friends": "disabled",
        "similarity_threshold": 0.5,
        "openai_model": "gpt-5.4-mini",
        "debug": False,
        "persona_bank": "v2",
    }
    with patch(
        "app.routers.admin.reload_persona_details",
        side_effect=FileNotFoundError("pkl not found"),
    ):
        resp = await client.put("/api/admin/settings", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "persona_details_v2.pkl" in resp.json()["detail"]
    # Override must NOT have been saved when the file was missing
    assert rs.get_effective_persona_bank() == "v3"


# ── Settings persist across requests ─────────────────────────────────────────


async def test_settings_persist_until_reset(client):
    """A PUT followed by a GET should return the updated values."""
    headers = await _login(client)
    with patch("app.routers.admin.reload_persona_details"):
        await client.put(
            "/api/admin/settings",
            json={
                "types_of_chat_list": ["PERSONA_ref"],
                "similarity_with_friends": "combined",
                "similarity_threshold": 0.8,
                "openai_model": "gpt-4o",
                "debug": True,
                "persona_bank": "v2",
            },
            headers=headers,
        )

    resp = await client.get("/api/admin/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["types_of_chat_list"] == ["PERSONA_ref"]
    assert data["similarity_with_friends"] == "combined"
    assert data["similarity_threshold"] == 0.8
    assert data["openai_model"] == "gpt-4o"
    assert data["debug"] is True
    assert data["persona_bank"] == "v2"
