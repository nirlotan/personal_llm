# Pydantic schemas for user profile / interest selection.
from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryListResponse(BaseModel):
    categories: list[str]


class Account(BaseModel):
    twitter_screen_name: str
    twitter_name: str
    wikidata_label: str
    wikidata_desc: str
    category: str


class AccountsResponse(BaseModel):
    accounts: list[Account]


class ProfileSubmission(BaseModel):
    """Selected categories and per-category accounts."""
    selected_categories: list[str] = Field(..., min_length=3, max_length=5)
    selected_accounts: list[str] = Field(..., min_length=3)
