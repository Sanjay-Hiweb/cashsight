"""CashSight Forecast Backtesting & Model Validation Module.

Evaluates forecast accuracy against held-out historical observation periods.
Computes standard statistical metrics (MAE, RMSE, direction accuracy) and
financial alert reliability (false alarms, missed alarms).

Follows docs/ARCHITECTURE.md section 9, docs/PRD.md section 8.2, and docs/RULES.md section 7.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import (
    DEFAULT_SAFETY_CUSHION,
    FORECAST_HORIZON_DAYS,
    MIN_RECOMMENDED_HISTORY_DAYS,
)
from core.forecasting import forecast_cash_balance, _prepare_history_series
from core.risk_engine import detect_cash_crunches


@dataclass
class BacktestReport:
    """Detailed backtest evaluation outcome."""
    model_name: str
    total_history_days: int
    train_days: int
    test_horizon_days: int
    mae: float
    rmse: float
    direction_accuracy_pct: float
    actual_ending_balance: float
    projected_ending_balance: float
    balance_error: float
    actual_crunch_occurred: bool
    predicted_crunch_occurred: bool
    is_false_alarm: bool
    is_missed_alarm: bool
    method_used: str
    status: str  # 'EVALUATED'
    notes: list[str]


def evaluate_forecast_backtest(
    historical_net_cash_flow: pd.DataFrame,
    initial_balance: float,
    test_horizon_days: int = FORECAST_HORIZON_DAYS,
    safety_cushion: float = DEFAULT_SAFETY_CUSHION,
    method: str = "prophet",
) -> BacktestReport:
    """Splits historical data into train and test sets to evaluate forecast performance.

    The last `test_horizon_days` (14 days) are held out as ground truth.
    """
    notes = [
        "[STANDARD PRACTICE] Evaluated on held-out historical window.",
        "[TO VERIFY] Exact production acceptance thresholds require founder approval.",
    ]

    df_clean = _prepare_history_series(historical_net_cash_flow)
    total_days = len(df_clean)

    if total_days < (test_horizon_days + 14):
        raise ValueError(
            f"Backtesting requires at least {test_horizon_days + 14} days of continuous history. "
            f"Provided dataset contains {total_days} days."
        )

    # Train / Test split
    train_df = df_clean.iloc[:-test_horizon_days].copy()
    test_df = df_clean.iloc[-test_horizon_days:].copy()

    # Compute actual balance evolution starting from initial_balance
    # To ground test set: balance at start of test set is initial_balance + cumsum(train net flow)
    train_net_sum = train_df["y"].sum()
    test_starting_balance = initial_balance + train_net_sum

    actual_daily_net = test_df["y"].values
    actual_balances = test_starting_balance + np.cumsum(actual_daily_net)
    actual_ending_bal = float(actual_balances[-1])

    # Run forecast using training set only
    forecast_res = forecast_cash_balance(
        train_df,
        current_balance=test_starting_balance,
        horizon_days=test_horizon_days,
        method=method,
    )
    pred_df = forecast_res.forecast_df

    pred_daily_net = pred_df["yhat"].values
    pred_balances = pred_df["projected_balance"].values
    pred_ending_bal = float(pred_balances[-1])

    # Metrics
    errors = actual_daily_net - pred_daily_net
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # Direction accuracy: sign(pred) == sign(actual)
    actual_signs = np.sign(actual_daily_net)
    pred_signs = np.sign(pred_daily_net)
    matching_directions = np.sum(actual_signs == pred_signs)
    direction_acc = float((matching_directions / test_horizon_days) * 100.0)

    # Balance error
    bal_error = float(abs(actual_ending_bal - pred_ending_bal))

    # Crunch evaluation: Did actual balance drop below safety cushion?
    actual_crunch = bool(np.any(actual_balances < safety_cushion))
    risk_eval = detect_cash_crunches(forecast_res, safety_cushion=safety_cushion)
    predicted_crunch = risk_eval.has_crunch

    false_alarm = predicted_crunch and not actual_crunch
    missed_alarm = actual_crunch and not predicted_crunch

    if false_alarm:
        notes.append("Observation: Model predicted a cash crunch that did not occur (conservative false alarm).")
    elif missed_alarm:
        notes.append("Observation: Model did not predict a cash crunch that did occur (missed alarm).")
    else:
        notes.append("Observation: Model correctly aligned with ground-truth crunch status.")

    return BacktestReport(
        model_name=method,
        total_history_days=total_days,
        train_days=len(train_df),
        test_horizon_days=test_horizon_days,
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        direction_accuracy_pct=round(direction_acc, 1),
        actual_ending_balance=round(actual_ending_bal, 2),
        projected_ending_balance=round(pred_ending_bal, 2),
        balance_error=round(bal_error, 2),
        actual_crunch_occurred=actual_crunch,
        predicted_crunch_occurred=predicted_crunch,
        is_false_alarm=false_alarm,
        is_missed_alarm=missed_alarm,
        method_used=forecast_res.method_used,
        status="EVALUATED",
        notes=notes,
    )
