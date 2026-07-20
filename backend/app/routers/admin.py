# Admin endpoints – password-protected runtime settings management.
from __future__ import annotations

import secrets
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.config import get_settings
from app.runtime_settings import (
    ALLOWED_CHAT_TYPES,
    ALLOWED_MODELS,
    ALLOWED_SIMILARITY_MODES,
    ALLOWED_PERSONA_BANKS,
    ALLOWED_RECOMMENDATION_MODES,
    ALL_TASK_KEYS,
    DEFAULT_REQUIRED_TASKS,
    get_current_overrides,
    get_effective_persona_bank,
    get_effective_required_tasks,
    update_runtime_settings,
)
from app.dependencies import get_loaded_persona_bank, reload_persona_details

router = APIRouter()

# ── In-memory token (reset on server restart) ────────────────────────────────

_admin_token: Optional[str] = None
_security = HTTPBearer()


def _require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> None:
    if _admin_token is None or credentials.credentials != _admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── Models ───────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


class AdminSettings(BaseModel):
    types_of_chat_list: list[str]
    similarity_with_friends: str
    similarity_threshold: float
    random_persona_similarity_threshold: float
    minimal_number_of_messages: int
    openai_model: str
    debug: bool
    persona_bank: str
    recommendation_mode: str
    required_tasks: dict[str, bool] = Field(
        default_factory=lambda: dict(DEFAULT_REQUIRED_TASKS)
    )


class OptionsResponse(BaseModel):
    allowed_chat_types: list[str]
    allowed_models: list[str]
    allowed_similarity_modes: list[str]
    allowed_persona_banks: list[str]
    allowed_recommendation_modes: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/login", response_model=LoginResponse)
async def admin_login(body: LoginRequest) -> LoginResponse:
    """Validate the admin password and return a short-lived bearer token."""
    global _admin_token
    settings = get_settings()
    if body.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    _admin_token = secrets.token_urlsafe(32)
    return LoginResponse(token=_admin_token)


@router.get("/options", response_model=OptionsResponse)
async def get_options(_: None = Depends(_require_admin)) -> OptionsResponse:
    """Return the list of allowed values for each setting."""
    return OptionsResponse(
        allowed_chat_types=ALLOWED_CHAT_TYPES,
        allowed_models=ALLOWED_MODELS,
        allowed_similarity_modes=ALLOWED_SIMILARITY_MODES,
        allowed_persona_banks=ALLOWED_PERSONA_BANKS,
        allowed_recommendation_modes=ALLOWED_RECOMMENDATION_MODES,
    )


@router.get("/settings", response_model=AdminSettings)
async def get_admin_settings(_: None = Depends(_require_admin)) -> AdminSettings:
    """Return the currently effective settings (env defaults + any runtime overrides)."""
    current = get_current_overrides()
    return AdminSettings(**current)


@router.put("/settings", response_model=AdminSettings)
async def put_admin_settings(
    body: AdminSettings,
    _: None = Depends(_require_admin),
) -> AdminSettings:
    """Override runtime settings. Values persist until the server is restarted."""
    for ct in body.types_of_chat_list:
        if ct not in ALLOWED_CHAT_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid chat type '{ct}'. Allowed: {ALLOWED_CHAT_TYPES}",
            )
    if body.openai_model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid model '{body.openai_model}'. Allowed: {ALLOWED_MODELS}",
        )
    if body.similarity_with_friends not in ALLOWED_SIMILARITY_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid similarity mode '{body.similarity_with_friends}'. Allowed: {ALLOWED_SIMILARITY_MODES}",
        )
    if not 0.0 <= body.similarity_threshold <= 1.0:
        raise HTTPException(
            status_code=422,
            detail="similarity_threshold must be between 0.0 and 1.0",
        )
    if not 0.0 <= body.random_persona_similarity_threshold <= 1.0:
        raise HTTPException(
            status_code=422,
            detail="random_persona_similarity_threshold must be between 0.0 and 1.0",
        )
    if body.minimal_number_of_messages < 1:
        raise HTTPException(
            status_code=422,
            detail="minimal_number_of_messages must be at least 1",
        )
    if not body.types_of_chat_list:
        raise HTTPException(
            status_code=422,
            detail="types_of_chat_list must contain at least one entry",
        )
    if body.persona_bank not in ALLOWED_PERSONA_BANKS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid persona_bank '{body.persona_bank}'. Allowed: {ALLOWED_PERSONA_BANKS}",
        )
    if body.recommendation_mode not in ALLOWED_RECOMMENDATION_MODES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid recommendation_mode '{body.recommendation_mode}'. Allowed: {ALLOWED_RECOMMENDATION_MODES}",
        )
    invalid_task_keys = [k for k in body.required_tasks if k not in ALL_TASK_KEYS]
    if invalid_task_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid required_tasks keys: {invalid_task_keys}. Allowed: {ALL_TASK_KEYS}",
        )
    if not any(body.required_tasks.get(k, False) for k in ALL_TASK_KEYS):
        raise HTTPException(
            status_code=422,
            detail="At least one task must be required",
        )

    # Hot-swap persona bank in memory if it changed from what's currently loaded.
    loaded_bank = get_loaded_persona_bank() or get_effective_persona_bank()
    if body.persona_bank != loaded_bank:
        try:
            reload_persona_details(body.persona_bank)
        except FileNotFoundError:
            raise HTTPException(
                status_code=422,
                detail=f"Persona bank file 'persona_details_{body.persona_bank}.pkl' not found in data directory.",
            )

    update_runtime_settings(
        types_of_chat_list=body.types_of_chat_list,
        similarity_with_friends=body.similarity_with_friends,
        similarity_threshold=body.similarity_threshold,
        random_persona_similarity_threshold=body.random_persona_similarity_threshold,
        minimal_number_of_messages=body.minimal_number_of_messages,
        openai_model=body.openai_model,
        debug=body.debug,
        persona_bank=body.persona_bank,
        recommendation_mode=body.recommendation_mode,
        required_tasks=body.required_tasks,
    )
    return AdminSettings(**get_current_overrides())
