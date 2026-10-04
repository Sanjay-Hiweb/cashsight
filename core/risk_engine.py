"""CashSight Cash-Crunch & Risk Detection Engine.

Compares conservative forecast projections against the user's safety cushion
to detect impending cash shortages ~14 days in advance.
Produces plain-language warnings with suggested actions.

Follows docs/ARCHITECTURE.md section 5.8, docs/PRD.md FR-008/FR-009, and docs/DESIGN.md section 5.
Independent of Streamlit UI.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
import pandas as pd

from config import (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    DEFAULT_SAFETY_CUSHION,
)


@dataclass
class CrunchResult:
    """Represents an impending cash shortfall event on a specific date."""
    crunch_date: str                 # YYYY-MM-DD
    days_away: int                   # Number of days from forecast start
    projected_balance: float         # Base expected balance
    conservative_balance: float      # Conservative lower estimate
    safety_cushion: float            # User's configured cushion
    shortfall: float                 # Shortfall below safety cushion
    is_negative_cash: bool           # True if balance drops below ₹0
    severity: str                    # 'low', 'medium', 'high', 'critical'
    title: str                       # Plain-language headline
    message: str                     # Calm, clear explanation
    suggested_action: str            # Practical, actionable next step


@dataclass
class RiskEvaluation:
    """Complete risk evaluation across the entire 14-day forecast window."""
    has_crunch: bool
    crunches: List[CrunchResult] = field(default_factory=list)
    earliest_crunch: Optional[CrunchResult] = None
    worst_crunch: Optional[CrunchResult] = None
    overall_severity: str = "none"
    headline: str = ""
    summary_message: str = ""
    recommended_action: str = ""


def _determine_severity(
    conservative_balance: float,
    safety_cushion: float,
    days_away: int,
) -> str:
    """Determines crunch severity based on balance deficit and proximity in days."""
    if conservative_balance < 0:
        return SEVERITY_CRITICAL
    if days_away <= 3:
        return SEVERITY_CRITICAL if conservative_balance < (safety_cushion * 0.5) else SEVERITY_HIGH
    if days_away <= 7:
        return SEVERITY_HIGH if conservative_balance < (safety_cushion * 0.5) else SEVERITY_MEDIUM
    if conservative_balance < (safety_cushion * 0.5):
        return SEVERITY_MEDIUM
    return SEVERITY_LOW


def _build_suggested_action(
    shortfall: float,
    days_away: int,
    is_negative: bool,
    top_upcoming_outflows: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generates a calm, practical suggested action tailored to small Indian shopkeepers."""
    fmt_shortfall = f"₹{shortfall:,.0f}"

    if is_negative and days_away <= 4:
        return (
            f"You may run out of cash by {days_away} days ({fmt_shortfall} deficit). "
            "Consider contacting your largest supplier immediately to request rescheduling their payment by 5–7 days, "
            "or deposit personal reserve cash."
        )

    if days_away <= 7:
        return (
            f"Review planned supplier payments due in the next week. "
            f"Delaying or staggering a payment by a few days could protect your safety cushion of {fmt_shortfall}."
        )

    return (
        f"You have about {days_away} days of advance notice. "
        "Review upcoming inventory restocking orders or follow up on any expected customer receivables "
        "to comfortably stay above your safety cushion."
    )


