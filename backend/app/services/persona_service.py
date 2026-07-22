# Persona matching & chat-type randomisation.
from __future__ import annotations

import random

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from app.config import get_settings
from app.dependencies import get_accounts, get_persona_details
from app.runtime_settings import (
    get_effective_random_persona_similarity_threshold,
    get_effective_similarity_threshold,
    get_effective_similarity_with_friends,
)
from app.services.session_service import SessionData


def pick_random_chat_type(session: SessionData) -> str:
    """Randomly select one of the remaining chat types and assign it to the session."""
    if not session.remaining_chat_types:
        raise ValueError("No more chat types remaining for this session.")
    choice = random.choice(session.remaining_chat_types)
    session.chat_type = choice
    return choice


def _rank_personas(
    session: SessionData,
    persona_details: pd.DataFrame,
    similarity_mode: str = "disabled",
    min_joint_categories: int = 1,
    similarity_threshold: float = 0.3,
) -> pd.DataFrame:
    """
    Return personas sorted for selection.

    Modes:
    - "disabled": rank by cosine similarity only.
    - "friends": rank by joint_categories → joint_users → cosine_similarity.
      Apply min_joint_categories filter when the session has selected accounts;
      fall back to the full set if no candidates survive.
    - "combined": first filter to personas whose cosine similarity exceeds
      similarity_threshold, then rank by joint_categories → joint_users →
      cosine_similarity (like "friends" but only among high-similarity personas).

    The returned DataFrame is a subset of persona_details (same index labels) with
    three extra columns: ``_joint_categories``, ``_joint_users``, ``_similarity``.
    """
    friends_filter = similarity_mode in ("friends", "combined")

    # Build {category -> set of selected accounts} when filtering is requested.
    cat_to_accounts: dict[str, set[str]] | None = None
    if friends_filter and session.selected_accounts:
        selected_lower = {a.lower() for a in session.selected_accounts}
        accounts_df = get_accounts()
        for _, row in accounts_df[
            accounts_df["twitter_name"].str.lower().isin(selected_lower)
        ].iterrows():
            if cat_to_accounts is None:
                cat_to_accounts = {}
            cat_to_accounts.setdefault(row["category"], set()).add(
                str(row["twitter_name"]).lower()
            )

    def _joint_scores(follows_list) -> tuple[int, int]:
        if cat_to_accounts is None or not isinstance(follows_list, list):
            return 0, 0
        follows_lower = {f.lower() for f in follows_list}
        joint_cats = sum(
            1
            for cat_accounts in cat_to_accounts.values()
            if cat_accounts & follows_lower
        )
        joint_users = sum(
            len(cat_accounts & follows_lower)
            for cat_accounts in cat_to_accounts.values()
        )
        return joint_cats, joint_users

    scored = persona_details.copy()
    joint = scored["follows_list"].apply(_joint_scores)
    scored["_joint_categories"] = joint.apply(lambda t: t[0])
    scored["_joint_users"] = joint.apply(lambda t: t[1])

    # Cosine similarity against the user's mean vector (computed early for combined mode).
    sv_matrix = np.stack(scored["sv"].values)
    all_similarities = cosine_similarity(
        sv_matrix, session.user_mean_vector.reshape(1, -1)
    ).flatten()
    scored["_similarity"] = all_similarities

    # Apply filtering based on mode.
    if similarity_mode == "combined":
        # First filter by similarity threshold.
        candidates = scored[scored["_similarity"] >= similarity_threshold]
        if candidates.empty:
            # No persona met the threshold: fall back to top-20 most similar.
            candidates = scored.nlargest(20, "_similarity")
        # Then apply min_joint_categories filter within threshold-passing personas.
        if cat_to_accounts is not None:
            filtered = candidates[candidates["_joint_categories"] >= min_joint_categories]
            if not filtered.empty:
                candidates = filtered
    elif similarity_mode == "friends":
        # Apply min_joint_categories filter.
        if cat_to_accounts is not None:
            candidates = scored[scored["_joint_categories"] >= min_joint_categories]
            if candidates.empty:
                candidates = scored
        else:
            candidates = scored
    else:
        # "disabled" – no filtering, rank by similarity only.
        candidates = scored

    # Sort: for "disabled" mode, only similarity matters.
    if similarity_mode == "disabled":
        candidates = candidates.sort_values(by=["_similarity"], ascending=[False])
    else:
        candidates = candidates.sort_values(
            by=["_joint_categories", "_joint_users", "_similarity"],
            ascending=[False, False, False],
        )

    return candidates


def find_most_similar_persona(
    session: SessionData,
    persona_details: pd.DataFrame,
    similarity_mode: str = "disabled",
    min_joint_categories: int = 1,
    similarity_threshold: float = 0.3,
) -> int:
    """Return the iloc position (in persona_details) of the best-ranked persona."""
    ranked = _rank_personas(
        session,
        persona_details,
        similarity_mode=similarity_mode,
        min_joint_categories=min_joint_categories,
        similarity_threshold=similarity_threshold,
    )
    return persona_details.index.get_loc(ranked.index[0])


