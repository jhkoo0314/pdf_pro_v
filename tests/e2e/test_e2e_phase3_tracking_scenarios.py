import pandas as pd
import pytest

from src.tracking_validation import build_tracking_report


@pytest.mark.e2e
def test_tracking_e2e_normal_low_coverage_untracked_cases():
    df = pd.DataFrame(
        [
            {
                "ship_id": "normal_case",
                "ship_date": "2025-01-01",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 100.0,
                "amount_ship": 1000.0,
                "claim_qty": 100.0,
                "claim_amount": 1000.0,
            },
            {
                "ship_id": "low_coverage_case",
                "ship_date": "2025-01-01",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 50.0,
                "amount_ship": 500.0,
                "claim_qty": 100.0,
                "claim_amount": 1000.0,
            },
            {
                "ship_id": "untracked_case",
                "ship_date": "2025-01-01",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 0.0,
                "amount_ship": 0.0,
                "claim_qty": 20.0,
                "claim_amount": 300.0,
            },
        ]
    )

    out = build_tracking_report(df)
    by_id = {r["ship_id"]: r for _, r in out.iterrows()}

    assert by_id["normal_case"]["tracking_quality_flag"] == "good"
    assert by_id["normal_case"]["coverage_ratio"] == 1.0

    assert by_id["low_coverage_case"]["tracking_quality_flag"] == "poor"
    assert by_id["low_coverage_case"]["coverage_ratio"] == 0.5

    assert by_id["untracked_case"]["tracked_amount"] == 0.0
    assert by_id["untracked_case"]["gap_amount"] == 300.0
