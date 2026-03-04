import pandas as pd
import pytest

from src.tracking_validation import build_tracking_report


@pytest.mark.unit
def test_tracking_metrics_columns_and_bounds():
    df = pd.DataFrame(
        [
            {
                "ship_id": "S00000001",
                "ship_date": "2025-01-05",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 100,
                "amount_ship": 1000000.0,
            }
        ]
    )
    out = build_tracking_report(df)
    assert "tracked_amount" in out.columns
    assert "coverage_ratio" in out.columns
    assert "gap_ratio" in out.columns
    assert "tracking_quality_flag" in out.columns
    assert (out["coverage_ratio"] >= 0).all()
    assert (out["coverage_ratio"] <= 1).all()
