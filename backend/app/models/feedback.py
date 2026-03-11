# Pydantic schemas for feedback / survey.
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SurveyQuestion(BaseModel):
    index: int
    short_label: str
    label: str
    description: str


class SurveyQuestionsResponse(BaseModel):
    questions: list[SurveyQuestion]


class FeedbackSubmission(BaseModel):
    ratings: dict[str, float]  # short_label → rating (1-5)
    free_text: str = Field(default="", max_length=2000)

    @field_validator("ratings")
    @classmethod
    def ratings_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        for key, val in v.items():
            if not (1 <= val <= 5):
                raise ValueError(f"Rating for '{key}' must be between 1 and 5")
        return v
