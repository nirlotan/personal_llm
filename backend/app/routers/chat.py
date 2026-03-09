# Chat endpoints – prepare, message, status.
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatPrepareResponse,
    ChatStatusResponse,
    TaskStatus,
)
from app.services.chat_service import (
    check_can_proceed,
    get_first_message,
    get_message_count,
    reset_chat_for_next_round,
    send_message,
)
from app.services.persona_service import (
    find_top_n_similar_personas,
    pick_random_chat_type,
    select_persona_for_session,
)
from app.services.prompt_service import build_system_prompt
from app.services.session_service import get_session

router = APIRouter()


@router.post("/{session_id}/chat/prepare", response_model=ChatPrepareResponse)
async def prepare_chat(session_id: str, persona_index: int | None = None):
    """Assign chat type, select persona, build system prompt, inject first message."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Pick a random chat type from remaining
    chat_type = pick_random_chat_type(session)

    # Select persona and get description
    persona_info = select_persona_for_session(session, persona_index=persona_index)

    # Build system prompt
    prompt = build_system_prompt(session, persona_info["description"])

    # Auto-inject first bot message
    first_msg = get_first_message(session)

    return ChatPrepareResponse(
        chat_type=chat_type,
        system_message_preview=prompt[:200] if prompt else "(empty – vanilla mode)",
    )


@router.get("/{session_id}/chat/first-message")
async def get_chat_first_message(session_id: str):
    """Return the first auto-generated bot message (if any)."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.chat_messages:
        return {"message": None}

    return {"message": session.chat_messages[0]["content"] if session.chat_messages else None}


@router.post("/{session_id}/chat/message", response_model=ChatMessageResponse)
async def post_chat_message(session_id: str, body: ChatMessageRequest):
    """Send a user message and get the LLM response."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.system_message and session.chat_type != "vanilla":
        raise HTTPException(status_code=400, detail="Chat not prepared yet – call /chat/prepare first")

    result = send_message(session, body.content)
    return ChatMessageResponse(**result)


@router.get("/{session_id}/chat/status", response_model=ChatStatusResponse)
async def get_chat_status(session_id: str):
    """Return task checklist, message count, and whether user can proceed."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    settings = get_settings()
    msg_count = get_message_count(session)
    can_proceed = check_can_proceed(session, settings.minimal_number_of_messages)

    return ChatStatusResponse(
        message_count=msg_count,
        tasks=TaskStatus(
            friendly_chat=bool(session.chat_status.get("Friendly Chat")),
            recommendation=bool(session.chat_status.get("Recommendation")),
            factual_information=bool(session.chat_status.get("Factual Information Request")),
        ),
        can_proceed=can_proceed,
    )


@router.get("/{session_id}/chat/messages")
async def get_chat_messages(session_id: str):
    """Return all chat messages (excluding hidden injections)."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Filter: skip the first injected system prompt from visible messages
    visible = []
    for msg in session.chat_messages:
        visible.append({"role": msg["role"], "content": msg["content"]})
    return {"messages": visible}


@router.post("/{session_id}/chat/reset")
async def reset_chat(session_id: str):
    """Reset chat state for the next round (2nd chatbot)."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    reset_chat_for_next_round(session)
    return {"status": "ok", "remaining_chat_types": len(session.remaining_chat_types)}
