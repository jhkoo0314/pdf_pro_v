from pathlib import Path

import pytest

from src.tracking_validation import run_tracking_validation, validate_tracking_tolerance


@pytest.mark.integration
def test_tracking_exit_criteria_outputs_and_tolerance():
    report = run_tracking_validation(input_dir="data/outputs", output_dir="data/outputs")
    ok, max_diff = validate_tracking_tolerance(report, tolerance=1e-6)
    assert ok
    assert max_diff <= 1e-6
    assert (Path("data/outputs") / "tracking_report_label.parquet").exists()
    assert (Path("data/outputs") / "tracking_trace_candidates_label.parquet").exists()
