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

    # Categories & accounts from Excel (single-sheet curated file)
    xls_path = f"{data_dir}/curated_twitter_accounts_with_categories_and_ids.xlsx"
    _accounts = pd.read_excel(xls_path)

    # Normalise column names to match internal conventions
    _accounts = _accounts.rename(columns={
        "Category": "category",
        "Twitter Account": "twitter_screen_name",
        "Full Name": "wikidata_label",
        "Description": "wikidata_desc",
    })
    # Strip leading '@' from screen names and create twitter_name alias
    _accounts["twitter_screen_name"] = _accounts["twitter_screen_name"].str.lstrip("@")
    _accounts["twitter_name"] = _accounts["twitter_screen_name"]

    _categories = _accounts["category"].unique().tolist()

    _accounts["sv"] = _accounts["sv"].apply(lambda x: np.fromstring(str(x).strip("[]"), sep=" "))
    _accounts = _accounts[
        [
            "twitter_screen_name", "twitter_user_id", "twitter_name",
            "wikidata_label", "wikidata_desc",
            "category", "sv",
        ]
    ]

    # DBpedia types merge into SocialVec entities
    df_dbpedia = pd.read_csv(f"{data_dir}/dbpedia_types.csv")
    _sv.entities = pd.merge(_sv.entities, df_dbpedia, on="screen_name", how="left")

    # Persona details
    _persona_details = pd.read_pickle(f"{data_dir}/persona_details_v3.pkl")
    _persona_details.drop_duplicates(subset="screen_name", inplace=True)

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
