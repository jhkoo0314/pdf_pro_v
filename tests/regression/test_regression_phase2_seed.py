from pathlib import Path
import shutil

import pandas as pd
import pytest

from src.ingest_merge import run_ingest_merge
from src.mastering import run_mastering


def _copy_source_raw_files(src_raw: Path, dst_raw: Path) -> None:
    dst_raw.mkdir(parents=True, exist_ok=True)
    for p in src_raw.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in {".xlsx", ".csv"}:
            shutil.copy2(p, dst_raw / p.name)


@pytest.mark.regression
def test_same_seed_same_parameters_produce_identical_body(test_work_dir: Path):
    src_raw = Path("data/raw")

    run1_raw = test_work_dir / "run1_raw"
    run1_out = test_work_dir / "run1_out"
    run2_raw = test_work_dir / "run2_raw"
    run2_out = test_work_dir / "run2_out"

    _copy_source_raw_files(src_raw, run1_raw)
    _copy_source_raw_files(src_raw, run2_raw)

    run_ingest_merge(raw_dir=run1_raw, output_dir=run1_raw, seed=77)
    art1 = run_mastering(raw_dir=run1_raw, output_dir=run1_out, seed=77)

    run_ingest_merge(raw_dir=run2_raw, output_dir=run2_raw, seed=77)
    art2 = run_mastering(raw_dir=run2_raw, output_dir=run2_out, seed=77)

    f1 = art1["fact_ship_pharmacy_mastered"].sort_values("ship_id").reset_index(drop=True)
    f2 = art2["fact_ship_pharmacy_mastered"].sort_values("ship_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(f1, f2, check_like=False)

    r1 = art1["dim_rep"].sort_values("rep_id").reset_index(drop=True)
    r2 = art2["dim_rep"].sort_values("rep_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(r1, r2, check_like=False)
