# Pydantic schemas for user profile / interest selection.
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CategoryListResponse(BaseModel):
    categories: list[str]


class Account(BaseModel):
    twitter_screen_name: str
    twitter_name: str
    display_name: str
    description: str
    category: str


class AccountsResponse(BaseModel):
    accounts: list[Account]


class ProfileSubmission(BaseModel):
    """Selected categories and per-category accounts."""
    selected_categories: list[str] = Field(..., min_length=3, max_length=5)
    selected_accounts: list[str] = Field(..., min_length=3, max_length=100)

    @field_validator("selected_categories", "selected_accounts", mode="before")
    @classmethod
    def items_not_too_long(cls, v: list) -> list:
        for item in v:
            if not isinstance(item, str) or len(item) > 200:
                raise ValueError("Each item must be a string of at most 200 characters")
        return v
