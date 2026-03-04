from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.kpi_publish import run_kpi_publish


@pytest.mark.e2e
def test_e2e_kpi_period_total_consistency(test_work_dir):
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
                "ship_date": "2025-03-10",
                "year_month": "2025-03",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "자누비아정",
                "amount_pre_share": 2000.0,
                "amount_post_share": 2000.0,
                "share_applied_flag": True,
                "share_rule_source": "extended",
            },
            {
                "ship_id": "S3",
                "ship_date": "2025-05-10",
                "year_month": "2025-05",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T02",
                "brand": "리피토정",
                "amount_pre_share": 3000.0,
                "amount_post_share": 3000.0,
                "share_applied_flag": True,
                "share_rule_source": "direct",
            },
        ]
    )
    rep = pd.DataFrame(
        [
            {"rep_id": "RC001", "rep_name": "최유정", "territory_code": "T01", "active_flag": True},
            {"rep_id": "RC002", "rep_name": "김수아", "territory_code": "T02", "active_flag": True},
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

    run_kpi_publish(input_dir=test_work_dir, output_dir=test_work_dir)

    m = pd.read_parquet(test_work_dir / "kpi_summary_month_label.parquet")
    q = pd.read_parquet(test_work_dir / "kpi_summary_quarter_label.parquet")
    y = pd.read_parquet(test_work_dir / "kpi_summary_year_label.parquet")

    m_pre = float(m[[c for c in m.columns if c.startswith("total_pre_share")][0]].sum())
    q_pre = float(q[[c for c in q.columns if c.startswith("total_pre_share")][0]].sum())
    y_pre = float(y[[c for c in y.columns if c.startswith("total_pre_share")][0]].sum())
    m_post = float(m[[c for c in m.columns if c.startswith("total_post_share")][0]].sum())
    q_post = float(q[[c for c in q.columns if c.startswith("total_post_share")][0]].sum())
    y_post = float(y[[c for c in y.columns if c.startswith("total_post_share")][0]].sum())

    assert abs(m_pre - q_pre) < 1e-6
    assert abs(q_pre - y_pre) < 1e-6
    assert abs(m_post - q_post) < 1e-6
    assert abs(q_post - y_post) < 1e-6
