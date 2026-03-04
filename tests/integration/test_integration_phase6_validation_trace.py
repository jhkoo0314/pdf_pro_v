from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.trace_log import run_trace_log
from src.tracking_validation import run_tracking_validation
from src.validation import run_validation


@pytest.mark.integration
def test_integration_tracking_to_validation_to_trace_log(test_work_dir):
    mastered = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "ship_date": "2025-01-10",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "록소르정",
                "qty": 10.0,
                "amount_ship": 1000.0,
                "mapping_quality_flag": "C",
            },
            {
                "ship_id": "S2",
                "ship_date": "2025-01-11",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "자누비아정",
                "qty": 0.0,
                "amount_ship": 0.0,
                "claim_qty": 20.0,
                "claim_amount": 2000.0,
                "mapping_quality_flag": "C",
            },
        ]
    )
    write_dual_outputs(mastered, test_work_dir, "fact_ship_pharmacy_mastered", include_default=False)

    tracking = run_tracking_validation(input_dir=test_work_dir, output_dir=test_work_dir, min_coverage=0.75)
    share = tracking.copy()
    share["amount_pre_share"] = share["amount_ship"].astype(float)
    share["amount_post_share"] = share["amount_ship"].astype(float)
    share["share_rule_source"] = "direct"
    share["share_applied_flag"] = True
    write_dual_outputs(share, test_work_dir, "share_settlement", include_default=False)

    validation_outputs = run_validation(input_dir=test_work_dir, output_dir=test_work_dir)
    trace_outputs = run_trace_log(input_dir=test_work_dir, output_dir=test_work_dir)

    assert len(validation_outputs["validation_report"]) >= 1
    assert "data_quality_flag" in validation_outputs["data_quality_flag"].columns
    assert {"trace_log", "trace_history"} == set(trace_outputs.keys())
    assert (test_work_dir / "trace_log_label.parquet").exists()
