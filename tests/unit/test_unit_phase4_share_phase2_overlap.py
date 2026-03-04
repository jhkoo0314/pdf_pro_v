import pandas as pd
import pytest

from src.share_engine import ShareConfig, apply_share_settlement


def _base_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ship_id": "S1001",
                "ship_date": "2025-01-10",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "amount_ship": 1234.56,
                "amount_pre_share": 1234.56,
                "qty": 10,
                "pharmacy_uid": "P001",
                "overlap_participant_type": "mixed",
            }
        ]
    )


def _rules() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.6,
                "ratio_clinic": 0.4,
                "version": "v1",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 50,
            },
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.8,
                "ratio_clinic": 0.2,
                "version": "v2",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 200,
            },
        ]
    )


@pytest.mark.unit
def test_overlap_group_id_is_deterministic_when_enabled():
    base = _base_rows()
    rules = _rules()

    out1 = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))
    out2 = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))

    assert out1.iloc[0]["overlap_group_id"] == out2.iloc[0]["overlap_group_id"]
    assert pd.notna(out1.iloc[0]["overlap_group_id"])
    assert out1.iloc[0]["overlap_generated_flag"] == True


@pytest.mark.unit
def test_overlap_uses_priority_rule_and_resolution_path():
    out = apply_share_settlement(_base_rows(), _rules(), config=ShareConfig(overlap_enabled=True))
    r = out.iloc[0]

    assert r["share_rule_version"] == "v2"
    assert r["share_rule_priority"] == 200
    assert r["rule_resolution_path"] == "overlap_resolved"
    assert r["rule_match_key"] == "2025-Q1|T01|brand_a|mixed"


@pytest.mark.unit
def test_rounding_correction_preserves_row_amount():
    out = apply_share_settlement(_base_rows(), _rules(), config=ShareConfig(overlap_enabled=True))
    r = out.iloc[0]

    assert abs(float(r["amount_pre_share"]) - float(r["amount_post_share"])) < 1e-6
    assert isinstance(float(r["allocation_rounding_delta"]), float)


@pytest.mark.unit
def test_mixed_participant_uses_mixed_scope_ratio_rule():
    base = _base_rows()
    base["amount_pre_share"] = 1000.0
    base["amount_ship"] = 1000.0
    base["overlap_participant_type"] = "mixed"

    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.9,
                "ratio_clinic": 0.1,
                "version": "v_scope_clinic_only",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "clinic_only",
                "priority": 999,
            },
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.7,
                "ratio_clinic": 0.3,
                "version": "v_scope_mixed",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            },
        ]
    )
    out = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))
    r = out.iloc[0]
    assert r["share_rule_version"] == "v_scope_mixed"
    assert abs(float(r["amount_hosp_share"]) - 700.0) < 1e-6
    assert abs(float(r["amount_clinic_share"]) - 300.0) < 1e-6
