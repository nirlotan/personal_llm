# Debug / admin endpoints (feature-flagged).
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.dependencies import get_accounts
from app.services.persona_service import find_top_n_similar_personas, pick_random_chat_type, select_persona_for_session
from app.services.prompt_service import build_system_prompt
from app.services.chat_service import get_first_message
from app.services.session_service import get_session

router = APIRouter()


def _require_debug():
    settings = get_settings()
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Debug mode is not enabled")


@router.get("/personas/{session_id}")
async def get_top_personas(session_id: str, n: int = 10):
    """Return top-N most similar personas for the session's user embedding (debug)."""
    _require_debug()
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_mean_vector is None:
        raise HTTPException(status_code=400, detail="User profile not yet computed")
    return {"personas": find_top_n_similar_personas(session, n=n)}


@router.get("/system-prompt/{session_id}")
async def get_system_prompt(session_id: str):
    """Return the full system prompt for the current chat (debug only)."""
    _require_debug()
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "chat_type": session.chat_type,
        "system_message": session.system_message or "(empty – vanilla mode)",
        "user_for_the_chat": session.user_for_the_chat,
    }


@router.get("/friends-info/{session_id}")
async def get_friends_info(session_id: str):
    """
    Return the similarity score and the overlapping accounts between the selected
    persona's follows_list and the user's selected accounts (debug only).
    Only available when SIMILARITY_WITH_FRIENDS=true.
    """
    _require_debug()
    settings = get_settings()
    if not settings.similarity_with_friends:
        raise HTTPException(
            status_code=403,
            detail="similarity_with_friends is not enabled",
        )
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_mean_vector is None:
        raise HTTPException(status_code=400, detail="User profile not yet computed")
    if not session.user_for_the_chat:
        raise HTTPException(status_code=400, detail="Chat not prepared yet")

    follows = session.selected_user_follow_list or []
    selected = session.selected_accounts or []
    selected_lower = {a.lower() for a in selected}
    joint_names = [f for f in follows if f.lower() in selected_lower]

    # Enrich joint accounts with their category
    accounts_df = get_accounts()
    name_to_category: dict[str, str] = {
        str(row["twitter_name"]).lower(): str(row["category"])
        for _, row in accounts_df.iterrows()
    }
    joint = [
        {"account": name, "category": name_to_category.get(name.lower(), "Unknown")}
        for name in joint_names
    ]

    return {
        "persona": session.user_for_the_chat,
        "similarity_score": round(session.selected_user_similarity, 4),
        "selected_accounts": selected,
        "joint_accounts": joint,
    }


@router.get("/persona-preview/{session_id}/{persona_index}")
async def get_persona_preview(session_id: str, persona_index: int):
    """
    Return the system prompt and friends overlap for a specific persona index
    without mutating the session (debug only).
    """
    _require_debug()
    from app.dependencies import get_persona_details
    from app.services.prompt_service import load_template

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_mean_vector is None:
        raise HTTPException(status_code=400, detail="User profile not yet computed")

    persona_details = get_persona_details()
    if persona_index < 0 or persona_index >= len(persona_details):
        raise HTTPException(status_code=404, detail="Persona index out of range")

    persona = persona_details.iloc[persona_index]
    description = str(persona.get("description", ""))
    screen_name = str(persona["screen_name"])

    # Build system prompt without mutating the session
    chat_type = session.chat_type or "vanilla"
    if chat_type == "vanilla":
        system_prompt = ""
    else:
        template = load_template("base_message.txt")
        system_prompt = template.replace("{character_description}", description)

    # Friends overlap
    follows = list(persona.get("follows_list") or [])
    selected = session.selected_accounts or []
    selected_lower = {a.lower() for a in selected}
    joint_names = [f for f in follows if f.lower() in selected_lower]

    accounts_df = get_accounts()
    name_to_category: dict[str, str] = {
        str(row["twitter_name"]).lower(): str(row["category"])
        for _, row in accounts_df.iterrows()
    }
    joint = [
        {"account": name, "category": name_to_category.get(name.lower(), "Unknown")}
        for name in joint_names
    ]

    return {
        "persona_index": persona_index,
        "screen_name": screen_name,
        "description": description,
        "chat_type": chat_type,
        "system_prompt": system_prompt,
        "selected_accounts": selected,
        "joint_accounts": joint,
    }


@router.post("/prepare-chat/{session_id}")
async def debug_prepare_chat(session_id: str, chat_type: str, persona_index: int | None = None):
    """Prepare a chat with a specific chat_type (debug only)."""
    _require_debug()
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Override chat type directly
    session.chat_type = chat_type
    session.remaining_chat_types = [chat_type]

    persona_info = select_persona_for_session(session, persona_index=persona_index)
    prompt = build_system_prompt(session, persona_info["description"])
    first_msg = get_first_message(session)

    return {
        "chat_type": chat_type,
        "persona": persona_info,
        "system_message": prompt,
        "first_message": first_msg,
    }
