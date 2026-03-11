"""
Pytest configuration and shared fixtures.
Sets up a test Flask app with all external services mocked.
"""
import os
import sys
import types
import pytest
from unittest.mock import MagicMock, patch

# ── Set env vars BEFORE any import that reads them ──────────────────────────
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'test_anon_key')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'test_service_key')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-pytest')


def _ensure_supabase_module():
    """
    Provide a lightweight supabase module stub for test environments where the
    real dependency is not installed yet.
    """
    if 'supabase' in sys.modules:
        return

    try:
        __import__('supabase')
    except ModuleNotFoundError:
        stub = types.ModuleType('supabase')
        stub.Client = object
        stub.create_client = MagicMock()
        sys.modules['supabase'] = stub


_ensure_supabase_module()


def _make_mock_client():
    """Return a chained Supabase mock that handles .table().select().eq().execute() calls."""
    client = MagicMock()
    # Make every chaining method return the same mock
    for method in ('table', 'select', 'insert', 'update', 'delete', 'upsert',
                   'eq', 'gte', 'lt', 'lte', 'order', 'limit', 'in_',
                   'maybe_single', 'execute'):
        getattr(client, method).return_value = client
    client.execute.return_value = MagicMock(data=[])
    return client


@pytest.fixture(scope='session')
def mock_supabase_client():
    return _make_mock_client()


@pytest.fixture(scope='session')
def app(mock_supabase_client):
    """
    Create the Flask test application.
    Patches supabase.create_client globally so SupabaseAuth and SupabaseDatabase
    never try to reach a real Supabase instance.
    """
    with patch('supabase.create_client', return_value=mock_supabase_client):
        # Clear any previously cached modules so the patch applies cleanly
        for mod in list(sys.modules.keys()):
            if any(mod.startswith(m) for m in ('auth', 'supabase_db', 'app',
                                                'extensions', 'db_utils',
                                                'blueprints')):
                sys.modules.pop(mod, None)

        import app as app_module

        flask_app = app_module.app
        flask_app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key-for-pytest',
            'WTF_CSRF_ENABLED': False,
        })
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Flask test client pre-seeded with an authenticated session."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-user-uuid'
        sess['email'] = 'test@example.com'
        sess['access_token'] = 'fake-access-token'
        sess['refresh_token'] = 'fake-refresh-token'
    return client
