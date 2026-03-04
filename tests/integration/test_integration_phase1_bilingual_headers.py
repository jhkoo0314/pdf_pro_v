from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.mark.integration
def test_output_reports_include_bilingual_headers():
    target = Path("data/outputs/tracking_report_label.csv")
    assert target.exists()
    df = pd.read_csv(target, encoding="utf-8-sig", nrows=1)
    cols = df.columns.tolist()
    assert any(" (" in c and c.endswith(")") for c in cols)
    assert "ship_date (출고일)" in cols
    assert "amount_ship (출고금액)" in cols
    assert "territory_code (영업권역코드)" in cols
