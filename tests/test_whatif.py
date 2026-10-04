"""Unit tests for the What-If payment-delay simulator."""

import pytest
import pandas as pd
from core.whatif_simulator import simulate_payment_delay
from data.generate_sample_data import generate_retail_shop_data
from config import TRANSACTION_TYPE_OUTFLOW, TRANSACTION_TYPE_INFLOW


def test_whatif_non_mutating():
    txns = generate_retail_shop_data(history_days=60, seed=101)
    original_dates = txns["date"].copy().tolist()

    # Find first outflow transaction
    outflow_indices = txns.index[txns["type"] == TRANSACTION_TYPE_OUTFLOW].tolist()
    assert len(outflow_indices) > 0
    target_idx = outflow_indices[-1]

    # Run simulation with 7 days delay
    result = simulate_payment_delay(
        transactions=txns,
        payment_index=target_idx,
        delay_days=7,
        current_balance=40000.0,
        safety_cushion=25000.0,
        method="statsmodels",
    )

    # CRITICAL CHECK: Original DataFrame dates must NOT have mutated
    assert txns["date"].tolist() == original_dates
    assert result.delay_days == 7
    assert result.payment_description == txns.loc[target_idx, "description"]
    assert result.amount == txns.loc[target_idx, "amount"]


def test_whatif_rejects_inflow():
    txns = generate_retail_shop_data(history_days=30, seed=102)
    inflow_indices = txns.index[txns["type"] == TRANSACTION_TYPE_INFLOW].tolist()

    with pytest.raises(ValueError, match="Only outflow"):
        simulate_payment_delay(
            transactions=txns,
            payment_index=inflow_indices[0],
            delay_days=5,
            current_balance=30000.0,
        )


def test_whatif_zero_delay():
    txns = generate_retail_shop_data(history_days=30, seed=103)
    outflow_indices = txns.index[txns["type"] == TRANSACTION_TYPE_OUTFLOW].tolist()

    result = simulate_payment_delay(
        transactions=txns,
        payment_index=outflow_indices[0],
        delay_days=0,
        current_balance=30000.0,
        method="statsmodels",
    )
    assert result.delay_days == 0
    assert result.shortfall_difference == 0.0
