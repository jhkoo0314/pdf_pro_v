"""Mastering for pharmacy UID, territory mapping, and quality flags."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

from src.generate_synth import build_dimensions
from src.io_utils import write_dual_outputs


def _to_canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    renamed = {}
    for c in out.columns:
        m = re.match(r"^([a-z0-9_]+)\s\(.+\)$", str(c))
        renamed[c] = m.group(1) if m else c
    return out.rename(columns=renamed)


def _read_parquet_prefer_label(base_dir: Path, base_name: str) -> pd.DataFrame:
    canonical = base_dir / f"{base_name}.parquet"
    label = base_dir / f"{base_name}_label.parquet"
    if canonical.exists():
        return pd.read_parquet(canonical)
    if label.exists():
        return _to_canonical_columns(pd.read_parquet(label))
    raise FileNotFoundError(f"Missing parquet for {base_name} in {base_dir}")


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^a-z0-9가-힣]", "", text)
    return text


def make_pharmacy_key(name: object, addr: object, tel: object) -> str:
    return "|".join([normalize_text(name), normalize_text(addr), normalize_text(tel)])


def build_pharmacy_uid_map(ref_pharmacy_df: pd.DataFrame) -> pd.DataFrame:
    base = ref_pharmacy_df.copy()
    base["pharmacy_key"] = base.apply(
        lambda r: make_pharmacy_key(
            r.get("pharmacy_name"), r.get("pharmacy_addr"), r.get("pharmacy_tel")
        ),
        axis=1,
    )
    base = base.drop_duplicates(subset=["pharmacy_key"]).reset_index(drop=True)
    base["pharmacy_uid"] = [f"P{i:06d}" for i in range(1, len(base) + 1)]
    return base


def territory_from_pharmacy_uid(pharmacy_uid: str) -> str:
    digest = hashlib.md5(pharmacy_uid.encode("utf-8")).hexdigest()
    idx = (int(digest[:8], 16) % 10) + 1
    return f"T{idx:02d}"


def _build_dim_pharmacy_master(uid_map: pd.DataFrame) -> pd.DataFrame:
    dim = uid_map.copy()
    dim["territory_code"] = dim["pharmacy_uid"].map(territory_from_pharmacy_uid)
    dim["territory_source"] = "C"
    dim["active_flag"] = True
    return dim[
        [
            "pharmacy_uid",
            "pharmacy_key",
            "pharmacy_name",
            "pharmacy_addr",
            "pharmacy_tel",
            "pharmacy_provider_id",
            "territory_code",
            "territory_source",
            "active_flag",
            "source_file",
            "source_row_id",
        ]
    ].rename(columns={"pharmacy_provider_id": "pharmacy_account_id"})


def master_fact_ship(raw_fact_df: pd.DataFrame, dim_pharmacy_df: pd.DataFrame) -> pd.DataFrame:
    fact = raw_fact_df.copy()
    fact["pharmacy_key"] = fact.apply(
        lambda r: make_pharmacy_key(
            r.get("pharmacy_name"), r.get("pharmacy_addr"), r.get("pharmacy_tel")
        ),
        axis=1,
    )
    join_cols = ["pharmacy_uid", "pharmacy_key", "territory_code", "territory_source"]
    fact = fact.merge(dim_pharmacy_df[join_cols], on="pharmacy_key", how="left")
    fact["mapping_quality_flag"] = fact.apply(
        lambda r: "UNMAPPED"
        if pd.isna(r["pharmacy_uid"])
        else ("C" if pd.notna(r["territory_code"]) else "A"),
        axis=1,
    )
    return fact.drop(columns=["pharmacy_key"])


def build_validation_report(mastered_df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    total = len(mastered_df)
    missing_uid = int(mastered_df["pharmacy_uid"].isna().sum())
    missing_territory = int(mastered_df["territory_code"].isna().sum())
    territory_missing_ratio = (missing_territory / total) if total else 0.0
    return pd.DataFrame(
        [
            {
                "rule_name": "territory_code_missing_ratio",
                "metric_value": territory_missing_ratio,
                "threshold": threshold,
                "status": "pass" if territory_missing_ratio <= threshold else "warn",
                "note": f"missing_uid={missing_uid}, missing_territory={missing_territory}, total={total}",
            }
        ]
    )


def run_mastering(
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "data/outputs",
    seed: int = 42,
    territory_missing_threshold: float = 0.05,
) -> dict[str, pd.DataFrame]:
    raw = Path(raw_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw_fact = _read_parquet_prefer_label(raw, "fact_ship_pharmacy_raw")
    ref_pharmacy = _read_parquet_prefer_label(raw, "ref_pharmacy_address")

    uid_map = build_pharmacy_uid_map(ref_pharmacy)
    dim_pharmacy = _build_dim_pharmacy_master(uid_map)
    fact_mastered = master_fact_ship(raw_fact, dim_pharmacy)

    dims = build_dimensions(seed=seed)
    dim_branch = dims["dim_branch"]
    dim_rep = dims["dim_rep"]
    dim_rep_assign = dims["dim_rep_assign"]

    validation_report = build_validation_report(
        fact_mastered, threshold=territory_missing_threshold
    )

    artifacts = {
        "dim_pharmacy_master": dim_pharmacy,
        "fact_ship_pharmacy_mastered": fact_mastered,
        "dim_branch": dim_branch,
        "dim_rep": dim_rep,
        "dim_rep_assign": dim_rep_assign,
        "validation_report": validation_report,
    }
    for name, df in artifacts.items():
        write_dual_outputs(df, out, name, include_default=False)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mastering for UID/territory mapping.")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/outputs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--territory-missing-threshold", type=float, default=0.05)
    args = parser.parse_args()
    run_mastering(
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        seed=args.seed,
        territory_missing_threshold=args.territory_missing_threshold,
    )


if __name__ == "__main__":
    main()
