# Profile service – category/account loading, embedding computation.
from __future__ import annotations

import numpy as np
import pandas as pd

from app.dependencies import get_accounts, get_categories
from app.services.session_service import SessionData


def list_categories() -> list[str]:
    """Return the list of selectable interest categories."""
    return get_categories()


def _clean(val) -> str:
    """Return a clean string, replacing NaN/None with empty string."""
    if val is None:
        return ""
    s = str(val)
    return "" if s.lower() == "nan" else s


def list_accounts_for_category(category: str) -> list[dict]:
    """Return accounts available in *category*."""
    accounts = get_accounts()
    subset = (
        accounts[accounts["category"] == category]
        .drop_duplicates(subset=["twitter_screen_name"])
    )
    records = []
    for _, row in subset.iterrows():
        records.append(
            {
                "twitter_screen_name": row["twitter_screen_name"],
                "twitter_name": row["twitter_name"],
                "display_name": _clean(row.get("Full Name")) or row["twitter_name"],
                "description": _clean(row.get("Description")),
                "category": row["category"],
            }
        )
    return records


def compute_user_embedding(session: SessionData) -> np.ndarray:
    """Compute the mean SocialVec embedding for accounts selected by the user."""
    accounts = get_accounts()
    matched = accounts[accounts["twitter_name"].isin(session.selected_accounts)]
    matched = matched[~matched["sv"].isna()]
    if matched.empty:
        raise ValueError("No valid SocialVec embeddings found for the selected accounts.")
    mean_vec = np.mean(np.stack(matched["sv"].values), axis=0)
    session.user_mean_vector = mean_vec
    return mean_vec
