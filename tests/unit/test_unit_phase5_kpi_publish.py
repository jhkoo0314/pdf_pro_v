from __future__ import annotations

import pandas as pd
import pytest

from src.kpi_publish import _data_quality_flag


@pytest.mark.unit
def test_data_quality_flag_is_pass_when_all_validation_pass():
    validation = pd.DataFrame(
        [
            {"rule_name": "r1", "status": "pass"},
            {"rule_name": "r2", "status": "PASS"},
        ]
    )
    assert _data_quality_flag(validation) == "pass"


@pytest.mark.unit
def test_data_quality_flag_is_fail_when_any_not_pass_or_empty():
    validation_warn = pd.DataFrame(
        [
            {"rule_name": "r1", "status": "pass"},
            {"rule_name": "r2", "status": "warn"},
        ]
    )
    validation_empty = pd.DataFrame(columns=["rule_name", "status"])
    assert _data_quality_flag(validation_warn) == "fail"
    assert _data_quality_flag(validation_empty) == "fail"
