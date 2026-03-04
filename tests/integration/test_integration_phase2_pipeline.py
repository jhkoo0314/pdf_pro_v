from pathlib import Path
import shutil

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


@pytest.mark.integration
def test_generate_ingest_to_mastering_flow(test_work_dir: Path):
    src_raw = Path("data/raw")
    run_raw = test_work_dir / "raw"
    out_dir = test_work_dir / "outputs"
    _copy_source_raw_files(src_raw, run_raw)

    run_ingest_merge(raw_dir=run_raw, output_dir=run_raw, seed=42)
    artifacts = run_mastering(raw_dir=run_raw, output_dir=out_dir, seed=42)

    assert (run_raw / "fact_ship_pharmacy_raw_label.parquet").exists()
    assert (run_raw / "ref_pharmacy_address_label.parquet").exists()
    assert (run_raw / "fact_ship_pharmacy_raw_label.csv").exists()
    assert (out_dir / "fact_ship_pharmacy_mastered_label.parquet").exists()
    assert (out_dir / "dim_pharmacy_master_label.parquet").exists()
    assert (out_dir / "validation_report_label.parquet").exists()
    assert (out_dir / "dim_rep_label.csv").exists()

    mastered = artifacts["fact_ship_pharmacy_mastered"]
    assert mastered["pharmacy_uid"].isna().sum() == 0
    assert mastered["territory_code"].isna().sum() == 0
