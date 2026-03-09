# Shared test fixtures.
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    """Provide an httpx async test client wired to the FastAPI app.
    Note: integration tests should mock heavy dependencies (SocialVec, OpenAI)."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
