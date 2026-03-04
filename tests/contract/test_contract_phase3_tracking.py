import pytest

from src.tracking_validation import run_tracking_validation


TRACKING_REQUIRED_COLS = {
    "ship_id",
    "ship_date",
    "year_month",
    "year_quarter",
    "year",
    "territory_code",
    "brand",
    "qty",
    "amount_ship",
    "claim_qty",
    "claim_amount",
    "tracked_qty",
    "tracked_amount",
    "gap_qty",
    "gap_amount",
    "coverage_ratio",
    "gap_ratio",
    "tracking_quality_flag",
}


@pytest.mark.contract
def test_tracking_report_contract_columns():
    report = run_tracking_validation(input_dir="data/outputs", output_dir="data/outputs")
    assert TRACKING_REQUIRED_COLS.issubset(set(report.columns))
