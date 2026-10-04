"""Unit tests for Account Aggregator sandbox adapter and ingestion parity."""

import pytest
import pandas as pd
from aggregator.setu_sandbox import SetuSandboxAdapter
from aggregator.csv_import import parse_and_validate_csv
from config import APPROVED_CATEGORIES, TRANSACTION_TYPE_INFLOW, TRANSACTION_TYPE_OUTFLOW


def test_setu_consent_lifecycle():
    adapter = SetuSandboxAdapter()
    consent = adapter.create_consent_request("user_123", "9876543210", data_period_days=90)
    assert consent.is_active is True
    assert consent.provider == "Setu AA Sandbox"

    # Fetch transactions with active consent
    res = adapter.fetch_sandbox_transactions(consent.consent_id)
    assert res.success is True
    assert res.data is not None
    assert len(res.data) > 0

    # Revoke consent
    assert adapter.revoke_consent(consent.consent_id) is True
    # Attempt fetch after revocation should fail
    res_after = adapter.fetch_sandbox_transactions(consent.consent_id)
    assert res_after.success is False
    assert "REVOKED" in res_after.error_message


def test_ingestion_parity():
    """Confirms that transactions ingested from Setu AA Sandbox conform to the exact

    same canonical schema as CSV ingested data.
    """
    adapter = SetuSandboxAdapter()
    consent = adapter.create_consent_request("user_parity", "9876543210")
    aa_result = adapter.fetch_sandbox_transactions(consent.consent_id)
    assert aa_result.success is True
    df_aa = aa_result.data

    # Canonical columns check
    expected_cols = ["date", "description", "category", "type", "amount"]
    assert list(df_aa.columns) == expected_cols

    # Values validation
    for _, row in df_aa.iterrows():
        assert row["category"] in APPROVED_CATEGORIES
        assert row["type"] in [TRANSACTION_TYPE_INFLOW, TRANSACTION_TYPE_OUTFLOW]
        assert row["amount"] > 0.0
