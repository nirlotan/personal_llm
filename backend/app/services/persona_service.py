# Persona matching & chat-type randomisation.
from __future__ import annotations

import random

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from app.config import get_settings
from app.dependencies import get_persona_details
from app.services.session_service import SessionData


def pick_random_chat_type(session: SessionData) -> str:
    """Randomly select one of the remaining chat types and assign it to the session."""
    if not session.remaining_chat_types:
        raise ValueError("No more chat types remaining for this session.")
    choice = random.choice(session.remaining_chat_types)
    session.chat_type = choice
    return choice


def find_most_similar_persona(session: SessionData, friends_filter: bool = False) -> int:
    """
    Return the iloc position (in persona_details) of the most similar persona.

    When friends_filter is True, only personas who follow at least one of the
    user's selected accounts are considered. Falls back to the full set if no
    candidates survive the filter.
    """
    persona_details = get_persona_details()

    if friends_filter and session.selected_accounts:
        selected_lower = {a.lower() for a in session.selected_accounts}
        mask = persona_details["follows_list"].apply(
            lambda fl: isinstance(fl, list)
            and any(f.lower() in selected_lower for f in fl)
        )
        candidates = persona_details[mask]
        if candidates.empty:
            # No persona follows any selected account – fall back to full set
            candidates = persona_details
    else:
        candidates = persona_details

    sv_matrix = np.stack(candidates["sv"].values)
    similarities = cosine_similarity(
        sv_matrix, session.user_mean_vector.reshape(1, -1)
    ).flatten()

    best_in_candidates = int(np.argmax(similarities))
    # Convert candidates-relative position back to persona_details iloc position
    original_label = candidates.index[best_in_candidates]
    return persona_details.index.get_loc(original_label)


def find_top_n_similar_personas(session: SessionData, n: int = 10) -> list[dict]:
    """Return the top-n most similar personas with their similarity scores."""
    persona_details = get_persona_details()
    sv_matrix = np.stack(persona_details["sv"].values)
    similarities = cosine_similarity(
        sv_matrix, session.user_mean_vector.reshape(1, -1)
    ).flatten()
    top_indices = np.argsort(-similarities)[:n]
    results = []
    for idx in top_indices:
        row = persona_details.iloc[idx]
        results.append(
            {
                "index": int(idx),
                "screen_name": row["screen_name"],
                "description": str(row.get("description", "")),
                "similarity": float(similarities[idx]),
                "follows_list": row.get("follows_list", []),
            }
        )
    return results


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
            session, friends_filter=settings.similarity_with_friends
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
        idx = random.randint(0, len(persona_details) - 1)
        persona = persona_details.iloc[idx]
        session.user_for_the_chat = persona["screen_name"]
        session.selected_user_similarity = 0.0
        session.user_embeddings = np.array(persona["sv"])
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
