import pytest

from src.contracts import (
    REQUIRED_AUDIT_COLUMNS,
    REQUIRED_CORE_COLUMNS,
    validate_share_rule_source_values,
    validate_snake_case_columns,
)


@pytest.mark.unit
def test_snake_case_columns_pass():
    cols = ["ship_date", "amount_ship", "share_rule_source"]
    result = validate_snake_case_columns(cols)
    assert result.ok


@pytest.mark.unit
def test_snake_case_columns_fail():
    cols = ["ship_date", "AmountShip", "share-rule-source"]
    result = validate_snake_case_columns(cols)
    assert not result.ok
    assert "AmountShip" in result.invalid


@pytest.mark.unit
def test_share_rule_source_values():
    result = validate_share_rule_source_values(["direct", "extended", "none"])
    assert result.ok


@pytest.mark.unit
def test_share_rule_source_values_fail():
    result = validate_share_rule_source_values(["direct", "bad"])
    assert not result.ok
    assert "bad" in result.invalid


@pytest.mark.unit
def test_canonical_columns_are_snake_case():
    canonical = list(REQUIRED_CORE_COLUMNS) + list(REQUIRED_AUDIT_COLUMNS)
    result = validate_snake_case_columns(canonical)
    assert result.ok
