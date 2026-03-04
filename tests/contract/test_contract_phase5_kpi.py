from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.kpi_publish import run_kpi_publish


def _prepare_minimum_kpi_inputs(base_dir) -> None:
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
            }
        ]
    )
    rep = pd.DataFrame(
        [
            {
                "rep_id": "RC001",
                "rep_name": "최유정",
                "territory_code": "T01",
                "active_flag": True,
            }
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
    write_dual_outputs(share, base_dir, "share_settlement", include_default=False)
    write_dual_outputs(rep, base_dir, "dim_rep", include_default=False)
    write_dual_outputs(validation, base_dir, "validation_report", include_default=False)


@pytest.mark.contract
def test_phase5_contract_for_all_kpi_outputs(test_work_dir):
    _prepare_minimum_kpi_inputs(test_work_dir)
    run_kpi_publish(input_dir=test_work_dir, output_dir=test_work_dir)

    expected_cols = {
        "rep_kpi_month": {
            "year_month",
            "rep_id",
            "rep_name",
            "territory_code",
            "brand",
            "amount_pre_share",
            "amount_post_share",
            "data_quality_flag",
        },
        "rep_kpi_quarter": {
            "year_quarter",
            "rep_id",
            "rep_name",
            "territory_code",
            "brand",
            "amount_pre_share",
            "amount_post_share",
            "data_quality_flag",
        },
        "rep_kpi_year": {
            "year",
            "rep_id",
            "rep_name",
            "territory_code",
            "brand",
            "amount_pre_share",
            "amount_post_share",
            "data_quality_flag",
        },
        "kpi_summary_month": {
            "year_month",
            "total_pre_share",
            "total_post_share",
            "share_rules_applied_count",
            "data_quality_flag",
        },
        "kpi_summary_quarter": {
            "year_quarter",
            "total_pre_share",
            "total_post_share",
            "share_rules_applied_count",
            "data_quality_flag",
        },
        "kpi_summary_year": {
            "year",
            "total_pre_share",
            "total_post_share",
            "share_rules_applied_count",
            "data_quality_flag",
        },
    }

    for base_name, required in expected_cols.items():
        out = pd.read_parquet(test_work_dir / f"{base_name}_label.parquet")
        canonical_cols = {c.split(" (")[0] for c in out.columns}
        assert required.issubset(canonical_cols)
