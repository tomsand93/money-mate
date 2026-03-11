"""
Tests for SupabaseDatabase CRUD behavior with a mocked Supabase client.
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


def _make_client():
    client = MagicMock()
    for method in (
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "upsert",
        "eq",
        "gte",
        "lt",
        "lte",
        "order",
        "limit",
        "in_",
        "maybe_single",
    ):
        getattr(client, method).return_value = client
    client.execute.return_value = MagicMock(data=[])
    return client


@pytest.fixture
def db():
    import os

    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "test_key")

    mock_client = _make_client()
    with patch("supabase.create_client", return_value=mock_client):
        from supabase_db import SupabaseDatabase

        database = SupabaseDatabase()
        database.set_user("test-user-uuid")
        return database


def test_get_user_id_returns_set_user(db):
    assert db.get_user_id() == "test-user-uuid"


def test_get_user_id_raises_without_user():
    import os

    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "test_key")
    mock_client = _make_client()
    with patch("supabase.create_client", return_value=mock_client):
        from supabase_db import SupabaseDatabase

        db_fresh = SupabaseDatabase()
    with pytest.raises(ValueError, match="No user set"):
        db_fresh.get_user_id()


def test_add_expenses_empty_dataframe_returns_zero(db):
    assert db.add_expenses(pd.DataFrame()) == 0


def test_add_expenses_skips_rows_without_billing_amount(db):
    df = pd.DataFrame(
        [
            {
                "purchase_date": pd.Timestamp("2024-01-15"),
                "business_name": "Test Shop",
                "billing_amount": None,
                "billing_currency": "ILS",
            }
        ]
    )
    assert db.add_expenses(df) == 0


def test_add_expenses_calls_upsert_for_valid_rows(db):
    db.client.execute.return_value = MagicMock(data=[{"id": 1}])
    df = pd.DataFrame(
        [
            {
                "purchase_date": pd.Timestamp("2024-01-15"),
                "business_name": "Test Shop",
                "billing_amount": 100.0,
                "billing_currency": "ILS",
                "transaction_amount": None,
                "transaction_currency": "ILS",
                "voucher_number": "12345",
                "additional_details": "",
                "category": "מזון",
                "source_file": "test.xlsx",
                "classification_method": "keyword",
                "classification_confidence": 0.95,
                "classification_reason": "סופר",
                "manually_edited": False,
                "is_installment": False,
                "installment_number": None,
                "total_installments": None,
            }
        ]
    )
    db.add_expenses(df)
    assert db.client.upsert.called or db.client.table.called


def test_billing_cycle_dates_default_day_9(db):
    db.get_user_settings = lambda use_cache=True: {"billing_cycle_day": 9, "monthly_income": 0}
    start, end = db.get_billing_cycle_dates(2024, 10)
    assert start == "2024-09-09"
    assert end == "2024-10-09"


def test_billing_cycle_dates_january_wraps_to_previous_year(db):
    db.get_user_settings = lambda use_cache=True: {"billing_cycle_day": 9, "monthly_income": 0}
    start, end = db.get_billing_cycle_dates(2024, 1)
    assert start == "2023-12-09"
    assert end == "2024-01-09"


def test_is_file_processed_returns_false_when_no_data(db):
    db.client.execute.return_value = MagicMock(data=[])
    assert db.is_file_processed("january.xlsx") is False


def test_is_file_processed_returns_true_when_found(db):
    db.client.execute.return_value = MagicMock(data=[{"id": "some-uuid"}])
    assert db.is_file_processed("january.xlsx") is True


def test_get_total_fixed_expenses_sums_amounts(db):
    db.get_all_fixed_expenses = lambda use_cache=True: [
        {"amount": 500.0, "expense_type": "need", "category": "שכירות"},
        {"amount": 200.0, "expense_type": "want", "category": "מנויים"},
    ]
    assert db.get_total_fixed_expenses() == 700.0


def test_get_total_fixed_expenses_empty(db):
    db.get_all_fixed_expenses = lambda use_cache=True: []
    assert db.get_total_fixed_expenses() == 0.0
