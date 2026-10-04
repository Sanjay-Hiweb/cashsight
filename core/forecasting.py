"""CashSight Core Forecasting Engine.

Implements the 14-day cash-flow forecasting algorithms:
1. Primary method: Prophet (weekly seasonality enabled, yearly seasonality disabled).
2. Fallback method: statsmodels Holt-Winters Exponential Smoothing.
3. Graceful baseline fallback when history is sparse.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import datetime
import numpy as np
import pandas as pd

from config import (
    FORECAST_HORIZON_DAYS,
    MIN_ABSOLUTE_HISTORY_DAYS,
    MIN_RECOMMENDED_HISTORY_DAYS,
)


class InsufficientHistoryError(ValueError):
    """Raised when the historical transaction record is too short to produce a forecast."""
    pass


class ForecastingModelError(RuntimeError):
    """Raised when a forecasting model encounters an irrecoverable calculation error."""
    pass


@dataclass
class ForecastResult:
    """Encapsulates the structured output of a cash-flow forecast."""
    forecast_df: pd.DataFrame
    method_used: str
    current_balance: float
    horizon_days: int
    history_days: int
    warning_notes: list[str]


def _prepare_history_series(
    historical_net_cash_flow: pd.DataFrame,
) -> pd.DataFrame:
    """Validates and prepares the historical daily net cash-flow DataFrame.

    Ensures continuous daily frequency with 'ds' and 'y' columns.
    """
    if historical_net_cash_flow.empty:
        raise InsufficientHistoryError("Historical cash flow data is empty.")

    df = historical_net_cash_flow.copy()

    # Identify date column
    if "ds" in df.columns:
        date_col = "ds"
    elif "date" in df.columns:
        date_col = "date"
    else:
        raise ValueError("DataFrame must contain 'ds' or 'date' column.")

    # Identify target column
    if "y" in df.columns:
        val_col = "y"
    elif "net_cash_flow" in df.columns:
        val_col = "net_cash_flow"
    elif "amount" in df.columns:
        val_col = "amount"
    else:
        raise ValueError("DataFrame must contain 'y' or 'net_cash_flow' column.")

    df["ds"] = pd.to_datetime(df[date_col])
    df["y"] = pd.to_numeric(df[val_col], errors="coerce").fillna(0.0)

    # Aggregate by day in case multiple rows exist per day
    df_daily = df.groupby("ds")["y"].sum().reset_index()

    # Check minimum history
    min_date = df_daily["ds"].min()
    max_date = df_daily["ds"].max()
    span_days = (max_date - min_date).days + 1

    if span_days < MIN_ABSOLUTE_HISTORY_DAYS:
        raise InsufficientHistoryError(
            f"At least {MIN_ABSOLUTE_HISTORY_DAYS} days of history required. Provided data covers {span_days} days."
        )

    # Reindex over full continuous daily date range to fill any missing days with 0.0
    full_range = pd.date_range(start=min_date, end=max_date, freq="D")
    df_reindexed = df_daily.set_index("ds").reindex(full_range, fill_value=0.0).reset_index()
    df_reindexed.rename(columns={"index": "ds"}, inplace=True)
    return df_reindexed


def _forecast_with_prophet(
    df_clean: pd.DataFrame,
    horizon_days: int,
) -> Tuple[pd.DataFrame, str]:
    """Forecasts using Prophet with weekly seasonality and disabled yearly seasonality."""
    try:
        from prophet import Prophet
    except ImportError as e:
        raise ForecastingModelError(f"Prophet is not installed: {e}")

    # Build model per brief: weekly seasonality enabled, yearly seasonality disabled
    model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=False,
        daily_seasonality=False,
        interval_width=0.80,  # 80% uncertainty interval
    )

    model.fit(df_clean[["ds", "y"]])
    future = model.make_future_dataframe(periods=horizon_days, freq="D", include_history=False)
    forecast = model.predict(future)

    # Output columns: ds, yhat, yhat_lower, yhat_upper
    out_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    out_df["ds"] = out_df["ds"].dt.strftime("%Y-%m-%d")
    return out_df, "prophet"


def _forecast_with_statsmodels(
    df_clean: pd.DataFrame,
    horizon_days: int,
) -> Tuple[pd.DataFrame, str]:
    """Forecasts using statsmodels Holt-Winters Exponential Smoothing with 7-day seasonality."""
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
    except ImportError as e:
        raise ForecastingModelError(f"statsmodels is not installed: {e}")

    series = df_clean["y"].values
    n = len(series)

    # Fallback to simple moving average if history is less than 14 days
    if n < 14:
        raise ForecastingModelError("Insufficient points for Holt-Winters seasonal fit.")

    try:
        # Use additive trend and weekly seasonality (period=7)
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        ).fit()
        predictions = model.forecast(horizon_days)
    except Exception:
        # Fallback to non-seasonal Holt-Winters if seasonal decomposition fails
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        ).fit()
        predictions = model.forecast(horizon_days)

    # Calculate empirical residual standard deviation for uncertainty bounds
    residuals = series - model.fittedvalues
    std_resid = float(np.std(residuals)) if len(residuals) > 0 else float(np.std(series) * 0.2)
    if std_resid <= 0.0:
        std_resid = max(float(np.mean(np.abs(series)) * 0.15), 100.0)

    # Generate future dates
    last_date = df_clean["ds"].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")

    yhat = np.array(predictions)
    # 80% interval ~ 1.28 * std
    z = 1.28
    yhat_lower = yhat - z * std_resid
    yhat_upper = yhat + z * std_resid

    out_df = pd.DataFrame({
        "ds": future_dates.strftime("%Y-%m-%d"),
        "yhat": yhat,
        "yhat_lower": yhat_lower,
        "yhat_upper": yhat_upper,
    })
    return out_df, "statsmodels_exponential_smoothing"


def _forecast_with_baseline(
    df_clean: pd.DataFrame,
    horizon_days: int,
) -> Tuple[pd.DataFrame, str]:
    """Deterministic moving-average + weekday seasonal baseline when advanced models are unavailable."""
    series = df_clean.copy()
    series["weekday"] = series["ds"].dt.weekday

    # Mean by day of the week
    weekday_means = series.groupby("weekday")["y"].mean().to_dict()
    overall_mean = series["y"].mean()
    overall_std = series["y"].std()
    if pd.isna(overall_std) or overall_std <= 0:
        overall_std = max(abs(overall_mean) * 0.2, 500.0)

    last_date = series["ds"].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")

    records = []
    z = 1.28
    for dt in future_dates:
        w = dt.weekday()
        val = weekday_means.get(w, overall_mean)
        records.append({
            "ds": dt.strftime("%Y-%m-%d"),
            "yhat": float(val),
            "yhat_lower": float(val - z * overall_std),
            "yhat_upper": float(val + z * overall_std),
        })

    return pd.DataFrame(records), "weekday_seasonal_baseline"


def forecast_cash_balance(
    historical_net_cash_flow: pd.DataFrame,
    current_balance: float,
    horizon_days: int = FORECAST_HORIZON_DAYS,
    method: str = "prophet",
) -> ForecastResult:
    """Generates a 14-day cash-balance forecast with uncertainty bounds.

    Parameters:
    - historical_net_cash_flow: DataFrame with [ds, net_cash_flow] or [date, amount, type]
    - current_balance: Starting verified cash balance in INR
    - horizon_days: Forecast horizon (default 14 days)
    - method: 'prophet' or 'statsmodels'

    Returns:
        ForecastResult with structured forecast_df containing:
        [ds, yhat, yhat_lower, yhat_upper, projected_balance,
         projected_balance_lower, projected_balance_upper]
    """
    warning_notes: list[str] = []
    df_clean = _prepare_history_series(historical_net_cash_flow)
    history_days = len(df_clean)

    if history_days < MIN_RECOMMENDED_HISTORY_DAYS:
        warning_notes.append(
            f"History contains {history_days} days, which is less than the recommended {MIN_RECOMMENDED_HISTORY_DAYS} days. "
            "Forecast uncertainty is higher."
        )

    out_df: Optional[pd.DataFrame] = None
    used_method: str = ""

    # Attempt primary method
    if method == "prophet":
        try:
            out_df, used_method = _forecast_with_prophet(df_clean, horizon_days)
        except Exception as e:
            warning_notes.append(f"Primary model (Prophet) was unavailable ({e}); activated statsmodels fallback.")
            try:
                out_df, used_method = _forecast_with_statsmodels(df_clean, horizon_days)
            except Exception as e2:
                warning_notes.append(f"statsmodels fallback failed ({e2}); using statistical weekday baseline.")
                out_df, used_method = _forecast_with_baseline(df_clean, horizon_days)
    elif method == "statsmodels":
        try:
            out_df, used_method = _forecast_with_statsmodels(df_clean, horizon_days)
        except Exception as e:
            warning_notes.append(f"statsmodels failed ({e}); using statistical weekday baseline.")
            out_df, used_method = _forecast_with_baseline(df_clean, horizon_days)
    else:
        out_df, used_method = _forecast_with_baseline(df_clean, horizon_days)

    # Convert predicted net cash flow into projected daily balances
    # Day t balance = current_balance + cumsum(yhat_1 ... yhat_t)
    out_df["projected_balance"] = (current_balance + out_df["yhat"].cumsum()).round(2)
    # Conservative lower bound: cumsum of conservative daily estimates
    out_df["projected_balance_lower"] = (current_balance + out_df["yhat_lower"].cumsum()).round(2)
    # Optimistic upper bound: cumsum of upper daily estimates
    out_df["projected_balance_upper"] = (current_balance + out_df["yhat_upper"].cumsum()).round(2)

    # Round net flow columns
    out_df["yhat"] = out_df["yhat"].round(2)
    out_df["yhat_lower"] = out_df["yhat_lower"].round(2)
    out_df["yhat_upper"] = out_df["yhat_upper"].round(2)

    return ForecastResult(
        forecast_df=out_df,
        method_used=used_method,
        current_balance=float(current_balance),
        horizon_days=horizon_days,
        history_days=history_days,
        warning_notes=warning_notes,
    )
