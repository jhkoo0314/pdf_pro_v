from __future__ import annotations

import pandas as pd
import pytest

from src.trace_log import apply_trace_actions, can_transition
from src.validation import build_validation_report


@pytest.mark.unit
def test_validation_issue_classification_counts_rule_missing():
    share = pd.DataFrame(
        [
            {
                "ship_id": "S1",
                "coverage_ratio": 0.5,
                "share_rule_source": "none",
                "territory_code": "T01",
                "mapping_quality_flag": "C",
            }
        ]
    )
    trace = pd.DataFrame([{"case_id": "TRC_1"}])
    report = build_validation_report(share, trace)
    by_issue = {r["issue_type"]: r for _, r in report.iterrows()}

    assert by_issue["RULE_MISSING"]["metric_value"] == 1.0
    assert by_issue["LOW_COVERAGE"]["metric_value"] == 1.0
    assert by_issue["TRACE_OPEN_CASE"]["metric_value"] == 1.0


@pytest.mark.unit
def test_trace_status_transition_rules():
    assert can_transition("Unverified", "Inquired")
    assert can_transition("Inquired", "Confirmed")
    assert can_transition("Inquired", "Rejected")
    assert not can_transition("Unverified", "Confirmed")
    assert not can_transition("Confirmed", "Inquired")


@pytest.mark.unit
def test_apply_trace_actions_blocks_invalid_transition():
    log = pd.DataFrame(
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
            {"case_id": "TRC_1", "to_status": "Confirmed", "updated_by": "qa", "note": "skip"},
        ]
    )
    out, hist = apply_trace_actions(log, actions)
    assert out.iloc[0]["trace_status"] == "Unverified"
    assert hist.iloc[0]["result"] == "invalid_transition"
