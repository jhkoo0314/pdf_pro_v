from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.kpi_publish import run_kpi_publish


@pytest.mark.integration
def test_integration_share_settlement_to_kpi_publish(test_work_dir):
    share = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "ship_date": "2025-01-10",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "록소르정",
                "amount_pre_share": 1000.0,
                "amount_post_share": 1000.0,
                "share_applied_flag": True,
                "share_rule_source": "direct",
            },
            {
                "ship_id": "S2",
                "ship_date": "2025-02-10",
                "year_month": "2025-02",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "자누비아정",
                "amount_pre_share": 2000.0,
                "amount_post_share": 2000.0,
                "share_applied_flag": True,
                "share_rule_source": "extended",
            },
        ]
    )
    rep = pd.DataFrame(
        [
            {"rep_id": "RC001", "rep_name": "최유정", "territory_code": "T01", "active_flag": True}
        ]
    )
    validation = pd.DataFrame(
        [
            {
                "rule_name": "territory_code_missing_ratio",
                "metric_value": 0.0,
                "threshold": 0.05,
                "status": "pass",
                "note": "ok",
            }
        ]
    )
    write_dual_outputs(share, test_work_dir, "share_settlement", include_default=False)
    write_dual_outputs(rep, test_work_dir, "dim_rep", include_default=False)
    write_dual_outputs(validation, test_work_dir, "validation_report", include_default=False)

    outputs = run_kpi_publish(input_dir=test_work_dir, output_dir=test_work_dir)

    assert set(outputs.keys()) == {
        "rep_kpi_month",
        "rep_kpi_quarter",
        "rep_kpi_year",
        "kpi_summary_month",
        "kpi_summary_quarter",
        "kpi_summary_year",
    }
    for name in outputs:
        assert (test_work_dir / f"{name}_label.csv").exists()
        assert (test_work_dir / f"{name}_label.parquet").exists()
        assert "data_quality_flag" in outputs[name].columns
