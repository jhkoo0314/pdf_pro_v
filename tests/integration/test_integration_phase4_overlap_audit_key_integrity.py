from __future__ import annotations

import re

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
from src.share_engine import ShareConfig, run_share_settlement


def _to_canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for c in df.columns:
        m = re.match(r"^([a-z0-9_]+)\s\(.+\)$", str(c))
        renamed[c] = m.group(1) if m else c
    return df.rename(columns=renamed)


@pytest.mark.integration
def test_share_overlap_audit_keys_match_share_settlement(test_work_dir):
    tracking = pd.DataFrame(
        [
            {
                "ship_id": "S100",
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
                "ship_id": "S101",
                "ship_date": "2025-01-11",
                "year_month": "2025-01",
                "year_quarter": "2025-Q1",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "qty": 20,
                "amount_ship": 2000.0,
                "amount_pre_share": 2000.0,
                "pharmacy_uid": "P002",
                "overlap_participant_type": "mixed",
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
                "version": "v2",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            }
        ]
    )
    write_dual_outputs(tracking, test_work_dir, "tracking_report", include_default=False)
    write_dual_outputs(rules, test_work_dir, "share_rules", include_default=False)

    settled = run_share_settlement(
        input_dir=test_work_dir,
        output_dir=test_work_dir,
        config=ShareConfig(overlap_enabled=True),
    )
    audit = _to_canonical_columns(pd.read_parquet(test_work_dir / "share_overlap_audit_label.parquet"))

    share_keys = set(
        tuple(x)
        for x in settled[["year_quarter", "territory_code", "brand", "overlap_group_id"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    audit_keys = set(
        tuple(x)
        for x in audit[["year_quarter", "territory_code", "brand", "overlap_group_id"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    assert share_keys == audit_keys
    assert (audit["conservation_gap"].astype(float).abs() <= 1e-6).all()
