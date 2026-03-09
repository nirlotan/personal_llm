# Firebase client initialisation.
from __future__ import annotations

import json

import firebase_admin
from firebase_admin import credentials, db

from app.config import get_settings


def get_firebase_app() -> firebase_admin.App:
    """Return the default Firebase app, initialising on first call."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()
    cred = credentials.Certificate(json.loads(settings.firebase_certificate_json))
    return firebase_admin.initialize_app(cred, {"databaseURL": settings.firebase_db_url})


def get_feedback_ref(path_override: str | None = None) -> db.Reference:
    """Return a Firebase DB reference for feedback storage."""
    settings = get_settings()
    app = get_firebase_app()
    path = path_override or settings.experiment_feedback_path
    return db.reference(path, app=app, url=settings.firebase_db_url)
