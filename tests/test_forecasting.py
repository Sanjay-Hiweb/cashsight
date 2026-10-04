"""Unit tests for the CashSight forecasting engine."""

import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from core.forecasting import (
    forecast_cash_balance,
    InsufficientHistoryError,
    _prepare_history_series,
)
from data.generate_sample_data import generate_retail_shop_data
from data.data_loader import aggregate_daily_net_cash_flow


def test_forecast_insufficient_history():
    # Only 5 days of data
    short_df = pd.DataFrame({
        "ds": ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"],
        "y": [1000, -500, 200, -300, 400],
    })
    with pytest.raises(InsufficientHistoryError):
        forecast_cash_balance(short_df, current_balance=10000.0)


def test_forecast_output_shape_and_columns():
    # 90 days synthetic history
    txns = generate_retail_shop_data(history_days=90, seed=123)
    daily = aggregate_daily_net_cash_flow(txns)

    result = forecast_cash_balance(daily, current_balance=50000.0, horizon_days=14, method="statsmodels")

    assert result.horizon_days == 14
    df = result.forecast_df
    assert len(df) == 14
    expected_cols = [
        "ds", "yhat", "yhat_lower", "yhat_upper",
        "projected_balance", "projected_balance_lower", "projected_balance_upper"
    ]
    for col in expected_cols:
        assert col in df.columns

    # Verify cumulative math: day 1 projected balance == current_balance + yhat_1
    assert df["projected_balance"].iloc[0] == round(50000.0 + df["yhat"].iloc[0], 2)


def test_forecast_prophet_engine():
    txns = generate_retail_shop_data(history_days=60, seed=456)
    daily = aggregate_daily_net_cash_flow(txns)

    result = forecast_cash_balance(daily, current_balance=30000.0, horizon_days=14, method="prophet")
    assert result.horizon_days == 14
    assert len(result.forecast_df) == 14
    assert result.method_used in ["prophet", "statsmodels_exponential_smoothing"]


def test_fallback_exponential_smoothing():
    txns = generate_retail_shop_data(history_days=60, seed=789)
    daily = aggregate_daily_net_cash_flow(txns)

    result = forecast_cash_balance(daily, current_balance=35000.0, horizon_days=14, method="statsmodels")
    assert "statsmodels" in result.method_used
    assert len(result.forecast_df) == 14
    # Conservative lower bound should be <= expected projected balance
    for idx, row in result.forecast_df.iterrows():
        assert row["projected_balance_lower"] <= row["projected_balance"]
        assert row["projected_balance"] <= row["projected_balance_upper"]
