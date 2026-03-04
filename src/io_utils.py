"""I/O utilities for parquet/csv and simple schema checks."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd

from src.column_labels import to_bilingual_columns
from src.contracts import validate_required_columns


def ensure_parent_dir(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_csv(df: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    p = ensure_parent_dir(path)
    df.to_csv(p, index=index, encoding="utf-8")
    return p


def read_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")


def write_parquet(df: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    p = ensure_parent_dir(path)
    # Engine is selected by pandas; pyarrow is recommended by project contract.
    df.to_parquet(p, index=index)
    return p


def read_parquet(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def validate_schema(df: pd.DataFrame, required_columns: Sequence[str]) -> None:
    result = validate_required_columns(df.columns, required_columns)
    if not result.ok:
        raise ValueError(result.message)


def save_with_schema_check(
    df: pd.DataFrame,
    path: str | Path,
    required_columns: Sequence[str],
    fmt: str = "parquet",
) -> Path:
    validate_schema(df, required_columns)
    if fmt == "parquet":
        return write_parquet(df, path)
    if fmt == "csv":
        return write_csv(df, path)
    raise ValueError(f"Unsupported format: {fmt}")


def write_dual_outputs(
    df: pd.DataFrame,
    output_dir: str | Path,
    base_name: str,
    include_default: bool = False,
) -> None:
    """Write canonical and bilingual label files together.

    Canonical files (optional):
    - {base_name}.parquet
    - {base_name}.csv

    Label files:
    - {base_name}_label.parquet
    - {base_name}_label.csv
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if include_default:
        write_parquet(df, out / f"{base_name}.parquet")
        write_csv(df, out / f"{base_name}.csv")
    label_df = to_bilingual_columns(df)
    write_parquet(label_df, out / f"{base_name}_label.parquet")
    write_csv(label_df, out / f"{base_name}_label.csv")
