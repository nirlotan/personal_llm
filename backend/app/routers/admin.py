# Admin endpoints – password-protected runtime settings management.
from __future__ import annotations

import secrets
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings
from app.runtime_settings import (
    ALLOWED_CHAT_TYPES,
    ALLOWED_MODELS,
    ALLOWED_SIMILARITY_MODES,
    ALLOWED_PERSONA_BANKS,
    get_current_overrides,
    get_effective_persona_bank,
    update_runtime_settings,
)
from app.dependencies import reload_persona_details

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
    openai_model: str
    debug: bool
    persona_bank: str


class OptionsResponse(BaseModel):
    allowed_chat_types: list[str]
    allowed_models: list[str]
    allowed_similarity_modes: list[str]
    allowed_persona_banks: list[str]


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

    # Hot-swap persona bank in memory if it changed
    if body.persona_bank != get_effective_persona_bank():
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
        openai_model=body.openai_model,
        debug=body.debug,
        persona_bank=body.persona_bank,
    )
    return AdminSettings(**get_current_overrides())
