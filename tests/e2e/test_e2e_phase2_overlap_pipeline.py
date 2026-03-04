from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.kpi_publish import run_kpi_publish
from src.share_engine import ShareConfig, run_share_settlement
from src.tracking_validation import run_tracking_validation
from src.validation import run_validation


@pytest.mark.e2e
def test_e2e_phase2_overlap_tracking_to_share_to_kpi(test_work_dir):
    mastered = pd.DataFrame(
        [
            {
                "ship_id": "S300",
                "ship_date": "2025-01-10",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 10.0,
                "amount_ship": 1000.0,
                "pharmacy_uid": "P001",
                "mapping_quality_flag": "C",
                "overlap_participant_type": "mixed",
            },
            {
                "ship_id": "S301",
                "ship_date": "2025-01-11",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 20.0,
                "amount_ship": 2000.0,
                "pharmacy_uid": "P002",
                "mapping_quality_flag": "C",
                "overlap_participant_type": "clinic",
            },
        ]
    )
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.5,
                "ratio_clinic": 0.5,
                "version": "v1",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            }
        ]
    )
    rep = pd.DataFrame(
        [{"rep_id": "RC001", "rep_name": "홍길동", "territory_code": "T01", "active_flag": True}]
    )
    write_dual_outputs(mastered, test_work_dir, "fact_ship_pharmacy_mastered", include_default=False)
    write_dual_outputs(rules, test_work_dir, "share_rules", include_default=False)
    write_dual_outputs(rep, test_work_dir, "dim_rep", include_default=False)

    run_tracking_validation(input_dir=test_work_dir, output_dir=test_work_dir, min_coverage=0.75)
    share_df = run_share_settlement(
        input_dir=test_work_dir,
        output_dir=test_work_dir,
        config=ShareConfig(overlap_enabled=True),
    )
    run_validation(input_dir=test_work_dir, output_dir=test_work_dir)
    kpi_outputs = run_kpi_publish(input_dir=test_work_dir, output_dir=test_work_dir)

    assert (test_work_dir / "share_overlap_audit_label.parquet").exists()
    assert (share_df["overlap_group_id"].notna()).all()
    assert set(share_df["rule_resolution_path"].unique()).issubset(
        {"direct", "extended", "overlap_resolved", "none"}
    )
    assert abs(float(share_df["amount_pre_share"].sum()) - float(share_df["amount_post_share"].sum())) < 1e-6
    assert "rep_kpi_quarter" in kpi_outputs
