"""CashSight CSV Import & Validation Module.

Validates and normalizes tabular financial data (CSV/bank statements) into the
canonical CashSight transaction schema:
    [date, description, category, type, amount]
"""

from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import List, Optional, Union, TextIO, Any
import datetime
import re
import pandas as pd

from config import (
    APPROVED_CATEGORIES,
    APPROVED_TRANSACTION_TYPES,
    TRANSACTION_TYPE_INFLOW,
    TRANSACTION_TYPE_OUTFLOW,
    SUPPORTED_DATE_FORMATS,
    MAX_CSV_FILE_SIZE_BYTES,
)

# Common column name aliases used in Indian bank statements and shopkeeper spreadsheets
COLUMN_ALIASES = {
    "date": ["date", "txn_date", "transaction date", "trans date", "value date"],
    "description": ["description", "particulars", "narration", "remarks", "details", "note"],
    "amount": ["amount", "txn_amount", "transaction amount", "total", "net amount"],
    "type": ["type", "txn_type", "transaction type", "dr_cr", "cr_dr"],
    "category": ["category", "cat", "tag", "expense type"],
    "debit": ["debit", "withdrawal", "dr", "debit amount"],
    "credit": ["credit", "deposit", "cr", "credit amount"],
}

# Rule-based keyword matching for auto-categorization
CATEGORY_KEYWORD_RULES = {
    "rent": [
        "rent", "kiraya", "lease", "landlord", "shop rent", "godown rent",
    ],
    "salary": [
        "salary", "salaries", "vetan", "wages", "staff", "employee", "helper", "maid",
    ],
    "supplier": [
        "supplier", "vendor", "wholesale", "trader", "distributor", "stock", "purchase",
        "goods", "mal", "maal", "inventory", "agency", "enterprises",
    ],
    "utilities": [
        "electricity", "bijli", "water", "paani", "power", "bescom", "tneb", "mseb",
        "cesc", "internet", "wifi", "broadband", "recharge", "bill", "phone bill",
        "maintenance",
    ],
    "sales": [
        "sales", "upi", "qr", "gpay", "phonepe", "paytm", "counter", "customer",
        "pos", "cash deposit", "daily collection", "bikri",
    ],
}


@dataclass
class CSVValidationResult:
    """Represents the outcome of validating and parsing a CSV file."""
    is_valid: bool
    data: Optional[pd.DataFrame] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0


def auto_categorize(description: str, txn_type: str) -> str:
    """Categorizes a transaction based on description keywords and transaction type.

    Returns one of the approved categories:
    ['rent', 'supplier', 'salary', 'sales', 'utilities', 'other'].
    """
    if not description or not isinstance(description, str):
        return "sales" if txn_type == TRANSACTION_TYPE_INFLOW else "other"

    desc_lower = description.lower()

    for category, keywords in CATEGORY_KEYWORD_RULES.items():
        for kw in keywords:
            # Word boundary matching or substring search
            if re.search(r"\b" + re.escape(kw) + r"\b", desc_lower) or kw in desc_lower:
                return category

    # Default fallback
    if txn_type == TRANSACTION_TYPE_INFLOW:
        return "sales"
    return "other"


def parse_date(date_val: Any) -> Optional[datetime.date]:
    """Tolerantly parses a date value against approved Indian and ISO date formats."""
    if pd.isna(date_val):
        return None

    if isinstance(date_val, (datetime.date, datetime.datetime)):
        return date_val.date() if isinstance(date_val, datetime.datetime) else date_val

    date_str = str(date_val).strip()
    if not date_str:
        return None

    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Attempt pandas fallback parser
    try:
        parsed = pd.to_datetime(date_str, dayfirst=True)
        return parsed.date()
    except Exception:
        return None


