"""CashSight What-If Simulator Module.

Allows shop owners to simulate the impact of delaying a specific upcoming or
recurring outflow payment (e.g., supplier payment, rent) by N days.
Produces a side-by-side comparison with the baseline forecast.

Follows docs/ARCHITECTURE.md section 5.9 and docs/PRD.md FR-011.
CRITICAL CONSTRAINT: Never alters the original transaction history or persistent records.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import datetime
import pandas as pd

from config import (
    DEFAULT_SAFETY_CUSHION,
    TRANSACTION_TYPE_OUTFLOW,
)
from data.data_loader import aggregate_daily_net_cash_flow
from core.forecasting import forecast_cash_balance, ForecastResult
from core.risk_engine import detect_cash_crunches, RiskEvaluation


@dataclass
class WhatIfComparison:
    """Side-by-side comparison between baseline and simulated scenario."""
    payment_description: str
    original_date: str
    simulated_date: str
    delay_days: int
    amount: float
    baseline_forecast: ForecastResult
    simulated_forecast: ForecastResult
    baseline_risk: RiskEvaluation
    simulated_risk: RiskEvaluation
    shortfall_difference: float      # Positive means shortfall reduced
    crunch_delayed_by_days: int     # How many days further out the crunch was pushed
    is_crunch_averted: bool          # True if crunch was completely resolved in 14-day window
    plain_language_summary: str      # Reassuring shopkeeper-friendly explanation


def simulate_payment_delay(
    transactions: pd.DataFrame,
    payment_index: int,
    delay_days: int,
    current_balance: float,
    safety_cushion: float = DEFAULT_SAFETY_CUSHION,
    method: str = "prophet",
) -> WhatIfComparison:
    """Simulates delaying a specific outgoing payment by N days.

    Args:
        transactions: Original canonical transaction DataFrame [date, description, category, type, amount].
                      MUST NOT be modified.
        payment_index: Integer index of the transaction row to delay.
        delay_days: Number of days to postpone the payment (1 to 30).
        current_balance: Starting verified cash balance.
        safety_cushion: Target minimum cash cushion.
        method: Forecasting engine method ('prophet' or 'statsmodels').

    Returns:
        WhatIfComparison with baseline and simulated results.
    """
    if transactions.empty:
        raise ValueError("Cannot run simulation on empty transactions dataset.")

    if payment_index < 0 or payment_index >= len(transactions):
        raise IndexError(f"Payment index {payment_index} is out of bounds (total rows: {len(transactions)}).")

    if delay_days < 0 or delay_days > 45:
        raise ValueError("Delay days must be between 0 and 45 days.")

    # 1. Isolate the target transaction from an immutable copy
    target_row = transactions.iloc[payment_index]
    if target_row["type"] != TRANSACTION_TYPE_OUTFLOW:
        raise ValueError(
            f"Cannot delay transaction '{target_row['description']}': Only outflow payments can be delayed."
        )

    # 2. Compute Baseline Outlook
    baseline_daily = aggregate_daily_net_cash_flow(transactions)
    baseline_forecast = forecast_cash_balance(baseline_daily, current_balance=current_balance, method=method)
    baseline_risk = detect_cash_crunches(baseline_forecast, safety_cushion=safety_cushion)

    # If delay is 0, simulated is identical to baseline
    if delay_days == 0:
        return WhatIfComparison(
            payment_description=str(target_row["description"]),
            original_date=str(target_row["date"]),
            simulated_date=str(target_row["date"]),
            delay_days=0,
            amount=float(target_row["amount"]),
            baseline_forecast=baseline_forecast,
            simulated_forecast=baseline_forecast,
            baseline_risk=baseline_risk,
            simulated_risk=baseline_risk,
            shortfall_difference=0.0,
            crunch_delayed_by_days=0,
            is_crunch_averted=False,
            plain_language_summary="No delay was applied. Forecast remains identical to the baseline.",
        )

    # 3. Create Simulation Copy (STRICTLY NON-MUTATING)
    sim_df = transactions.copy(deep=True)

    # Calculate new simulated date
    orig_date = pd.to_datetime(target_row["date"]).date()
    new_date = orig_date + datetime.timedelta(days=delay_days)
    new_date_str = new_date.strftime("%Y-%m-%d")

    # Update ONLY the simulation copy
    sim_df.at[payment_index, "date"] = new_date_str

    # 4. Compute Simulated Outlook
    sim_daily = aggregate_daily_net_cash_flow(sim_df)
    sim_forecast = forecast_cash_balance(sim_daily, current_balance=current_balance, method=method)
    sim_risk = detect_cash_crunches(sim_forecast, safety_cushion=safety_cushion)

    # 5. Measure differences
    orig_shortfall = baseline_risk.worst_crunch.shortfall if baseline_risk.worst_crunch else 0.0
    sim_shortfall = sim_risk.worst_crunch.shortfall if sim_risk.worst_crunch else 0.0
    shortfall_diff = round(orig_shortfall - sim_shortfall, 2)

    is_averted = baseline_risk.has_crunch and not sim_risk.has_crunch

    # Calculate crunch postponement
    delayed_by = 0
    if baseline_risk.earliest_crunch and sim_risk.earliest_crunch:
        delayed_by = max(0, sim_risk.earliest_crunch.days_away - baseline_risk.earliest_crunch.days_away)
    elif baseline_risk.has_crunch and not sim_risk.has_crunch:
        delayed_by = 14  # Pushed beyond current 14-day horizon

    # Build plain language summary
    amt_fmt = f"₹{float(target_row['amount']):,.0f}"
    desc = target_row["description"]
    if is_averted:
        summary = (
            f"Good news: Delaying '{desc}' ({amt_fmt}) by {delay_days} days completely prevents your "
            f"projected cash crunch over the next 14 days! Your balance stays above the ₹{safety_cushion:,.0f} cushion."
        )
    elif delayed_by > 0:
        summary = (
            f"Delaying '{desc}' ({amt_fmt}) by {delay_days} days pushes your cash shortage from Day "
            f"{baseline_risk.earliest_crunch.days_away} to Day {sim_risk.earliest_crunch.days_away} "
            f"(buying {delayed_by} extra days to collect sales revenue)."
        )
    else:
        summary = (
            f"Delaying '{desc}' ({amt_fmt}) by {delay_days} days changes the timing of cash outflow, "
            f"reducing peak shortfall by ₹{max(0.0, shortfall_diff):,.0f}."
        )

    return WhatIfComparison(
        payment_description=str(target_row["description"]),
        original_date=str(target_row["date"]),
        simulated_date=new_date_str,
        delay_days=delay_days,
        amount=float(target_row["amount"]),
        baseline_forecast=baseline_forecast,
        simulated_forecast=sim_forecast,
        baseline_risk=baseline_risk,
        simulated_risk=sim_risk,
        shortfall_difference=shortfall_diff,
        crunch_delayed_by_days=delayed_by,
        is_crunch_averted=is_averted,
        plain_language_summary=summary,
    )
