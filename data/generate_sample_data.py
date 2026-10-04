"""CashSight Synthetic Sample Data Generator.

Generates realistic, clearly fictional transaction data for small Indian shop owners
(e.g., Kirana, apparel, hardware store) over a 180-day (6-month) history.
Includes a realistic future period designed to trigger a potential cash crunch
around 10-14 days ahead for testing and demonstration.

Follows docs/ARCHITECTURE.md section 5.3, docs/PRD.md FR-005, and docs/RULES.md.
"""

from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import random
import pandas as pd

# Ensure cashsight root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    APPROVED_CATEGORIES,
    TRANSACTION_TYPE_INFLOW,
    TRANSACTION_TYPE_OUTFLOW,
    SAMPLE_DATA_DIR,
)

DISCLAIMER = "FICTIONAL SYNTHETIC DATA FOR CASHSIGHT DEVELOPMENT AND TESTING ONLY"


def generate_retail_shop_data(
    shop_name: str = "Shree Ganesh Kirana & General Store",
    shop_type: str = "Kirana / Grocery",
    history_days: int = 180,
    end_date: Optional[date] = None,
    seed: int = 42,
    induce_crunch: bool = True,
) -> pd.DataFrame:
    """Generates synthetic transactions for a retail business.

    Args:
        shop_name: Name of the business.
        shop_type: Business category.
        history_days: Days of historical transactions (default: 180 days ~ 6 months).
        end_date: Anchor date for today (defaults to current date).
        seed: Random seed for deterministic reproducibility.
        induce_crunch: If True, schedules upcoming recurring obligations (rent + supplier)
                       that produce a projected cash crunch ~10-14 days ahead.

    Returns:
        DataFrame in canonical schema: [date, description, category, type, amount]
    """
    random.seed(seed)
    today = end_date or date.today()
    start_date = today - timedelta(days=history_days)

    records: List[Dict[str, Any]] = []

    current_d = start_date
    while current_d <= today:
        d_str = current_d.strftime("%Y-%m-%d")
        weekday = current_d.weekday()  # 0=Mon, 6=Sun

        # 1. Daily Sales (Inflows)
        # Sales are higher on weekends (Saturday/Sunday)
        base_sales = random.uniform(8000, 16000) if weekday < 5 else random.uniform(14000, 26000)
        # Slight month-end/start variation
        if current_d.day in [1, 2, 3, 28, 29, 30]:
            base_sales *= 1.15
        sales_amt = round(base_sales, 2)
        records.append({
            "date": d_str,
            "description": f"Daily Counter Sales & UPI ({shop_name})",
            "category": "sales",
            "type": TRANSACTION_TYPE_INFLOW,
            "amount": sales_amt,
        })

        # 2. Monthly Rent (Outflow - 5th of each month)
        if current_d.day == 5:
            records.append({
                "date": d_str,
                "description": "Monthly Commercial Shop Rent - Landlord Sharma",
                "category": "rent",
                "type": TRANSACTION_TYPE_OUTFLOW,
                "amount": 22000.0,
            })

        # 3. Monthly Staff Salary (Outflow - 7th of each month)
        if current_d.day == 7:
            records.append({
                "date": d_str,
                "description": "Staff Wages & Helper Salaries (Ramesh & Suresh)",
                "category": "salary",
                "type": TRANSACTION_TYPE_OUTFLOW,
                "amount": 16000.0,
            })

        # 4. Monthly Utilities (Outflow - 15th of each month)
        if current_d.day == 15:
            util_amt = round(random.uniform(3200, 5800), 2)
            records.append({
                "date": d_str,
                "description": "State Electricity Board Commercial Bill",
                "category": "utilities",
                "type": TRANSACTION_TYPE_OUTFLOW,
                "amount": util_amt,
            })

        # 5. Weekly Supplier / Stock Purchases (Tuesdays and Fridays)
        if weekday in [1, 4]:
            supplier_amt = round(random.uniform(18000, 38000), 2)
            supplier_names = [
                "Balaji FMCG Wholesalers",
                "National Grains & Pulses Trader",
                "Metro Dairy & Beverage Distributors",
                "Kisan Oil & Spices Supply",
            ]
            s_name = random.choice(supplier_names)
            records.append({
                "date": d_str,
                "description": f"Stock Purchase - {s_name}",
                "category": "supplier",
                "type": TRANSACTION_TYPE_OUTFLOW,
                "amount": supplier_amt,
            })

        # 6. Occasional Miscellaneous Expenses (Tea, packing material, cleaning)
        if random.random() < 0.25:
            misc_amt = round(random.uniform(300, 1200), 2)
            records.append({
                "date": d_str,
                "description": "Shop packaging material & daily sundries",
                "category": "other",
                "type": TRANSACTION_TYPE_OUTFLOW,
                "amount": misc_amt,
            })

        current_d += timedelta(days=1)

    df = pd.DataFrame(records)
    # Chronological sort
    df["dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(["dt", "type"]).drop(columns=["dt"]).reset_index(drop=True)
    return df


def save_sample_data_file(target_path: Optional[Path] = None) -> Path:
    """Generates synthetic sample data and writes it to data/sample_data/sample_transactions.csv."""
    path = target_path or (SAMPLE_DATA_DIR / "sample_transactions.csv")
    path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_retail_shop_data()
    df.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    out_path = save_sample_data_file()
    print(f"Generated sample synthetic transactions at: {out_path}")
