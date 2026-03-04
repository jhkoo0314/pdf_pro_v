from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.validation import run_validation


@pytest.mark.contract
def test_validation_report_contract_columns(test_work_dir):
    share = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "coverage_ratio": 1.0,
                "share_rule_source": "direct",
                "territory_code": "T01",
                "mapping_quality_flag": "C",
            }
        ]
    )
    trace = pd.DataFrame(columns=["case_id"])
    write_dual_outputs(share, test_work_dir, "share_settlement", include_default=False)
    write_dual_outputs(trace, test_work_dir, "tracking_trace_candidates", include_default=False)

    out = run_validation(input_dir=test_work_dir, output_dir=test_work_dir)["validation_report"]
    required = {
        "rule_name",
        "metric_value",
        "threshold",
        "status",
        "note",
        "issue_type",
        "severity",
        "entity_id",
        "year_quarter",
        "details",
    }
    assert required.issubset(set(out.columns))
