from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd
import pytest

from src.ingest_merge import run_ingest_merge
from src.kpi_publish import run_kpi_publish
from src.mastering import run_mastering
from src.share_engine import run_share_settlement
from src.trace_log import run_trace_log
from src.tracking_validation import run_tracking_validation
from src.validation import run_validation
import app.streamlit_app as ui


def _copy_source_raw_files(src_raw: Path, dst_raw: Path) -> None:
    dst_raw.mkdir(parents=True, exist_ok=True)
    for p in src_raw.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in {".xlsx", ".csv"}:
            shutil.copy2(p, dst_raw / p.name)


@pytest.mark.integration
def test_streamlit_data_flow_tracking_to_share_to_kpi(test_work_dir):
    raw = test_work_dir / "raw"
    out = test_work_dir / "out"
    _copy_source_raw_files(Path("data/raw"), raw)

    run_ingest_merge(raw_dir=raw, output_dir=raw, seed=42)
    run_mastering(raw_dir=raw, output_dir=out, seed=42, territory_missing_threshold=0.05)
    run_tracking_validation(input_dir=out, output_dir=out, min_coverage=0.75)
    run_share_settlement(input_dir=out, output_dir=out)
    run_kpi_publish(input_dir=out, output_dir=out)
    run_validation(input_dir=out, output_dir=out)
    run_trace_log(input_dir=out, output_dir=out)

    tracking = ui._read_label_csv("tracking_report", root=out)
    share = ui._read_label_csv("share_settlement", root=out)
    rep_kpi_q = ui._read_label_csv("rep_kpi_quarter", root=out)

    assert len(tracking) > 0
    assert len(share) > 0
    assert len(rep_kpi_q) > 0

    c = {ui._canonical_col(col): col for col in share.columns}
    period = sorted(share[c["year_quarter"]].dropna().astype(str).unique().tolist())[:1]
    territory = sorted(share[c["territory_code"]].dropna().astype(str).unique().tolist())[:1]
    brand = sorted(share[c["brand"]].dropna().astype(str).unique().tolist())[:1]

    filtered = ui._apply_filters(
        share,
        period_mode="quarter",
        period_values=period,
        territory_values=territory,
        brand_values=brand,
        pharmacy_values=[],
        rep_values=[],
    )
    assert len(filtered) > 0
