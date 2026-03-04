from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.trace_log import run_trace_log
from src.validation import run_validation


@pytest.mark.integration
def test_phase6_exit_criteria_outputs_and_missing_reason_zero(test_work_dir):
    share = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "록소르정",
                "coverage_ratio": 0.6,
                "share_rule_source": "none",
                "mapping_quality_flag": "C",
            }
        ]
    )
    trace_candidates = pd.DataFrame(
        [
            {
                "case_id": "TRC_1",
                "ship_id": "S1",
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "록소르정",
                "gap_amount": 100.0,
                "coverage_ratio": 0.6,
                "trace_status": "Unverified",
                "trace_reason": "low_coverage",
                "created_from": "tracking_validation",
            }
        ]
    )
    trace_actions = pd.DataFrame(
        [
            {"case_id": "TRC_1", "to_status": "Inquired", "updated_by": "qa", "note": "inquiry sent"},
            {"case_id": "TRC_1", "to_status": "Confirmed", "updated_by": "qa", "note": "route confirmed"},
        ]
    )

    write_dual_outputs(share, test_work_dir, "share_settlement", include_default=False)
    write_dual_outputs(trace_candidates, test_work_dir, "tracking_trace_candidates", include_default=False)
    write_dual_outputs(trace_actions, test_work_dir, "trace_actions", include_default=False)

    validation_outputs = run_validation(input_dir=test_work_dir, output_dir=test_work_dir)
    trace_outputs = run_trace_log(input_dir=test_work_dir, output_dir=test_work_dir)

    # Exit criteria 1: validation_report generated
    assert (test_work_dir / "validation_report_label.csv").exists()
    assert len(validation_outputs["validation_report"]) > 0

    # Exit criteria 2: trace transition log generated
    assert (test_work_dir / "trace_history_label.csv").exists()
    assert len(trace_outputs["trace_history"]) >= 1

    # Exit criteria 3: no missing failure reason/details
    vr = validation_outputs["validation_report"]
    assert vr["details"].astype(str).str.strip().ne("").all()
