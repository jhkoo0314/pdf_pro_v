from __future__ import annotations

import pandas as pd
import pytest

from src.trace_log import apply_trace_actions


@pytest.mark.regression
def test_trace_recovery_loop_keeps_confirmed_case_stable():
    base_log = pd.DataFrame(
        [
            {
                "case_id": "TRC_1",
                "trace_status": "Unverified",
                "ship_id": "S1",
                "year_quarter": "2025-Q1",
                "territory_code": "T01",
                "brand": "록소르정",
                "trace_reason": "low_coverage",
                "note": "",
                "updated_by": "system",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "created_from": "tracking_validation",
            }
        ]
    )
    actions = pd.DataFrame(
        [
            {"case_id": "TRC_1", "to_status": "Inquired", "updated_by": "qa", "note": "ask wholesaler"},
            {"case_id": "TRC_1", "to_status": "Confirmed", "updated_by": "qa", "note": "confirmed route"},
            {"case_id": "TRC_1", "to_status": "Rejected", "updated_by": "qa", "note": "should fail"},
        ]
    )
    out, hist = apply_trace_actions(base_log, actions)

    assert out.iloc[0]["trace_status"] == "Confirmed"
    assert hist.iloc[0]["result"] == "applied"
    assert hist.iloc[1]["result"] == "applied"
    assert hist.iloc[2]["result"] == "invalid_transition"
