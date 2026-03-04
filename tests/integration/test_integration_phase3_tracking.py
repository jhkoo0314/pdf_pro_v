from pathlib import Path

import pytest

from src.tracking_validation import run_tracking_validation


@pytest.mark.integration
def test_mastering_to_tracking_validation_flow():
    report = run_tracking_validation(input_dir="data/outputs", output_dir="data/outputs")
    assert len(report) > 0
    assert "tracking_quality_flag" in report.columns
    assert (Path("data/outputs") / "tracking_report_label.parquet").exists()
    assert (Path("data/outputs") / "tracking_report_label.csv").exists()
