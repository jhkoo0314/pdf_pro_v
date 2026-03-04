from pathlib import Path
import uuid

import pandas as pd
import pytest

from src.contracts import REQUIRED_CORE_COLUMNS
from src.io_utils import read_csv, read_parquet, save_with_schema_check, write_dual_outputs


def _test_output_path(suffix: str) -> Path:
    out_dir = Path("data") / "_test_tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{uuid.uuid4().hex}{suffix}"


@pytest.mark.unit
def test_csv_round_trip_with_schema():
    row = {
        "ship_date": "2026-01-01",
        "year_month": "2026-01",
        "year_quarter": "2026-Q1",
        "year": 2026,
        "amount_ship": 1000.0,
        "amount_supply": 900.0,
        "amount_pre_share": 1000.0,
        "amount_post_share": 1000.0,
        "qty": 10,
        "brand": "BrandA",
        "territory_code": "T01",
        "pharmacy_uid": "P001",
    }
    df = pd.DataFrame([row])
    out = _test_output_path(".csv")

    save_with_schema_check(df, out, REQUIRED_CORE_COLUMNS, fmt="csv")
    loaded = read_csv(out)

    assert len(loaded) == 1
    assert set(REQUIRED_CORE_COLUMNS).issubset(set(loaded.columns))


@pytest.mark.unit
def test_schema_check_fails_on_missing_column():
    df = pd.DataFrame([{"ship_date": "2026-01-01"}])
    out = _test_output_path(".csv")
    with pytest.raises(ValueError):
        save_with_schema_check(df, out, REQUIRED_CORE_COLUMNS, fmt="csv")


@pytest.mark.unit
def test_parquet_round_trip_with_schema():
    pyarrow = pytest.importorskip("pyarrow")
    assert pyarrow is not None

    row = {
        "ship_date": "2026-01-01",
        "year_month": "2026-01",
        "year_quarter": "2026-Q1",
        "year": 2026,
        "amount_ship": 1000.0,
        "amount_supply": 900.0,
        "amount_pre_share": 1000.0,
        "amount_post_share": 1000.0,
        "qty": 10,
        "brand": "BrandA",
        "territory_code": "T01",
        "pharmacy_uid": "P001",
    }
    df = pd.DataFrame([row])
    out = _test_output_path(".parquet")

    save_with_schema_check(df, out, REQUIRED_CORE_COLUMNS, fmt="parquet")
    loaded = read_parquet(out)

    assert len(loaded) == 1
    assert set(REQUIRED_CORE_COLUMNS).issubset(set(loaded.columns))


@pytest.mark.unit
def test_write_dual_outputs_creates_bilingual_label_files():
    row = {
        "ship_date": "2026-01-01",
        "year_month": "2026-01",
        "year_quarter": "2026-Q1",
        "year": 2026,
        "amount_ship": 1000.0,
        "amount_supply": 900.0,
        "amount_pre_share": 1000.0,
        "amount_post_share": 1000.0,
        "qty": 10,
        "brand": "BrandA",
        "territory_code": "T01",
        "pharmacy_uid": "P001",
    }
    df = pd.DataFrame([row])
    out_dir = Path("data") / "_test_tmp" / uuid.uuid4().hex
    out_dir.mkdir(parents=True, exist_ok=True)

    write_dual_outputs(df, out_dir, "sample", include_default=False)

    assert not (out_dir / "sample.csv").exists()
    assert not (out_dir / "sample.parquet").exists()
    assert (out_dir / "sample_label.csv").exists()
    assert (out_dir / "sample_label.parquet").exists()

    label_df = read_csv(out_dir / "sample_label.csv")
    assert any(c.startswith("ship_date (") for c in label_df.columns)