def detect_cash_crunches(
    forecast: Union[pd.DataFrame, Any],
    safety_cushion: float = DEFAULT_SAFETY_CUSHION,
    top_upcoming_outflows: Optional[List[Dict[str, Any]]] = None,
) -> RiskEvaluation:
    """Evaluates 14-day forecast against user's safety cushion.

    Public Contract (docs/ARCHITECTURE.md section 5.8):
    - forecast: DataFrame containing [ds, projected_balance, projected_balance_lower]
                or ForecastResult instance.
    - safety_cushion: Configured threshold in INR (defaults to 25,000 INR).

    Returns:
        RiskEvaluation containing structured CrunchResult objects and summary messages.
    """
    if hasattr(forecast, "forecast_df"):
        df = forecast.forecast_df.copy()
    elif isinstance(forecast, pd.DataFrame):
        df = forecast.copy()
    else:
        raise ValueError("Invalid forecast format. Expected DataFrame or ForecastResult.")

    if df.empty:
        return RiskEvaluation(
            has_crunch=False,
            headline="No forecast available",
            summary_message="Historical transaction data is insufficient to compute risk outlook.",
            recommended_action="Import transactions to enable 14-day cash-crunch forecasting.",
        )

    # Required columns
    if "ds" not in df.columns:
        raise ValueError("Forecast DataFrame must contain 'ds' date column.")

    # Determine projected balance columns
    if "projected_balance_lower" in df.columns:
        lower_col = "projected_balance_lower"
    elif "projected_balance" in df.columns:
        lower_col = "projected_balance"
    else:
        raise ValueError("Forecast DataFrame must contain 'projected_balance' or 'projected_balance_lower'.")

    base_col = "projected_balance" if "projected_balance" in df.columns else lower_col

    crunches: List[CrunchResult] = []

    for idx, row in df.iterrows():
        days_away = idx + 1
        d_str = str(row["ds"])[:10]
        base_bal = float(row[base_col])
        cons_bal = float(row[lower_col])

        # Check if conservative estimate falls below safety cushion
        if cons_bal < safety_cushion:
            shortfall = round(safety_cushion - cons_bal, 2)
            is_neg = cons_bal < 0
            severity = _determine_severity(cons_bal, safety_cushion, days_away)
            action = _build_suggested_action(shortfall, days_away, is_neg, top_upcoming_outflows)

            title = (
                f"Deficit Risk on {d_str}" if is_neg
                else f"Below Safety Cushion on {d_str}"
            )
            msg = (
                f"In {days_away} days ({d_str}), your conservative balance may drop to ₹{cons_bal:,.0f}, "
                f"which is ₹{shortfall:,.0f} below your ₹{safety_cushion:,.0f} safety cushion."
            )

            crunches.append(CrunchResult(
                crunch_date=d_str,
                days_away=days_away,
                projected_balance=base_bal,
                conservative_balance=cons_bal,
                safety_cushion=float(safety_cushion),
                shortfall=shortfall,
                is_negative_cash=is_neg,
                severity=severity,
                title=title,
                message=msg,
                suggested_action=action,
            ))

    if not crunches:
        return RiskEvaluation(
            has_crunch=False,
            crunches=[],
            overall_severity="none",
            headline="Safe Cash Position",
            summary_message=(
                f"Your estimated cash balance stays above your ₹{safety_cushion:,.0f} safety cushion "
                "throughout the next 14 days based on current patterns."
            ),
            recommended_action="Continue monitoring your cash flow normally.",
        )

    # Identify earliest and worst crunches
    earliest = crunches[0]
    worst = max(crunches, key=lambda c: c.shortfall)

    # Overall severity is the highest among crunches
    severity_order = {SEVERITY_LOW: 1, SEVERITY_MEDIUM: 2, SEVERITY_HIGH: 3, SEVERITY_CRITICAL: 4}
    highest_sev = max(crunches, key=lambda c: severity_order.get(c.severity, 0)).severity

    headline = (
        f"Possible cash shortage in {earliest.days_away} days ({earliest.crunch_date})"
        if earliest.is_negative_cash
        else f"Cash balance dipping below cushion in {earliest.days_away} days"
    )

    summary_message = (
        f"Based on historical cash-flow patterns, your balance is projected to fall below your "
        f"₹{safety_cushion:,.0f} safety cushion starting on {earliest.crunch_date} (approx. ₹{earliest.shortfall:,.0f} shortfall). "
        f"Peak shortfall reaches ₹{worst.shortfall:,.0f} on {worst.crunch_date}. This is an estimate, not a guarantee."
    )

    return RiskEvaluation(
        has_crunch=True,
        crunches=crunches,
        earliest_crunch=earliest,
        worst_crunch=worst,
        overall_severity=highest_sev,
        headline=headline,
        summary_message=summary_message,
        recommended_action=earliest.suggested_action,
    )
