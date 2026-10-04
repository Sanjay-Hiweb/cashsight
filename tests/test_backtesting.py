"""Unit tests for the forecast backtesting validation module."""

import pytest
import pandas as pd
from core.backtesting import evaluate_forecast_backtest
from data.generate_sample_data import generate_retail_shop_data
from data.data_loader import aggregate_daily_net_cash_flow


def test_forecast_backtesting_execution():
    # Generate 120 days history
    txns = generate_retail_shop_data(history_days=120, seed=42)
    daily = aggregate_daily_net_cash_flow(txns)

    report = evaluate_forecast_backtest(
        historical_net_cash_flow=daily,
        initial_balance=35000.0,
        test_horizon_days=14,
        safety_cushion=25000.0,
        method="statsmodels",
    )

    assert report.status == "EVALUATED"
    assert report.test_horizon_days == 14
    assert report.mae >= 0.0
    assert report.rmse >= 0.0
    assert 0.0 <= report.direction_accuracy_pct <= 100.0
    assert len(report.notes) > 0


def test_backtesting_insufficient_history():
    short_df = pd.DataFrame({
        "ds": [f"2026-09-{i:02d}" for i in range(1, 15)],
        "y": [1000.0] * 14,
    })
    with pytest.raises(ValueError, match="at least"):
        evaluate_forecast_backtest(short_df, initial_balance=10000.0, test_horizon_days=14)