def find_top_n_similar_personas(
    session: SessionData,
    n: int = 10,
    similarity_mode: str = "disabled",
    min_joint_categories: int = 1,
    similarity_threshold: float = 0.3,
) -> list[dict]:
    """Return the top-n best-ranked personas with their scores."""
    persona_details = get_persona_details()
    ranked = _rank_personas(
        session,
        persona_details,
        similarity_mode=similarity_mode,
        min_joint_categories=min_joint_categories,
        similarity_threshold=similarity_threshold,
    )
    results = []
    for label, row in ranked.head(n).iterrows():
        results.append(
            {
                "index": int(persona_details.index.get_loc(label)),
                "screen_name": row["screen_name"],
                "description": str(row.get("description", "")),
                "similarity": float(row["_similarity"]),
                "joint_categories": int(row["_joint_categories"]),
                "joint_users": int(row["_joint_users"]),
                "follows_list": row.get("follows_list", []),
            }
        )
    return results


def _pick_random_persona_below_similarity_threshold(
    session: SessionData,
    persona_details: pd.DataFrame,
    similarity_threshold: float,
) -> tuple[int, np.ndarray]:
    """Pick a random persona whose similarity is below ``similarity_threshold``."""
    if session.user_mean_vector is None:
        idx = random.randint(0, len(persona_details) - 1)
        return idx, np.array([])

    all_embeddings = np.stack(persona_details["sv"].values)
    similarities = cosine_similarity(
        all_embeddings,
        session.user_mean_vector.reshape(1, -1),
    ).flatten()
    candidate_indices = np.where(similarities < similarity_threshold)[0]

    if len(candidate_indices) == 0:
        # Best-effort fallback: when no persona is below the threshold, use the
        # least similar persona available.
        idx = int(np.argmin(similarities))
    else:
        idx = int(random.choice(candidate_indices.tolist()))
    return idx, similarities


def select_persona_for_session(session: SessionData, persona_index: int | None = None) -> dict:
    """
    Select and assign a persona to the session based on chat_type.

    Returns the persona info dict.
    """
    persona_details = get_persona_details()
    chat_type = session.chat_type

    if chat_type == "Personalized Like Me":
        settings = get_settings()
        idx = persona_index if persona_index is not None else find_most_similar_persona(
            session,
            persona_details,
            similarity_mode=get_effective_similarity_with_friends(),
            min_joint_categories=settings.min_joint_categories,
            similarity_threshold=get_effective_similarity_threshold(),
        )
        persona = persona_details.iloc[idx]
        session.user_for_the_chat = persona["screen_name"]
        session.selected_user_similarity = float(
            cosine_similarity(
                np.stack(persona_details["sv"].values),
                session.user_mean_vector.reshape(1, -1),
            ).flatten()[idx]
        )
        session.user_embeddings = np.array(persona["sv"])
        session.selected_user_follow_list = persona.get("follows_list", [])
        return {
            "screen_name": persona["screen_name"],
            "description": str(persona.get("description", "")),
        }

    elif chat_type == "Personalized Random":
        idx, similarities = _pick_random_persona_below_similarity_threshold(
            session,
            persona_details,
            similarity_threshold=get_effective_random_persona_similarity_threshold(),
        )
        persona = persona_details.iloc[idx]
        session.user_for_the_chat = persona["screen_name"]
        session.user_embeddings = np.array(persona["sv"])
        if similarities.size > 0:
            session.selected_user_similarity = float(similarities[idx])
        elif session.user_mean_vector is not None:
            session.selected_user_similarity = float(
                cosine_similarity(
                    np.array(persona["sv"]).reshape(1, -1),
                    session.user_mean_vector.reshape(1, -1),
                ).flatten()[0]
            )
        else:
            session.selected_user_similarity = 0.0
        session.selected_user_follow_list = persona.get("follows_list", [])
        return {
            "screen_name": persona["screen_name"],
            "description": str(persona.get("description", "")),
        }

    elif chat_type in ("PERSONA_ref", "SPC_ref"):
        prefix = chat_type.split("_")[0]
        ref_df = pd.read_excel(f"app/data/{prefix}_selected_personas.xlsx")
        idx = random.randint(0, len(ref_df) - 1)
        row = ref_df.iloc[idx].astype(str)
        session.user_for_the_chat = row["persona_id"]
        return {
            "screen_name": row["persona_id"],
            "description": row["persona"],
        }

    else:
        # vanilla / vanilla_with_prompt
        session.user_for_the_chat = chat_type
        session.selected_user_similarity = 0.0
        return {"screen_name": chat_type, "description": ""}
