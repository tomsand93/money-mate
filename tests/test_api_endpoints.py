"""
Flask test-client integration tests for key API endpoints.
"""
import json
from unittest.mock import MagicMock, patch


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_signup_page_renders(client):
    response = client.get("/signup")
    assert response.status_code == 200


def test_upload_redirects_when_unauthenticated(client):
    response = client.get("/upload")
    assert response.status_code in (302, 308)
    assert "/login" in response.headers.get("Location", "")


def test_dashboard_redirects_when_unauthenticated(client):
    response = client.get("/")
    assert response.status_code in (302, 308)


def test_reports_redirects_when_unauthenticated(client):
    response = client.get("/reports")
    assert response.status_code in (302, 308)


def test_login_next_param_relative_redirect_allowed(app, client):
    with patch("auth.SupabaseAuth.sign_in", return_value=(True, "ok", MagicMock())):
        with patch("auth.SupabaseAuth.is_authenticated", return_value=False):
            resp = client.post(
                "/login?next=/reports",
                data={"email": "a@b.com", "password": "pass123"},
                follow_redirects=False,
            )
            location = resp.headers.get("Location", "")
            assert "/reports" in location
            assert location.startswith("/")


def test_login_next_param_external_url_rejected(app, client):
    with patch("auth.SupabaseAuth.sign_in", return_value=(True, "ok", MagicMock())):
        with patch("auth.SupabaseAuth.is_authenticated", return_value=False):
            resp = client.post(
                "/login?next=http://evil.com",
                data={"email": "a@b.com", "password": "pass123"},
                follow_redirects=False,
            )
            location = resp.headers.get("Location", "")
            assert "evil.com" not in location


def test_api_categorize_requires_auth(client):
    resp = client.post(
        "/api/categorize",
        json={"business_name": "Test", "category": "מזון"},
    )
    assert resp.status_code in (302, 308, 401)


def test_api_categorize_missing_params_returns_400(auth_client, app):
    with patch("extensions.ai_categorizer") as mock_ai:
        mock_ai._save_correction.return_value = []
        resp = auth_client.post("/api/categorize", json={})
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["success"] is False


def test_api_categorize_success(auth_client, app):
    with patch("extensions.ai_categorizer") as mock_ai:
        mock_ai._save_correction.return_value = []
        resp = auth_client.post(
            "/api/categorize",
            json={"business_name": "סופרמרקט", "category": "מזון"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["success"] is True


def test_update_transaction_category_missing_params(auth_client, app):
    with patch("db_utils.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.get_user_id.return_value = "test-user-uuid"

        resp = auth_client.post("/update_transaction_category", json={})
        assert resp.status_code == 400


def test_update_transaction_category_not_found(auth_client, app):
    with patch("db_utils.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.get_user_id.return_value = "test-user-uuid"
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=None)
        mock_db.client.table.return_value = chain
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.maybe_single.return_value = chain
        mock_get_db.return_value = mock_db

        resp = auth_client.post(
            "/update_transaction_category",
            json={"id": "nonexistent-uuid", "category": "מזון"},
        )
        assert resp.status_code == 404
