from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.io_utils import write_dual_outputs
import app.streamlit_app as ui


@pytest.mark.smoke
def test_meta_caption_contains_rule_version_and_timestamp(test_work_dir, monkeypatch):
    out_dir = test_work_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    rules = pd.DataFrame(
        [
            {"year_quarter": "2025-Q1", "territory_code": "T01", "brand": "록소르정", "version": "v1", "status": "confirmed"}
        ]
    )
    write_dual_outputs(rules, out_dir, "share_rules", include_default=False)
    # Ensure at least one output csv exists for execution time extraction.
    (out_dir / "dummy_label.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    monkeypatch.setattr(ui, "OUT_DIR", Path(out_dir))
    caption = ui._meta_caption()
    assert "기준 파일:" in caption
    assert "룰 버전:" in caption
    assert "v1" in caption
    assert "실행시각:" in caption
