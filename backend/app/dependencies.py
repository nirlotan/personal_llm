# Shared FastAPI dependencies (lifespan-scoped singletons).
from __future__ import annotations

from typing import Any

import dspy
import numpy as np
import pandas as pd
from socialvec.socialvec import SocialVec

from app.config import get_settings
from app import runtime_settings as _rs

# ── Module-level singletons (populated by startup()) ────────────────────────

_sv: SocialVec | None = None
_categories: list[str] = []
_accounts: pd.DataFrame = pd.DataFrame()
_persona_details: pd.DataFrame = pd.DataFrame()
_loaded_persona_bank: str | None = None
_lm_cache: dict[str, Any] = {}  # keyed by model name


def _normalize_persona_details(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize persona-bank schema so downstream services can rely on optional fields."""
    normalized = df.copy()
    normalized.drop_duplicates(subset="screen_name", inplace=True)

    if len(normalized) > 0 and isinstance(normalized["sv"].iloc[0], tuple):
        normalized["sv"] = normalized["sv"].apply(lambda x: x[0])

    if "follows_list" not in normalized.columns:
        normalized["follows_list"] = [[] for _ in range(len(normalized))]
    else:
        normalized["follows_list"] = normalized["follows_list"].apply(
            lambda value: value if isinstance(value, list) else []
        )

    return normalized


async def startup() -> None:
    """Load heavy resources once at application startup."""
    global _sv, _categories, _accounts, _lm_cache, _persona_details, _loaded_persona_bank

    settings = get_settings()
    data_dir = settings.data_dir

    # SocialVec model
    _sv = SocialVec()

    # Categories & accounts from pre-processed pickle
    _accounts = pd.read_pickle(f"{data_dir}/curated_twitter_accounts.pkl")

    # Normalise: strip leading '@' and create twitter_name alias (in case pickle was
    # created directly from the raw Excel without these transforms)
    _accounts["twitter_screen_name"] = _accounts["twitter_screen_name"].str.lstrip("@")
    _accounts["twitter_name"] = _accounts["twitter_screen_name"]

    # Ensure sv column contains numpy arrays (handles both list and string formats)
    if len(_accounts) > 0 and not isinstance(_accounts["sv"].iloc[0], np.ndarray):
        _accounts["sv"] = _accounts["sv"].apply(
            lambda x: np.array(x) if isinstance(x, list)
            else np.fromstring(str(x).strip("[]"), sep=" " if " " in str(x) else ",")
        )

    _categories = _accounts["category"].unique().tolist()

    # DBpedia types merge into SocialVec entities
    df_dbpedia = pd.read_csv(f"{data_dir}/dbpedia_types.csv")
    _sv.entities = pd.merge(_sv.entities, df_dbpedia, on="screen_name", how="left")

    # Persona details (respect runtime default/override instead of hardcoding v3)
    bank = _rs.get_effective_persona_bank()
    _persona_details = _normalize_persona_details(
        pd.read_pickle(f"{data_dir}/persona_details_{bank}.pkl", compression='gzip')
    )
    _loaded_persona_bank = bank

    # DSPy LLM – prime the cache with the startup model
    default_model = _rs.get_effective_openai_model()
    if default_model == "gemma4":
        default_model = settings.openai_model
    _lm_cache[default_model] = dspy.LM(
        f"openai/{default_model}", api_key=settings.openai_api_key
    )


def get_sv() -> SocialVec:
    assert _sv is not None, "SocialVec not initialised – call startup() first"
    return _sv


def get_categories() -> list[str]:
    return _categories


def get_accounts() -> pd.DataFrame:
    return _accounts.copy()


def get_lm() -> Any:
    """Return the DSPy LM for the currently effective model, creating it if needed."""
    model = _rs.get_effective_openai_model()
    if model == "gemma4":
        # Intent classification currently relies on DSPy OpenAI wiring.
        # Keep it stable even when the chat engine is switched to Gemma.
        model = get_settings().openai_model
    if model not in _lm_cache:
        settings = get_settings()
        _lm_cache[model] = dspy.LM(f"openai/{model}", api_key=settings.openai_api_key)
    return _lm_cache[model]


def get_intent_lm() -> Any:
    """Return the DSPy LM used for intent classification.

    Intent classification always uses gpt-4o regardless of the model selected
    in the admin page for the main conversation.
    """
    settings = get_settings()
    model = "gpt-4o"
    if model not in _lm_cache:
        _lm_cache[model] = dspy.LM(f"openai/{model}", api_key=settings.openai_api_key)
    return _lm_cache[model]


def get_persona_details() -> pd.DataFrame:
    return _persona_details.copy()


def get_loaded_persona_bank() -> str | None:
    """Return the persona bank currently loaded in memory."""
    return _loaded_persona_bank


def reload_persona_details(bank: str) -> None:
    """Hot-swap the in-memory persona details DataFrame when the admin changes the bank."""
    global _persona_details, _loaded_persona_bank
    from app.config import get_settings
    settings = get_settings()
    pkl_path = f"{settings.data_dir}/persona_details_{bank}.pkl"
    _persona_details = _normalize_persona_details(pd.read_pickle(pkl_path), compression='gzip')
    _loaded_persona_bank = bank
