"""KPI publish for month/quarter/year from share settlement outputs."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

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


def _data_quality_flag(validation_df: pd.DataFrame) -> str:
    if validation_df.empty:
        return "fail"
    statuses = validation_df["status"].astype(str).str.lower().str.strip()
    return "pass" if (statuses == "pass").all() else "fail"


def _assign_rep_to_ship(share_df: pd.DataFrame, rep_df: pd.DataFrame) -> pd.DataFrame:
    reps = rep_df.copy()
    if "active_flag" in reps.columns:
        reps = reps[reps["active_flag"] == True].copy()
    reps = reps.sort_values(["territory_code", "rep_id"]).reset_index(drop=True)

    by_territory: dict[str, list[tuple[str, str]]] = {}
    for territory, g in reps.groupby("territory_code"):
        by_territory[str(territory)] = [
            (str(r["rep_id"]), str(r["rep_name"])) for _, r in g.iterrows()
        ]

    def pick(row: pd.Series) -> tuple[str, str]:
        territory = str(row.get("territory_code", ""))
        ship_id = str(row.get("ship_id", ""))
        pool = by_territory.get(territory, [])
        if not pool:
            return ("UNASSIGNED", "미배정")
        h = int(hashlib.md5(ship_id.encode("utf-8")).hexdigest()[:8], 16)
        return pool[h % len(pool)]

    out = share_df.copy()
    picked = out.apply(pick, axis=1)
    out["rep_id"] = [x[0] for x in picked]
    out["rep_name"] = [x[1] for x in picked]
    return out


def _build_rep_kpi(base_df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    grp_cols = [period_col, "rep_id", "rep_name", "territory_code", "brand"]
    g = base_df.groupby(grp_cols, dropna=False)

    out = g.agg(
        amount_pre_share=("amount_pre_share", "sum"),
        amount_post_share=("amount_post_share", "sum"),
        ship_count=("ship_id", "count"),
        share_applied_count=("share_applied_flag", "sum"),
        direct_rules_count=("share_rule_source", lambda s: int((s == "direct").sum())),
        extended_rules_count=("share_rule_source", lambda s: int((s == "extended").sum())),
        none_rules_count=("share_rule_source", lambda s: int((s == "none").sum())),
    ).reset_index()
    return out


def _build_kpi_summary(base_df: pd.DataFrame, period_col: str) -> pd.DataFrame:
    g = base_df.groupby([period_col], dropna=False)
    out = g.agg(
        total_pre_share=("amount_pre_share", "sum"),
        total_post_share=("amount_post_share", "sum"),
        share_rules_applied_count=("share_applied_flag", "sum"),
        direct_rules_count=("share_rule_source", lambda s: int((s == "direct").sum())),
        extended_rules_count=("share_rule_source", lambda s: int((s == "extended").sum())),
        none_rules_count=("share_rule_source", lambda s: int((s == "none").sum())),
        row_count=("ship_id", "count"),
    ).reset_index()
    return out


def run_kpi_publish(
    input_dir: str | Path = "data/outputs",
    output_dir: str | Path = "data/outputs",
) -> dict[str, pd.DataFrame]:
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    share = _read_parquet_prefer_label(in_dir, "share_settlement")
    rep = _read_parquet_prefer_label(in_dir, "dim_rep")
    validation = _read_parquet_prefer_label(in_dir, "validation_report")

    data_quality_flag = _data_quality_flag(validation)
    base = _assign_rep_to_ship(share, rep)

    rep_kpi_month = _build_rep_kpi(base, "year_month")
    rep_kpi_quarter = _build_rep_kpi(base, "year_quarter")
    rep_kpi_year = _build_rep_kpi(base, "year")

    kpi_summary_month = _build_kpi_summary(base, "year_month")
    kpi_summary_quarter = _build_kpi_summary(base, "year_quarter")
    kpi_summary_year = _build_kpi_summary(base, "year")

    outputs = {
        "rep_kpi_month": rep_kpi_month,
        "rep_kpi_quarter": rep_kpi_quarter,
        "rep_kpi_year": rep_kpi_year,
        "kpi_summary_month": kpi_summary_month,
        "kpi_summary_quarter": kpi_summary_quarter,
        "kpi_summary_year": kpi_summary_year,
    }

    for name, df in outputs.items():
        out = df.copy()
        out["data_quality_flag"] = data_quality_flag
        write_dual_outputs(out, out_dir, name, include_default=False)
        outputs[name] = out

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish month/quarter/year KPI outputs.")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    args = parser.parse_args()
    run_kpi_publish(input_dir=args.input_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
