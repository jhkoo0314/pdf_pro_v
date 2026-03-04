from __future__ import annotations

import pandas as pd
import pytest

from src.share_engine import ShareConfig, apply_share_settlement


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ship_id": "S200",
                "ship_date": "2025-04-03",
                "year_month": "2025-04",
                "year_quarter": "2025-Q2",
                "year": 2025,
                "territory_code": "T05",
                "brand": "brand_b",
                "qty": 12,
                "amount_ship": 2200.0,
                "amount_pre_share": 2200.0,
                "pharmacy_uid": "P900",
                "overlap_participant_type": "mixed",
            }
        ]
    )


@pytest.mark.regression
def test_phase2_overlap_deterministic_with_same_input():
    base = _base_df()
    rules = pd.DataFrame(
        [
            {
                "year_quarter": "2025-Q1",
                "territory_code": "T05",
                "brand": "brand_b",
                "ratio_hosp": 0.4,
                "ratio_clinic": 0.6,
                "version": "v1",
                "status": "confirmed",
                "overlap_mode": "full",
                "participant_scope": "mixed",
                "priority": 100,
            }
        ]
    )

    out1 = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))
    out2 = apply_share_settlement(base, rules, config=ShareConfig(overlap_enabled=True))
    pd.testing.assert_frame_equal(
        out1.sort_values("ship_id").reset_index(drop=True),
        out2.sort_values("ship_id").reset_index(drop=True),
        check_like=False,
    )
    assert out1.iloc[0]["share_rule_source"] == "extended"
    assert out1.iloc[0]["rule_resolution_path"] == "overlap_resolved"
