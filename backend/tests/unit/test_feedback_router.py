import pytest
from fastapi.testclient import TestClient

from app.services.session_service import SessionData
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _completed_eligible_prolific_session() -> SessionData:
    session = SessionData(session_id="PID123__STUDY456__SES789", user_from_prolific=True)
    session.required_feedback_rounds = 2
    session.number_of_feedbacks_provided = 2
    session.attention_checks_passed = 2
    session.attention_checks_failed = 0
    session.eligible_for_completion_credit = True
    return session


def test_completion_info_returns_prolific_redirect_with_configured_code(client, monkeypatch):
    session = _completed_eligible_prolific_session()

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "ABC123"

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion")

    assert resp.status_code == 200
    body = resp.json()
    assert body["redirect_url"] == f"/api/sessions/{session.session_id}/completion/redirect"
    assert body["session_id"] == session.session_id


def test_completion_info_returns_prolific_fallback_code_when_config_missing(client, monkeypatch):
    session = _completed_eligible_prolific_session()

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "   "

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion")

    assert resp.status_code == 200
    body = resp.json()
    assert body["redirect_url"] == f"/api/sessions/{session.session_id}/completion/redirect"
    assert body["session_id"] == session.session_id


def test_completion_info_non_prolific_gets_no_redirect(client, monkeypatch):
    session = SessionData(session_id="regular-session-id", user_from_prolific=False)
    session.required_feedback_rounds = 1
    session.number_of_feedbacks_provided = 1
    session.attention_checks_passed = 1

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "ABC123"

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion")

    assert resp.status_code == 200
    body = resp.json()
    assert body["redirect_url"] is None
    assert body["session_id"] == session.session_id


def test_completion_info_rejects_incomplete_survey(client, monkeypatch):
    session = SessionData(session_id="PID123__STUDY456__SES789", user_from_prolific=True)
    session.required_feedback_rounds = 2
    session.number_of_feedbacks_provided = 1
    session.attention_checks_passed = 1

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "ABC123"

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion")

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Survey not fully completed"


def test_completion_info_rejects_attention_failure(client, monkeypatch):
    session = _completed_eligible_prolific_session()
    session.attention_checks_failed = 1
    session.eligible_for_completion_credit = False

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "ABC123"

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion")

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Survey completion not eligible for credit"


def test_completion_redirect_endpoint_redirects_with_configured_code(client, monkeypatch):
    session = _completed_eligible_prolific_session()

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "ABC123"

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion/redirect", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == "https://app.prolific.com/submissions/complete?cc=ABC123"


def test_completion_redirect_endpoint_uses_fallback_code_when_empty(client, monkeypatch):
    session = _completed_eligible_prolific_session()

    monkeypatch.setattr("app.routers.feedback.get_session", lambda session_id: session)

    class DummySettings:
        prolific_approval = "   "

    monkeypatch.setattr("app.routers.feedback.get_settings", lambda: DummySettings())

    resp = client.get(f"/api/sessions/{session.session_id}/completion/redirect", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == "https://app.prolific.com/submissions/complete?cc=C3KTZS0A"
