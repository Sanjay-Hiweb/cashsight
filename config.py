"""CashSight Configuration Module.

Centralizes non-secret application settings, constants, and safe development defaults.
Follows docs/ARCHITECTURE.md, docs/PRD.md, and docs/RULES.md.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample_data"
DEFAULT_DB_PATH = BASE_DIR / "storage" / "cashsight.db"

# Product Scope & Constants [FROM BRIEF]
PRODUCT_NAME = "CashSight"
PRODUCT_TAGLINE = "Know 2 weeks ahead if you will run short of cash, and what to do about it."
FORECAST_HORIZON_DAYS = 14
DEFAULT_SAFETY_CUSHION = 25000.0  # In INR
FREE_TRIAL_DAYS = 30

# Pricing Hypotheses [TO VERIFY with shop owners per PRD]
PROVISIONAL_MONTHLY_PRICE_INR = 499
PROVISIONAL_ANNUAL_PRICE_INR = 4999

# Supported Transaction Categories [FROM BRIEF]
APPROVED_CATEGORIES = [
    "rent",
    "supplier",
    "salary",
    "sales",
    "utilities",
    "other",
]

# Supported Transaction Types [FROM BRIEF]
TRANSACTION_TYPE_INFLOW = "inflow"
TRANSACTION_TYPE_OUTFLOW = "outflow"
APPROVED_TRANSACTION_TYPES = [
    TRANSACTION_TYPE_INFLOW,
    TRANSACTION_TYPE_OUTFLOW,
]

# Supported Languages for Onboarding [FROM BRIEF]
SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "hi", "label": "Hindi (हिंदी)"},
    {"code": "ta", "label": "Tamil (தமிழ்)"},
    {"code": "te", "label": "Telugu (తెలుగు)"},
    {"code": "kn", "label": "Kannada (ಕನ್ನಡ)"},
    {"code": "pa", "label": "Punjabi (ਪੰਜਾਬੀ)"},
]

# Business Types for Onboarding [FROM BRIEF]
SUPPORTED_BUSINESS_TYPES = [
    "Kirana / Grocery",
    "Clothing / Apparel",
    "Hardware / Electrical",
    "Wholesale / Trading",
    "Other Retail",
]

# Risk / Crunch Severity Levels [DEC-005 Provisional]
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# CSV Ingestion Contract Defaults [DEC-003]
CSV_REQUIRED_COLUMNS = ["date", "description", "amount", "type"]
CSV_OPTIONAL_COLUMNS = ["category"]
MAX_CSV_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB safety limit
SUPPORTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
]

# Minimum transaction history recommended for reliable forecasting (in days)
MIN_RECOMMENDED_HISTORY_DAYS = 60
MIN_ABSOLUTE_HISTORY_DAYS = 14


@dataclass
class AppConfig:
    """Application runtime configuration."""
    db_path: Path = field(default_factory=lambda: Path(os.getenv("CASHSIGHT_DB_PATH", str(DEFAULT_DB_PATH))))
    env: str = field(default_factory=lambda: os.getenv("CASHSIGHT_ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("CASHSIGHT_DEBUG", "false").lower() == "true")
    default_safety_cushion: float = DEFAULT_SAFETY_CUSHION
    forecast_horizon_days: int = FORECAST_HORIZON_DAYS


config = AppConfig()
