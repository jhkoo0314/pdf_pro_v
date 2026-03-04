import pytest
import pandas as pd

from src.contracts import (
    REQUIRED_AUDIT_COLUMNS,
    REQUIRED_CORE_COLUMNS,
    validate_required_columns,
)


@pytest.mark.contract
def test_required_core_columns_contract():
    cols = list(REQUIRED_CORE_COLUMNS) + ["extra_col"]
    result = validate_required_columns(cols, REQUIRED_CORE_COLUMNS)
    assert result.ok


@pytest.mark.contract
def test_required_audit_columns_contract():
    cols = list(REQUIRED_AUDIT_COLUMNS)
    result = validate_required_columns(cols, REQUIRED_AUDIT_COLUMNS)
    assert result.ok


@pytest.mark.contract
def test_missing_required_columns_fails():
    cols = ["ship_date", "year_month"]
    result = validate_required_columns(cols, REQUIRED_CORE_COLUMNS)
    assert not result.ok
    assert "year_quarter" in result.missing


@pytest.mark.contract
def test_core_column_types_and_non_nullable_contract():
    row = {
        "ship_date": "2026-01-01",
        "year_month": "2026-01",
        "year_quarter": "2026-Q1",
        "year": 2026,
        "amount_ship": 1000.0,
        "amount_supply": 900.0,
        "amount_pre_share": 1000.0,
        "amount_post_share": 1000.0,
        "qty": 10,
        "brand": "BrandA",
        "territory_code": "T01",
        "pharmacy_uid": "P001",
        "share_applied_flag": True,
        "share_rule_version": "v1",
        "share_rule_source": "direct",
    }
    df = pd.DataFrame([row])

    required = list(REQUIRED_CORE_COLUMNS) + list(REQUIRED_AUDIT_COLUMNS)
    assert df[required].isna().sum().sum() == 0

    assert pd.api.types.is_integer_dtype(df["year"])
    assert pd.api.types.is_integer_dtype(df["qty"])
    assert pd.api.types.is_numeric_dtype(df["amount_ship"])
    assert pd.api.types.is_numeric_dtype(df["amount_supply"])
    assert pd.api.types.is_numeric_dtype(df["amount_pre_share"])
    assert pd.api.types.is_numeric_dtype(df["amount_post_share"])
    assert pd.api.types.is_bool_dtype(df["share_applied_flag"])


@pytest.mark.contract
def test_non_nullable_contract_fails_when_null_exists():
    row = {
        "ship_date": "2026-01-01",
        "year_month": "2026-01",
        "year_quarter": "2026-Q1",
        "year": 2026,
        "amount_ship": 1000.0,
        "amount_supply": 900.0,
        "amount_pre_share": 1000.0,
        "amount_post_share": 1000.0,
        "qty": 10,
        "brand": "BrandA",
        "territory_code": "T01",
        "pharmacy_uid": None,
        "share_applied_flag": True,
        "share_rule_version": "v1",
        "share_rule_source": "direct",
    }
    df = pd.DataFrame([row])
    required = list(REQUIRED_CORE_COLUMNS) + list(REQUIRED_AUDIT_COLUMNS)
    assert df[required].isna().sum().sum() > 0
