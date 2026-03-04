from __future__ import annotations

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.share_engine import ShareConfig, run_share_settlement


def _tracking_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "ship_date": "2025-01-10",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 10,
                "amount_ship": 1000.0,
                "amount_pre_share": 1000.0,
                "pharmacy_uid": "P001",
                "overlap_participant_type": "mixed",
            },
            {
                "ship_id": "S2",
                "ship_date": "2025-01-11",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 15,
                "amount_ship": 1500.0,
                "amount_pre_share": 1500.0,
                "pharmacy_uid": "P002",
                "overlap_participant_type": "clinic",
            },
        ]
    )


def _rules() -> pd.DataFrame:
    return pd.DataFrame(
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
            },
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.6,
                "ratio_clinic": 0.4,
                "version": "v2",
                "status": "confirmed",
                "overlap_mode": "partial",
                "participant_scope": "clinic_only",
                "priority": 200,
            },
        ]
    )


@pytest.mark.integration
def test_tracking_to_share_settlement_phase2_overlap_on_off(test_work_dir):
    tracking = _tracking_rows()
    rules = _rules()
    write_dual_outputs(tracking, test_work_dir, "tracking_report", include_default=False)
    write_dual_outputs(rules, test_work_dir, "share_rules", include_default=False)

    off_df = run_share_settlement(
        input_dir=test_work_dir,
        output_dir=test_work_dir,
        config=ShareConfig(overlap_enabled=False),
    )
    on_df = run_share_settlement(
        input_dir=test_work_dir,
        output_dir=test_work_dir,
        config=ShareConfig(overlap_enabled=True),
    )

    assert (test_work_dir / "share_overlap_audit_label.parquet").exists()
    assert off_df["overlap_group_id"].isna().all()
    assert (off_df["overlap_generated_flag"] == False).all()
    assert on_df["overlap_group_id"].notna().all()
    assert (on_df["overlap_generated_flag"] == True).any()
