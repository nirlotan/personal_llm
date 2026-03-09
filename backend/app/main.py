# FastAPI application entry point.
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import startup
from app.routers import sessions, profile, chat, feedback, debug

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_firebase() -> None:
    """Try to initialise Firebase at startup so misconfiguration is visible immediately."""
    import json
    from app.firebase import get_firebase_app
    settings = get_settings()

    cert = settings.firebase_certificate_json
    db_url = settings.firebase_db_url

    # Detect obvious placeholders
    if not cert or "..." in cert or "your-project" in db_url:
        logger.warning(
            "⚠️  Firebase credentials look like placeholders — "
            "set FIREBASE_CERTIFICATE_JSON and FIREBASE_DB_URL in backend/.env "
            "(or keep using .streamlit/secrets.toml). Firebase writes will fail until fixed."
        )
        return

    # Validate the JSON is parseable and has expected keys
    try:
        parsed = json.loads(cert)
        assert "private_key" in parsed and "client_email" in parsed
    except Exception as exc:
        logger.error("❌ FIREBASE_CERTIFICATE_JSON is not valid service-account JSON: %s", exc)
        return

    try:
        get_firebase_app()
        logger.info(
            "✅ Firebase initialised  db=%s  path=%s",
            db_url, settings.experiment_feedback_path,
        )
    except Exception as exc:
        logger.error("❌ Firebase initialisation failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await startup()
    _validate_firebase()
    yield  # app is running
    # Shutdown logic (if any) goes here


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(profile.router, prefix="/api", tags=["profile"])
    app.include_router(chat.router, prefix="/api/sessions", tags=["chat"])
    app.include_router(feedback.router, prefix="/api", tags=["feedback"])
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
