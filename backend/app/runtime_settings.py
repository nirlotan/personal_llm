# Runtime-mutable settings that override the base .env config for the lifetime
# of the server process.  Reset to None = fall back to Settings value from .env.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class _RuntimeOverrides:
    types_of_chat_list: Optional[list[str]] = None
    similarity_with_friends: Optional[str] = None
    similarity_threshold: Optional[float] = None
    openai_model: Optional[str] = None
    debug: Optional[bool] = None
    persona_bank: Optional[str] = None


_overrides = _RuntimeOverrides()

# ── Allowed values for each setting ─────────────────────────────────────────

ALLOWED_CHAT_TYPES: list[str] = [
    "vanilla",
    "Personalized Like Me",
    "Personalized Random",
    "PERSONA_ref",
]
ALLOWED_MODELS: list[str] = ["gpt-5.4-mini", "gpt-4o", "gpt-5.2", "gpt-5.4"]
ALLOWED_SIMILARITY_MODES: list[str] = ["disabled", "friends", "combined"]
ALLOWED_PERSONA_BANKS: list[str] = ["v3", "v2"]


# ── Accessors ────────────────────────────────────────────────────────────────


def get_effective_types_of_chat_list() -> list[str]:
    if _overrides.types_of_chat_list is not None:
        return _overrides.types_of_chat_list
    from app.config import get_settings
    return get_settings().types_of_chat_list


def get_effective_similarity_with_friends() -> str:
    if _overrides.similarity_with_friends is not None:
        return _overrides.similarity_with_friends
    from app.config import get_settings
    return get_settings().similarity_with_friends


def get_effective_similarity_threshold() -> float:
    if _overrides.similarity_threshold is not None:
        return _overrides.similarity_threshold
    from app.config import get_settings
    return get_settings().similarity_threshold


def get_effective_openai_model() -> str:
    if _overrides.openai_model is not None:
        return _overrides.openai_model
    from app.config import get_settings
    return get_settings().openai_model


def get_effective_debug() -> bool:
    if _overrides.debug is not None:
        return _overrides.debug
    from app.config import get_settings
    return get_settings().debug


def get_effective_persona_bank() -> str:
    if _overrides.persona_bank is not None:
        return _overrides.persona_bank
    return "v3"  # default: new persona bank


# ── Mutators (called by the admin router) ────────────────────────────────────


def update_runtime_settings(
    types_of_chat_list: list[str] | None = None,
    similarity_with_friends: str | None = None,
    similarity_threshold: float | None = None,
    openai_model: str | None = None,
    debug: bool | None = None,
    persona_bank: str | None = None,
) -> None:
    if types_of_chat_list is not None:
        _overrides.types_of_chat_list = types_of_chat_list
    if similarity_with_friends is not None:
        _overrides.similarity_with_friends = similarity_with_friends
    if similarity_threshold is not None:
        _overrides.similarity_threshold = similarity_threshold
    if openai_model is not None:
        _overrides.openai_model = openai_model
    if debug is not None:
        _overrides.debug = debug
    if persona_bank is not None:
        _overrides.persona_bank = persona_bank


def get_current_overrides() -> dict:
    """Return the effective values of all managed settings."""
    return {
        "types_of_chat_list": get_effective_types_of_chat_list(),
        "similarity_with_friends": get_effective_similarity_with_friends(),
        "similarity_threshold": get_effective_similarity_threshold(),
        "openai_model": get_effective_openai_model(),
        "debug": get_effective_debug(),
        "persona_bank": get_effective_persona_bank(),
    }
