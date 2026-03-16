# Profile / interest-selection endpoints.
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.profile import (
    AccountsResponse,
    Account,
    CategoryListResponse,
    ProfileSubmission,
)
from app.services.profile_service import (
    compute_user_embedding,
    list_accounts_for_category,
    list_categories,
)
from app.services.session_service import get_session

router = APIRouter()


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories():
    """Return the list of selectable interest categories."""
    return CategoryListResponse(categories=list_categories())


@router.get("/categories/{category_name}/accounts", response_model=AccountsResponse)
async def get_accounts_for_category(category_name: str):
    """Return accounts available under *category_name*."""
    accounts = list_accounts_for_category(category_name)
    if not accounts:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found or empty")
    return AccountsResponse(accounts=[Account(**a) for a in accounts])


@router.post("/sessions/{session_id}/profile")
async def submit_profile(session_id: str, body: ProfileSubmission):
    """Submit selected categories and accounts; compute user embedding."""
    settings = get_settings()
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    n_cats = len(body.selected_categories)
    if not (settings.min_categories <= n_cats <= settings.max_categories):
        raise HTTPException(
            status_code=422,
            detail=f"Select between {settings.min_categories} and {settings.max_categories} categories",
        )

    session.selected_categories = body.selected_categories
    session.selected_accounts = body.selected_accounts

    try:
        compute_user_embedding(session)
    except ValueError:
        raise HTTPException(status_code=400, detail="Could not compute profile from selected accounts")

    return {"status": "ok", "embedding_computed": True}
