from __future__ import annotations

import pandas as pd
import pytest

from src.share_engine import ShareConfig, apply_share_settlement


@pytest.mark.regression
def test_q1_q2_boundary_rule_inheritance_and_overlap_resolution():
    base = pd.DataFrame(
        [
            {
                "ship_id": "Q2_DIRECT_NONE",
                "ship_date": "2025-04-10",
                "year_month": "2025-04",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T01",
                "brand": "brand_a",
                "amount_ship": 1000.0,
                "amount_pre_share": 1000.0,
                "qty": 10,
                "pharmacy_uid": "P001",
                "overlap_participant_type": "mixed",
            },
            {
                "ship_id": "Q2_EXTENDED_FULL",
                "ship_date": "2025-04-11",
                "year_month": "2025-04",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T02",
                "brand": "brand_a",
                "amount_ship": 1000.0,
                "amount_pre_share": 1000.0,
                "qty": 10,
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
                "ratio_hosp": 0.6,
                "ratio_clinic": 0.4,
                "version": "v1_q1_full",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            },
            {
                "year_quarter": "2025-Q2",
                "territory_code": "T01",
                "brand": "brand_a",
                "ratio_hosp": 0.5,
                "ratio_clinic": 0.5,
                "version": "v2_q2_none",
                "status": "confirmed",
                "overlap_mode": "none",
                "participant_scope": "mixed",
                "priority": 200,
            },
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T02",
                "brand": "brand_a",
                "ratio_hosp": 0.7,
                "ratio_clinic": 0.3,
                "version": "v1_q1_full_t02",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            },
        ]
    )

    out = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))
    by_id = {r["ship_id"]: r for _, r in out.iterrows()}

    # Q2 direct rule exists with overlap_mode=none => overlap is resolved (not overlap_resolved path)
    assert by_id["Q2_DIRECT_NONE"]["share_rule_source"] == "direct"
    assert by_id["Q2_DIRECT_NONE"]["rule_resolution_path"] == "direct"
    assert by_id["Q2_DIRECT_NONE"]["share_rule_version"] == "v2_q2_none"

    # Q2 direct missing in T02 => inherit Q1 rule and keep overlap-resolved path
    assert by_id["Q2_EXTENDED_FULL"]["share_rule_source"] == "extended"
    assert by_id["Q2_EXTENDED_FULL"]["rule_resolution_path"] == "overlap_resolved"
    assert by_id["Q2_EXTENDED_FULL"]["share_rule_version"] == "v1_q1_full_t02"
