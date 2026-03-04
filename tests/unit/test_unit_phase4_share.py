import pandas as pd
import pytest

from src.share_engine import (
    ShareConfig,
    apply_share_settlement,
    redistribute_clinic_pool_by_base_amount,
)


def _base_row(year_quarter: str) -> dict[str, object]:
    return {
        "ship_id": "S1",
        "ship_date": "2025-01-01",
        "year_month": "2025-01",
        "year_quarter": year_quarter,
        "year": 2025,
        "territory_code": "T01",
        "brand": "brand_a",
        "amount_ship": 1000.0,
        "amount_pre_share": 1000.0,
        "qty": 10,
        "pharmacy_uid": "P000001",
    }


@pytest.mark.unit
def test_share_direct_rule_applies_and_sets_audit_columns():
    base = pd.DataFrame([_base_row("2025-Q1")])
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.6,
                "ratio_clinic": 0.4,
                "version": "v1",
                "status": "confirmed",
            }
        ]
    )
    out = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=False))
    r = out.iloc[0]
    assert r["share_rule_source"] == "direct"
    assert r["share_applied_flag"] == True
    assert r["share_rule_version"] == "v1"
    assert r["overlap_generated_flag"] == False
    assert abs(r["amount_post_share"] - 1000.0) < 1e-6


@pytest.mark.unit
def test_share_extended_rule_when_current_quarter_missing():
    base = pd.DataFrame([_base_row("2025-Q2")])
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.7,
                "ratio_clinic": 0.3,
                "version": "v_prev",
                "status": "confirmed",
            }
        ]
    )
    out = apply_share_settlement(base, rules)
    r = out.iloc[0]
    assert r["share_rule_source"] == "extended"
    assert r["share_rule_version"] == "v_prev"
    assert r["share_applied_flag"] == True


@pytest.mark.unit
def test_share_none_when_no_rule_found():
    base = pd.DataFrame([_base_row("2025-Q1")])
    rules = pd.DataFrame(
        columns=[
            "year_quarter",
            "territory_code",
            "brand",
            "ratio_hosp",
            "ratio_clinic",
            "version",
            "status",
        ]
    )
    out = apply_share_settlement(base, rules)
    r = out.iloc[0]
    assert r["share_rule_source"] == "none"
    assert r["share_applied_flag"] == False
    assert pd.isna(r["share_rule_version"])


@pytest.mark.unit
def test_redistribute_clinic_pool_by_base_amount():
    base = pd.DataFrame(
        [
            {"rep_id": "RC001", "base_amount": 100.0},
            {"rep_id": "RC002", "base_amount": 300.0},
        ]
    )
    out = redistribute_clinic_pool_by_base_amount(base, clinic_pool_amount=400.0)
    by_id = {r["rep_id"]: r["allocated_amount"] for _, r in out.iterrows()}
    assert by_id["RC001"] == 100.0
    assert by_id["RC002"] == 300.0


@pytest.mark.unit
def test_redistribute_returns_empty_when_participants_missing():
    base = pd.DataFrame(columns=["rep_id", "base_amount"])
    out = redistribute_clinic_pool_by_base_amount(base, clinic_pool_amount=400.0)
    assert out.empty
