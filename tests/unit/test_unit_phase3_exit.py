import pandas as pd
import pytest

from src.tracking_validation import (
    build_tracking_report,
    build_trace_candidates,
    validate_tracking_tolerance,
)


@pytest.mark.unit
def test_coverage_gap_tolerance_within_limit():
    df = pd.DataFrame(
        [
            {
                "ship_id": "S1",
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
            }
        ]
    )
    report = build_tracking_report(df)
    ok, max_diff = validate_tracking_tolerance(report, tolerance=1e-6)
    assert ok
    assert max_diff <= 1e-6


@pytest.mark.unit
def test_untracked_case_convertible_to_trace_format():
    df = pd.DataFrame(
        [
            {
                "ship_id": "S_untracked",
                "ship_date": "2025-01-01",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 0.0,
                "amount_ship": 0.0,
                "claim_qty": 10.0,
                "claim_amount": 100.0,
            }
        ]
    )
    report = build_tracking_report(df)
    trace = build_trace_candidates(report, min_coverage=0.75)
    assert len(trace) == 1
    assert trace.iloc[0]["trace_status"] == "Unverified"
    assert trace.iloc[0]["trace_reason"] == "no_tracking"
