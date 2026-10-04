"""CashSight Data Loader Module.

Provides functions to load, aggregate, and inspect transaction datasets for
the forecasting and risk engines.
Follows docs/ARCHITECTURE.md section 5.3 and docs/PRD.md.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import sys
import datetime
import pandas as pd

# Ensure cashsight root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    SAMPLE_DATA_DIR,
    TRANSACTION_TYPE_INFLOW,
    TRANSACTION_TYPE_OUTFLOW,
    MIN_RECOMMENDED_HISTORY_DAYS,
    MIN_ABSOLUTE_HISTORY_DAYS,
)
from data.generate_sample_data import generate_retail_shop_data, save_sample_data_file


def load_sample_transactions(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads sample transactions from disk, generating them if they do not yet exist."""
    path = csv_path or (SAMPLE_DATA_DIR / "sample_transactions.csv")
    if not path.is_file():
        save_sample_data_file(path)

    df = pd.read_csv(path)
    return df


def aggregate_daily_net_cash_flow(df_transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregates individual canonical transactions into daily net cash-flow records.

    Input DataFrame schema:
        [date, description, category, type, amount]

    Output DataFrame schema:
        [ds, total_inflow, total_outflow, net_cash_flow]
        where 'ds' is datetime string YYYY-MM-DD.
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["ds", "total_inflow", "total_outflow", "net_cash_flow"])

    df = df_transactions.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Inflows and Outflows
    inflows = df[df["type"] == TRANSACTION_TYPE_INFLOW].groupby("date")["amount"].sum()
    outflows = df[df["type"] == TRANSACTION_TYPE_OUTFLOW].groupby("date")["amount"].sum()

    # Create full continuous date range to prevent gaps in time-series forecasting
    min_date = df["date"].min()
    max_date = df["date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D").strftime("%Y-%m-%d")

    daily_df = pd.DataFrame({"ds": all_dates})
    daily_df["total_inflow"] = daily_df["ds"].map(inflows).fillna(0.0).round(2)
    daily_df["total_outflow"] = daily_df["ds"].map(outflows).fillna(0.0).round(2)
    daily_df["net_cash_flow"] = (daily_df["total_inflow"] - daily_df["total_outflow"]).round(2)

    return daily_df


def inspect_transaction_dataset(df_transactions: pd.DataFrame) -> Dict[str, Any]:
    """Computes high-level statistics and data-quality checks on a transaction dataset."""
    if df_transactions.empty:
        return {
            "total_records": 0,
            "date_range": ("N/A", "N/A"),
            "days_of_history": 0,
            "total_inflow": 0.0,
            "total_outflow": 0.0,
            "net_flow": 0.0,
            "has_sufficient_history": False,
            "recommended_history_met": False,
        }

    df = df_transactions.copy()
    dates = pd.to_datetime(df["date"])
    min_date = dates.min()
    max_date = dates.max()
    days_of_history = (max_date - min_date).days + 1

    inflows = df[df["type"] == TRANSACTION_TYPE_INFLOW]["amount"].sum()
    outflows = df[df["type"] == TRANSACTION_TYPE_OUTFLOW]["amount"].sum()

    return {
        "total_records": len(df),
        "date_range": (min_date.strftime("%Y-%m-%d"), max_date.strftime("%Y-%m-%d")),
        "days_of_history": days_of_history,
        "total_inflow": round(float(inflows), 2),
        "total_outflow": round(float(outflows), 2),
        "net_flow": round(float(inflows - outflows), 2),
        "has_sufficient_history": days_of_history >= MIN_ABSOLUTE_HISTORY_DAYS,
        "recommended_history_met": days_of_history >= MIN_RECOMMENDED_HISTORY_DAYS,
    }
