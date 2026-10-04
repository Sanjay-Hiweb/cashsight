"""Unit tests for the cash-crunch risk engine."""

import pytest
import pandas as pd
from core.risk_engine import (
    detect_cash_crunches,
    CrunchResult,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)


def test_no_cash_crunch():
    # Balance stays well above safety cushion
    df_forecast = pd.DataFrame({
        "ds": [f"2026-10-{i:02d}" for i in range(1, 15)],
        "projected_balance": [60000.0 + i * 500 for i in range(14)],
        "projected_balance_lower": [50000.0 + i * 400 for i in range(14)],
        "projected_balance_upper": [70000.0 + i * 600 for i in range(14)],
    })

    risk = detect_cash_crunches(df_forecast, safety_cushion=25000.0)
    assert risk.has_crunch is False
    assert len(risk.crunches) == 0
    assert "safe" in risk.headline.lower()


def test_detected_cash_crunch_and_shortfall():
    # Balance drops below safety cushion on Day 5
    lower_balances = [
        30000.0, 28000.0, 27000.0, 26000.0,
        22000.0, 18000.0, 15000.0, 12000.0,  # Below 25,000 cushion
        10000.0, 8000.0, 6000.0, 4000.0, 2000.0, -1000.0
    ]
    df_forecast = pd.DataFrame({
        "ds": [f"2026-10-{i:02d}" for i in range(1, 15)],
        "projected_balance": [bal + 5000.0 for bal in lower_balances],
        "projected_balance_lower": lower_balances,
        "projected_balance_upper": [bal + 10000.0 for bal in lower_balances],
    })

    risk = detect_cash_crunches(df_forecast, safety_cushion=25000.0)
    assert risk.has_crunch is True
    assert len(risk.crunches) > 0

    # Earliest crunch should be Day 5 (2026-10-05)
    earliest = risk.earliest_crunch
    assert earliest.days_away == 5
    assert earliest.crunch_date == "2026-10-05"
    assert earliest.shortfall == 25000.0 - 22000.0  # 3000

    # Worst crunch should be the last day (-1000 balance -> 26000 shortfall)
    worst = risk.worst_crunch
    assert worst.shortfall == 25000.0 - (-1000.0)
    assert worst.is_negative_cash is True

    # Severity should escalate to critical due to negative cash
    assert risk.overall_severity == SEVERITY_CRITICAL
    assert "suggested_action" in dir(earliest)
    assert len(earliest.suggested_action) > 10


def test_empty_forecast_graceful_handling():
    risk = detect_cash_crunches(pd.DataFrame())
    assert risk.has_crunch is False
    assert "no forecast" in risk.headline.lower()
