"""End-to-End Integration Tests for CashSight MVP.

Verifies complete user journeys from ingestion to forecasting, risk detection,
What-If simulation, database persistence, and data deletion (Right to Erasure).
Follows docs/TODO.md TEST-002, TEST-003, TEST-004.
"""

import io
import pytest
import pandas as pd
from storage.db import DatabaseManager
from aggregator.csv_import import parse_and_validate_csv
from aggregator.setu_sandbox import SetuSandboxAdapter
from data.data_loader import aggregate_daily_net_cash_flow
from core.forecasting import forecast_cash_balance
from core.risk_engine import detect_cash_crunches
from core.whatif_simulator import simulate_payment_delay
from data.generate_sample_data import generate_retail_shop_data


def test_full_csv_journey_e2e(tmp_path):
    # 1. Setup isolated database
    test_db = DatabaseManager(db_path=tmp_path / "e2e_cashsight.db")

    # 2. User Onboarding
    user_id = test_db.save_user({
        "name": "Sunil Gupta",
        "phone": "9811223344",
        "business_name": "Gupta Hardware Store",
        "business_type": "Hardware / Electrical",
        "language": "hi",
        "safety_cushion": 20000.0,
        "current_balance": 35000.0,
    })
    test_db.record_consent(user_id, "CSV Upload")

    # 3. CSV Ingestion
    sample_df = generate_retail_shop_data(history_days=90, seed=555)
    csv_buffer = io.StringIO()
    sample_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    val_res = parse_and_validate_csv(csv_buffer)
    assert val_res.is_valid is True
    assert val_res.valid_rows > 0

    # 4. Save to Database
    saved_count = test_db.save_transactions(user_id, val_res.data, source="csv")
    assert saved_count == val_res.valid_rows

    # 5. Retrieve from Database and Aggregate
    db_txns = test_db.get_transactions(user_id)
    assert len(db_txns) == saved_count
    daily_df = aggregate_daily_net_cash_flow(db_txns)
    assert len(daily_df) >= 90

    # 6. Run Forecasting (Prophet & Statsmodels)
    forecast_res = forecast_cash_balance(daily_df, current_balance=35000.0, horizon_days=14, method="statsmodels")
    assert len(forecast_res.forecast_df) == 14

    # 7. Evaluate Cash Crunches
    risk_res = detect_cash_crunches(forecast_res, safety_cushion=20000.0)
    assert risk_res.headline != ""
    assert len(risk_res.summary_message) > 0

    # 8. Run What-If Simulation on an outflow
    outflows = db_txns[db_txns["type"] == "outflow"]
    target_idx = outflows.index[-1]
    whatif_res = simulate_payment_delay(
        transactions=db_txns,
        payment_index=target_idx,
        delay_days=7,
        current_balance=35000.0,
        safety_cushion=20000.0,
        method="statsmodels",
    )
    assert whatif_res.delay_days == 7
    assert len(whatif_res.plain_language_summary) > 0

    # 9. Consent Revocation and Erasure
    test_db.revoke_consent(user_id)
    assert test_db.has_active_consent(user_id) is False

    del_res = test_db.delete_user_data(user_id)
    assert del_res["success"] is True
    assert test_db.get_user(user_id) is None
    assert len(test_db.get_transactions(user_id)) == 0


def test_full_aa_sandbox_journey_e2e(tmp_path):
    # 1. Setup isolated database
    test_db = DatabaseManager(db_path=tmp_path / "e2e_aa.db")

    # 2. User Onboarding
    user_id = test_db.save_user({
        "name": "Kavita Rao",
        "phone": "9845012345",
        "business_name": "Rao Silks & Sarees",
        "business_type": "Clothing / Apparel",
        "language": "kn",
        "safety_cushion": 25000.0,
        "current_balance": 40000.0,
    })

    # 3. Account Aggregator Consent Flow
    adapter = SetuSandboxAdapter()
    consent = adapter.create_consent_request(user_id, "9845012345")
    test_db.record_consent(user_id, provider=adapter.PROVIDER_NAME)

    # 4. Fetch Sandbox Transactions
    ext_res = adapter.fetch_sandbox_transactions(consent.consent_id)
    assert ext_res.success is True
    assert ext_res.data is not None

    # 5. Persist to Database
    test_db.save_transactions(user_id, ext_res.data, source="setu_sandbox")
    retrieved = test_db.get_transactions(user_id)
    assert len(retrieved) == len(ext_res.data)
