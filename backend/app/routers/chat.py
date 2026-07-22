# Chat endpoints – prepare, message, status.
from __future__ import annotations

import logging

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

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
from app.runtime_settings import (
    get_effective_minimal_number_of_messages,
    get_effective_types_of_chat_list,
    get_effective_required_tasks,
)


router = APIRouter()
logger = logging.getLogger(__name__)


def _sync_chat_types_for_unstarted_session(session) -> None:
    """Apply current runtime chat types only before the first chat starts."""
    if session.chat_messages:
        return
    if session.chat_type is not None:
        return
    if session.number_of_feedbacks_provided > 0:
        return
    session.remaining_chat_types = list(get_effective_types_of_chat_list())


@router.post("/{session_id}/chat/prepare", response_model=ChatPrepareResponse)
async def prepare_chat(session_id: str, persona_index: int | None = None):
    """Assign chat type, select persona, build system prompt, inject first message."""
    import time as _time
    _t0 = _time.perf_counter()

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # A session can be created before admin runtime settings are changed.
    # Re-sync pending chat types right before the very first prepare call.
    _sync_chat_types_for_unstarted_session(session)

    try:
        # Pick a random chat type from remaining
        chat_type = pick_random_chat_type(session)
        logger.info("[prepare:%s] step=pick_chat_type elapsed_ms=%.0f", session_id, (_time.perf_counter()-_t0)*1000)

        # Select persona and get description
        persona_info = select_persona_for_session(session, persona_index=persona_index)
        logger.info("[prepare:%s] step=select_persona elapsed_ms=%.0f", session_id, (_time.perf_counter()-_t0)*1000)

        # Build system prompt
        prompt = build_system_prompt(session, persona_info["description"])
        logger.info("[prepare:%s] step=build_prompt elapsed_ms=%.0f", session_id, (_time.perf_counter()-_t0)*1000)

        # Auto-inject first bot message (blocking LLM call – run off the event loop)
        first_msg = await run_in_threadpool(get_first_message, session)
        logger.info("[prepare:%s] step=first_message elapsed_ms=%.0f", session_id, (_time.perf_counter()-_t0)*1000)

    except ValueError as exc:
        # E.g. no more chat types remaining
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("[prepare:%s] FAILED elapsed_ms=%.0f error=%s", session_id, (_time.perf_counter()-_t0)*1000, exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to prepare chat. Check model credentials and runtime model settings. "
                f"Root error: {exc}"
            ),
        )

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

    try:
        result = send_message(session, body.content)
    except Exception as exc:
        logger.exception("Failed to generate chat response for session %s", session_id)
        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to generate a chat response. Check model credentials and runtime model settings. "
                f"Root error: {exc}"
            ),
        )
    return ChatMessageResponse(**result)


@router.get("/{session_id}/chat/status", response_model=ChatStatusResponse)
async def get_chat_status(session_id: str):
    """Return task checklist, message count, and whether user can proceed."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_count = get_message_count(session)
    can_proceed = check_can_proceed(session, get_effective_minimal_number_of_messages())

    return ChatStatusResponse(
        message_count=msg_count,
        tasks=TaskStatus(
            friendly_chat=bool(session.chat_status.get("Friendly Chat")),
            recommendation=bool(session.chat_status.get("Recommendation")),
            second_recommendation=bool(session.chat_status.get("Second Recommendation")),
            stance_request=bool(session.chat_status.get("Stance Request")),
            factual_information=bool(session.chat_status.get("Factual Information Request")),
        ),
        can_proceed=can_proceed,
        min_messages=get_effective_minimal_number_of_messages(),
        required_tasks=get_effective_required_tasks(),
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
