import pandas as pd
import pytest

from src.share_engine import apply_share_settlement


@pytest.mark.regression
def test_share_amount_conservation_sum_pre_equals_sum_post():
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
                "ship_date": "2025-01-02",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "amount_ship": 2000.0,
                "amount_pre_share": 2000.0,
                "qty": 20,
            },
        ]
    )
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.55,
                "ratio_clinic": 0.45,
                "version": "v1",
                "status": "confirmed",
            }
        ]
    )

    out = apply_share_settlement(base, rules)
    assert abs(float(out["amount_pre_share"].sum()) - float(out["amount_post_share"].sum())) < 1e-6
