# Pydantic schemas for feedback / survey.
from __future__ import annotations

from pydantic import BaseModel


class SurveyQuestion(BaseModel):
    index: int
    short_label: str
    label: str
    description: str


class SurveyQuestionsResponse(BaseModel):
    questions: list[SurveyQuestion]


class FeedbackSubmission(BaseModel):
    ratings: dict[str, float]  # short_label → rating (1-5)
    free_text: str = ""
