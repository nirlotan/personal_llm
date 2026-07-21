# Firebase client initialisation.
from __future__ import annotations

import json
import os
from contextlib import contextmanager

import firebase_admin
from firebase_admin import credentials, db

from app.config import get_settings


_PROXY_ENV_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


@contextmanager
def firebase_proxyless_env():
    """Temporarily clear proxy env vars for Firebase network calls."""
    previous_values = {name: os.environ.pop(name, None) for name in _PROXY_ENV_VARS}
    try:
        yield
    finally:
        for name, value in previous_values.items():
            if value is not None:
                os.environ[name] = value


def get_firebase_app() -> firebase_admin.App:
    """Return the default Firebase app, initialising on first call."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()
    cert = json.loads(settings.firebase_certificate_json)
    # TOML / env-var storage often preserves literal \n instead of real newlines in the PEM key.
    if "private_key" in cert:
        cert["private_key"] = cert["private_key"].replace("\\n", "\n")
    with firebase_proxyless_env():
        cred = credentials.Certificate(cert)
        return firebase_admin.initialize_app(cred, {"databaseURL": settings.firebase_db_url})


def get_feedback_ref(path_override: str | None = None) -> db.Reference:
    """Return a Firebase DB reference for feedback storage."""
    settings = get_settings()
    app = get_firebase_app()
    path = path_override or settings.experiment_feedback_path
    return db.reference(path, app=app, url=settings.firebase_db_url)
