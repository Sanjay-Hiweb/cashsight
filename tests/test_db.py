"""Unit tests for SQLite storage, persistence, consent, and data deletion."""

import os
from pathlib import Path
import pytest
import pandas as pd
from storage.db import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_cashsight.db"
    mgr = DatabaseManager(db_path=db_file)
    return mgr


def test_user_creation_and_retrieval(temp_db):
    user_id = temp_db.save_user({
        "name": "Karan Verma",
        "phone": "9876543210",
        "business_name": "Verma Cloth Store",
        "business_type": "Clothing / Apparel",
        "language": "hi",
        "safety_cushion": 30000.0,
        "current_balance": 55000.0,
    })

    user = temp_db.get_user(user_id)
    assert user is not None
    assert user["name"] == "Karan Verma"
    assert user["business_name"] == "Verma Cloth Store"
    assert user["safety_cushion"] == 30000.0
    assert user["current_balance"] == 55000.0

    trial = temp_db.get_trial_status(user_id)
    assert trial["is_valid_user"] is True
    assert trial["days_remaining"] == 30
    assert trial["is_trial_expired"] is False


def test_consent_and_revocation(temp_db):
    user_id = temp_db.save_user({
        "name": "Sita Ram",
        "phone": "9123456789",
        "business_name": "Sita Ram Traders",
        "business_type": "Wholesale / Trading",
    })

    assert temp_db.has_active_consent(user_id) is False

    consent_id = temp_db.record_consent(user_id, provider="Setu AA Sandbox")
    assert temp_db.has_active_consent(user_id) is True

    temp_db.revoke_consent(user_id, consent_id)
    assert temp_db.has_active_consent(user_id) is False


def test_transactions_persistence(temp_db):
    user_id = temp_db.save_user({
        "name": "Anil Hardware",
        "phone": "9988776655",
        "business_name": "Anil Electricals",
        "business_type": "Hardware / Electrical",
    })

    df = pd.DataFrame([
        {"date": "2026-09-01", "description": "Pipe Supplier", "category": "supplier", "type": "outflow", "amount": 15000.0},
        {"date": "2026-09-02", "description": "Counter UPI", "category": "sales", "type": "inflow", "amount": 8000.0},
    ])

    count = temp_db.save_transactions(user_id, df, source="csv")
    assert count == 2

    retrieved = temp_db.get_transactions(user_id)
    assert len(retrieved) == 2
    assert retrieved["amount"].iloc[0] == 15000.0


def test_user_data_deletion_right_to_erasure(temp_db):
    user_id = temp_db.save_user({
        "name": "Dev User",
        "phone": "9000000000",
        "business_name": "Dev Shop",
        "business_type": "Other Retail",
    })
    temp_db.record_consent(user_id, "CSV Upload")
    df = pd.DataFrame([{"date": "2026-09-01", "description": "Sale", "category": "sales", "type": "inflow", "amount": 1000.0}])
    temp_db.save_transactions(user_id, df)

    # Perform full erasure
    res = temp_db.delete_user_data(user_id)
    assert res["success"] is True
    assert res["deleted"]["users"] == 1
    assert res["deleted"]["transactions"] == 1
    assert res["deleted"]["consents"] == 1

    # Confirm user, txns, and consents are gone
    assert temp_db.get_user(user_id) is None
    assert len(temp_db.get_transactions(user_id)) == 0
    assert temp_db.has_active_consent(user_id) is False