def parse_amount(val: Any) -> Optional[float]:
    """Parses a numerical amount, removing commas, currency symbols, and spaces."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        amt = float(val)
        return amt if amt >= 0 else None

    val_str = str(val).strip()
    # Remove Indian Rupee symbols, commas, spaces
    cleaned = re.sub(r"[₹Rs\.\s,]", "", val_str, flags=re.IGNORECASE)
    # Re-handle decimal dot if stripped
    original_dot = "." in val_str
    if original_dot:
        # Better cleaner preserving decimal point
        cleaned = re.sub(r"[^\d.]", "", val_str)

    try:
        amt = float(cleaned)
        return amt if amt >= 0 else None
    except ValueError:
        return None


def parse_and_validate_csv(
    file_source: Union[str, Path, StringIO, TextIO],
    file_size_bytes: Optional[int] = None,
) -> CSVValidationResult:
    """Parses and validates a CSV file into canonical CashSight transactions.

    Requirements enforced:
    - Rejects empty files or oversized files (>5MB).
    - Maps column aliases to standard columns (date, description, amount, type, category).
    - Supports separate Debit / Credit column statements.
    - Rejects malformed dates and invalid non-positive amounts.
    - Applies auto-categorization to approved categories.
    - Flags duplicate records and reports warnings.
    - Never mutates amounts silently.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # File size check
    if file_size_bytes and file_size_bytes > MAX_CSV_FILE_SIZE_BYTES:
        return CSVValidationResult(
            is_valid=False,
            errors=[f"File size exceeds maximum allowed limit of {MAX_CSV_FILE_SIZE_BYTES // (1024*1024)} MB."],
        )

    # Read CSV
    try:
        if isinstance(file_source, (str, Path)) and Path(str(file_source)).is_file():
            path_obj = Path(str(file_source))
            if path_obj.stat().st_size == 0:
                return CSVValidationResult(is_valid=False, errors=["Uploaded file is empty (0 bytes)."])
            df_raw = pd.read_csv(file_source)
        elif isinstance(file_source, StringIO):
            content = file_source.getvalue()
            if not content.strip():
                return CSVValidationResult(is_valid=False, errors=["Uploaded file is empty."])
            df_raw = pd.read_csv(file_source)
        else:
            df_raw = pd.read_csv(file_source)
    except Exception as e:
        return CSVValidationResult(is_valid=False, errors=[f"Failed to read CSV file: {str(e)}"])

    if df_raw.empty:
        return CSVValidationResult(is_valid=False, errors=["CSV file contains no data rows."])

    # Normalize header column names
    col_map = {}
    lower_to_orig = {str(c).strip().lower(): c for c in df_raw.columns}

    for target_col, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_to_orig:
                col_map[target_col] = lower_to_orig[alias]
                break

    # Check for required columns
    has_date = "date" in col_map
    has_desc = "description" in col_map
    has_direct_amount = "amount" in col_map
    has_debit_credit = "debit" in col_map and "credit" in col_map

    if not has_date:
        errors.append("Missing required date column (e.g., 'date', 'txn_date', 'transaction date').")
    if not has_desc:
        errors.append("Missing required description column (e.g., 'description', 'particulars', 'narration').")
    if not has_direct_amount and not has_debit_credit:
        errors.append("Missing required amount columns (either 'amount' or both 'debit' and 'credit').")

    if errors:
        return CSVValidationResult(is_valid=False, errors=errors, total_rows=len(df_raw))

    # Process rows into canonical records
    records = []
    for idx, row in df_raw.iterrows():
        row_num = idx + 2  # 1-indexed header + row

        # Parse Date
        raw_date = row[col_map["date"]]
        parsed_d = parse_date(raw_date)
        if not parsed_d:
            errors.append(f"Row {row_num}: Invalid or unrecognized date '{raw_date}'.")
            continue

        # Parse Description
        raw_desc = str(row[col_map["description"]]).strip() if pd.notna(row[col_map["description"]]) else ""
        if not raw_desc:
            raw_desc = "Unspecified Transaction"

        # Determine Amount and Type
        amount = 0.0
        txn_type = ""

        if has_debit_credit:
            debit_val = parse_amount(row[col_map["debit"]])
            credit_val = parse_amount(row[col_map["credit"]])

            if debit_val and debit_val > 0:
                amount = debit_val
                txn_type = TRANSACTION_TYPE_OUTFLOW
            elif credit_val and credit_val > 0:
                amount = credit_val
                txn_type = TRANSACTION_TYPE_INFLOW
            else:
                errors.append(f"Row {row_num}: Neither valid debit nor credit amount found.")
                continue
        else:
            raw_amount = row[col_map["amount"]]
            amt_parsed = parse_amount(raw_amount)
            if amt_parsed is None or amt_parsed <= 0:
                errors.append(f"Row {row_num}: Invalid or non-positive amount '{raw_amount}'.")
                continue
            amount = amt_parsed

            # Parse Type if present
            if "type" in col_map and pd.notna(row[col_map["type"]]):
                raw_type = str(row[col_map["type"]]).strip().lower()
                if raw_type in ["inflow", "credit", "cr", "income", "deposit", "+"]:
                    txn_type = TRANSACTION_TYPE_INFLOW
                elif raw_type in ["outflow", "debit", "dr", "expense", "withdrawal", "-"]:
                    txn_type = TRANSACTION_TYPE_OUTFLOW
                else:
                    errors.append(f"Row {row_num}: Unknown transaction type '{raw_type}'. Must be 'inflow' or 'outflow'.")
                    continue
            else:
                # If negative sign was present in original raw amount
                if isinstance(raw_amount, (int, float)) and raw_amount < 0:
                    txn_type = TRANSACTION_TYPE_OUTFLOW
                    amount = abs(raw_amount)
                elif isinstance(raw_amount, str) and "-" in raw_amount:
                    txn_type = TRANSACTION_TYPE_OUTFLOW
                else:
                    # Default: outflow for expenses, but prompt user warning
                    txn_type = TRANSACTION_TYPE_OUTFLOW
                    warnings.append(f"Row {row_num}: Transaction type not specified; defaulted to 'outflow'.")

        # Category
        category = "other"
        if "category" in col_map and pd.notna(row[col_map["category"]]):
            raw_cat = str(row[col_map["category"]]).strip().lower()
            if raw_cat in APPROVED_CATEGORIES:
                category = raw_cat
            else:
                category = auto_categorize(raw_desc, txn_type)
        else:
            category = auto_categorize(raw_desc, txn_type)

        records.append({
            "date": parsed_d.strftime("%Y-%m-%d"),
            "description": raw_desc,
            "category": category,
            "type": txn_type,
            "amount": round(float(amount), 2),
        })

    if not records:
        return CSVValidationResult(
            is_valid=False,
            errors=errors or ["No valid transaction records could be extracted."],
            total_rows=len(df_raw),
            valid_rows=0,
        )

    df_clean = pd.DataFrame(records)

    # Duplicate detection
    duplicate_mask = df_clean.duplicated(subset=["date", "description", "amount", "type"], keep="first")
    duplicate_count = int(duplicate_mask.sum())
    if duplicate_count > 0:
        warnings.append(f"{duplicate_count} duplicate transaction(s) detected and deduplicated.")
        df_clean = df_clean[~duplicate_mask].reset_index(drop=True)

    # Sort chronologically
    df_clean["date_dt"] = pd.to_datetime(df_clean["date"])
    df_clean = df_clean.sort_values("date_dt").drop(columns=["date_dt"]).reset_index(drop=True)

    # If there were partial row errors, record as warnings if we have good rows, or fail if high ratio
    if errors and len(df_clean) > 0:
        warnings.extend([f"Skipped {len(errors)} invalid row(s) due to errors."] + errors[:5])
        errors = []  # Partial valid recovery allowed with warnings

    return CSVValidationResult(
        is_valid=True,
        data=df_clean,
        errors=[],
        warnings=warnings,
        total_rows=len(df_raw),
        valid_rows=len(df_clean),
    )


def generate_sample_csv_template() -> str:
    """Returns a sample CSV template adhering to the approved contract."""
    return (
        "date,description,amount,type,category\n"
        "2026-09-01,Daily Shop Sales,14500,inflow,sales\n"
        "2026-09-02,Kirana Wholesaler Supplier,22000,outflow,supplier\n"
        "2026-09-05,Shop Electricity Bill,3400,outflow,utilities\n"
        "2026-09-10,Shop Helper Salary,12000,outflow,salary\n"
        "2026-09-15,Commercial Shop Rent,18000,outflow,rent\n"
    )
