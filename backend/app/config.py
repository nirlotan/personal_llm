# Application configuration loaded from environment variables and secrets.
from __future__ import annotations

import json
import os
import platform
from functools import lru_cache
from pathlib import Path

import toml
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration – reads from env vars / .env file."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- App ---
    app_name: str = "Personal LLM Research Platform"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]  # frontend origin

    # --- Chat constraints ---
    minimal_number_of_messages: int = 8
    max_interests_pc: int = 6
    max_interests_mobile: int = 2

    # --- Selection limits ---
    min_categories: int = 4
    max_categories: int = 5
    min_accounts_per_category: int = 3
    max_accounts_per_category: int = 5

    # --- OpenAI ---
    openai_api_key: str = ""

    # --- Firebase ---
    firebase_certificate_json: str = ""  # raw JSON string
    firebase_db_url: str = ""
    experiment_feedback_path: str = "/survey_results"

    # --- Chat types ---
    types_of_chat_list: list[str] = ["vanilla", "Personalized Like Me"]

    # --- Prolific ---
    prolific_approval: str = ""

    # --- Proxy ---
    http_proxy: str = ""
    https_proxy: str = ""

    # --- Persona matching ---
    similarity_with_friends: bool = False
    min_joint_categories: int = 2

    # --- Data paths (relative to backend/) ---
    data_dir: str = "app/data"


def _load_legacy_secrets() -> dict:
    """Attempt to load secrets from the legacy Streamlit secrets file."""
    if platform.system() == "Darwin":
        secrets_path = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
    else:
        secrets_path = Path("/etc/secrets/keys.toml")

    if secrets_path.exists():
        return toml.load(secrets_path)
    return {}


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings, merging env vars with legacy secrets."""
    legacy = _load_legacy_secrets()

    # Map legacy keys → env-compatible overrides (only if env var not already set)
    env_overrides: dict[str, str] = {}
    if legacy.get("openai_api_key") and not os.getenv("OPENAI_API_KEY"):
        env_overrides["OPENAI_API_KEY"] = legacy["openai_api_key"]
    if legacy.get("freebase_certificate") and not os.getenv("FIREBASE_CERTIFICATE_JSON"):
        env_overrides["FIREBASE_CERTIFICATE_JSON"] = legacy["freebase_certificate"]
    if legacy.get("firebase_db_url") and not os.getenv("FIREBASE_DB_URL"):
        env_overrides["FIREBASE_DB_URL"] = legacy["firebase_db_url"]
    if legacy.get("types_of_chat_list") and not os.getenv("TYPES_OF_CHAT_LIST"):
        env_overrides["TYPES_OF_CHAT_LIST"] = json.dumps(legacy["types_of_chat_list"])
    if legacy.get("prolific_approval") and not os.getenv("PROLIFIC_APPROVAL"):
        env_overrides["PROLIFIC_APPROVAL"] = legacy["prolific_approval"]
    if legacy.get("experiment_feedback_path") and not os.getenv("EXPERIMENT_FEEDBACK_PATH"):
        env_overrides["EXPERIMENT_FEEDBACK_PATH"] = legacy["experiment_feedback_path"]

    # Temporarily set env vars so Pydantic picks them up
    for k, v in env_overrides.items():
        os.environ[k] = v

    return Settings()
