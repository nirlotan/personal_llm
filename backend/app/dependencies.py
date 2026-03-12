# Shared FastAPI dependencies (lifespan-scoped singletons).
from __future__ import annotations

from typing import Any

import dspy
import numpy as np
import pandas as pd
from socialvec.socialvec import SocialVec

from app.config import get_settings

# ── Module-level singletons (populated by startup()) ────────────────────────

_sv: SocialVec | None = None
_categories: list[str] = []
_accounts: pd.DataFrame = pd.DataFrame()
_lm: Any = None
_persona_details: pd.DataFrame = pd.DataFrame()


async def startup() -> None:
    """Load heavy resources once at application startup."""
    global _sv, _categories, _accounts, _lm, _persona_details

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

    # Persona details
    _persona_details = pd.read_pickle(f"{data_dir}/persona_details_v3.pkl")
    _persona_details.drop_duplicates(subset="screen_name", inplace=True)

    # Unwrap sv if stored as (array, count) tuples (new pickle format)
    if len(_persona_details) > 0 and isinstance(_persona_details["sv"].iloc[0], tuple):
        _persona_details["sv"] = _persona_details["sv"].apply(lambda x: x[0])

    # DSPy LLM
    _lm = dspy.LM("openai/gpt-4o", api_key=settings.openai_api_key)


def get_sv() -> SocialVec:
    assert _sv is not None, "SocialVec not initialised – call startup() first"
    return _sv


def get_categories() -> list[str]:
    return _categories


def get_accounts() -> pd.DataFrame:
    return _accounts.copy()


def get_lm() -> Any:
    assert _lm is not None, "DSPy LM not initialised – call startup() first"
    return _lm


def get_persona_details() -> pd.DataFrame:
    return _persona_details.copy()
