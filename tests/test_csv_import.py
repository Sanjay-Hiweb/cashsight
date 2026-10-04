"""Unit tests for CSV import, validation, and auto-categorization."""

import io
import pytest
import pandas as pd
from aggregator.csv_import import (
    parse_and_validate_csv,
    auto_categorize,
    parse_amount,
    parse_date,
    generate_sample_csv_template,
)
from config import APPROVED_CATEGORIES, TRANSACTION_TYPE_INFLOW, TRANSACTION_TYPE_OUTFLOW


def test_valid_csv_parsing():
    csv_text = """date,description,amount,type,category
2026-09-01,Shop sales counter,15000,inflow,sales
2026-09-02,Wholesaler payment,25000,outflow,supplier
2026-09-05,Shop Landlord rent,18000,outflow,rent
"""
    result = parse_and_validate_csv(io.StringIO(csv_text))
    assert result.is_valid is True
    assert result.valid_rows == 3
    assert list(result.data.columns) == ["date", "description", "category", "type", "amount"]
    assert result.data["amount"].iloc[0] == 15000.0


def test_missing_required_columns():
    csv_text = "wrong_col,another_col\n1,2\n"
    result = parse_and_validate_csv(io.StringIO(csv_text))
    assert result.is_valid is False
    assert any("date" in err.lower() for err in result.errors)
    assert any("description" in err.lower() for err in result.errors)


def test_empty_csv():
    result = parse_and_validate_csv(io.StringIO(""))
    assert result.is_valid is False
    assert "empty" in result.errors[0].lower()


def test_invalid_dates_and_amounts():
    csv_text = """date,description,amount,type
bad-date,Sales,5000,inflow
2026-09-02,Sales,-100,inflow
2026-09-03,Valid,1000,inflow
"""
    result = parse_and_validate_csv(io.StringIO(csv_text))
    # Should recover the 1 valid row with warnings
    assert result.is_valid is True
    assert result.valid_rows == 1
    assert result.data["description"].iloc[0] == "Valid"


def test_debit_credit_columns_parsing():
    csv_text = """date,particulars,withdrawal,deposit
2026-09-01,UPI Sales Counter,,12000
2026-09-02,Electricity Board,4200,
"""
    result = parse_and_validate_csv(io.StringIO(csv_text))
    assert result.is_valid is True
    assert result.valid_rows == 2
    assert result.data["type"].iloc[0] == TRANSACTION_TYPE_INFLOW
    assert result.data["amount"].iloc[0] == 12000.0
    assert result.data["type"].iloc[1] == TRANSACTION_TYPE_OUTFLOW
    assert result.data["amount"].iloc[1] == 4200.0
    assert result.data["category"].iloc[1] == "utilities"


def test_auto_categorization():
    assert auto_categorize("Landlord Sharma shop kiraya", "outflow") == "rent"
    assert auto_categorize("Staff helper salary Ramesh", "outflow") == "salary"
    assert auto_categorize("Balaji FMCG Wholesalers vendor", "outflow") == "supplier"
    assert auto_categorize("MSEB power electric bill", "outflow") == "utilities"
    assert auto_categorize("Daily GPay UPI collection", "inflow") == "sales"
    assert auto_categorize("Miscellaneous donation", "outflow") == "other"


def test_duplicate_handling():
    csv_text = """date,description,amount,type
2026-09-01,Daily Sales,5000,inflow
2026-09-01,Daily Sales,5000,inflow
2026-09-02,Supplier,10000,outflow
"""
    result = parse_and_validate_csv(io.StringIO(csv_text))
    assert result.is_valid is True
    assert result.valid_rows == 2  # Deduplicated from 3 to 2
    assert any("duplicate" in w.lower() for w in result.warnings)


def test_template_generation():
    template = generate_sample_csv_template()
    assert "date,description,amount,type,category" in template
