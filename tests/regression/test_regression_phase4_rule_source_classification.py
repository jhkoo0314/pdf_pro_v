import pandas as pd
import pytest

from src.share_engine import apply_share_settlement


@pytest.mark.regression
def test_rule_source_classification_is_direct_extended_none_only():
    base = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "ship_date": "2025-01-01",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "amount_ship": 1000.0,
                "amount_pre_share": 1000.0,
                "qty": 10,
            },
            {
                "ship_id": "S2",
                "ship_date": "2025-04-01",
                "year_month": "2025-04",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "amount_ship": 2000.0,
                "amount_pre_share": 2000.0,
                "qty": 20,
            },
            {
                "ship_id": "S3",
                "ship_date": "2025-04-01",
                "year_month": "2025-04",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T99",
                "brand": "brand_z",
                "amount_ship": 500.0,
                "amount_pre_share": 500.0,
                "qty": 5,
            },
        ]
    )
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.5,
                "ratio_clinic": 0.5,
                "version": "v1",
                "status": "confirmed",
            }
        ]
    )

    out = apply_share_settlement(base, rules)
    by_id = {r["ship_id"]: r["share_rule_source"] for _, r in out.iterrows()}

    assert by_id["S1"] == "direct"
    assert by_id["S2"] == "extended"
    assert by_id["S3"] == "none"
    assert set(out["share_rule_source"].unique()).issubset({"direct", "extended", "none"})
