# Pydantic schemas for chat.
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ChatType(str, Enum):
    VANILLA = "vanilla"
    PERSONALIZED_LIKE_ME = "Personalized Like Me"
    PERSONALIZED_RANDOM = "Personalized Random"
    PERSONA_REF = "PERSONA_ref"
    SPC_REF = "SPC_ref"
    VANILLA_WITH_PROMPT = "vanilla_with_prompt"


class ChatPrepareResponse(BaseModel):
    chat_type: str
    system_message_preview: str  # first 200 chars (debug aid)


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    role: str  # "assistant"
    content: str
    intent: str | None = None
    topic: str | None = None


class TaskStatus(BaseModel):
    friendly_chat: bool = False
    recommendation: bool = False
    factual_information: bool = False


class ChatStatusResponse(BaseModel):
    message_count: int
    tasks: TaskStatus
    can_proceed: bool
