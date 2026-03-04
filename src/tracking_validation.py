"""Tracking validation: compare claim-like demand vs shipped amounts."""

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


def _factor_from_key(key: str) -> float:
    digest = hashlib.md5(str(key).encode("utf-8")).hexdigest()
    unit = int(digest[:8], 16) / 0xFFFFFFFF
    return 0.7 + (unit * 0.6)  # 0.7 ~ 1.3


def _quality_flag(coverage: float) -> str:
    if coverage >= 0.90:
        return "good"
    if coverage >= 0.75:
        return "watch"
    return "poor"


def build_tracking_report(mastered_df: pd.DataFrame) -> pd.DataFrame:
    df = mastered_df.copy()

    if "claim_amount" not in df.columns or "claim_qty" not in df.columns:
        keys = df.get("ship_id", pd.Series(range(1, len(df) + 1)))
        factors = keys.astype(str).map(_factor_from_key)
        df["claim_amount"] = (df["amount_ship"].astype(float) * factors).round(2)
        df["claim_qty"] = (df["qty"].astype(float) * factors).round(2)
    else:
        df["claim_amount"] = df["claim_amount"].astype(float).round(2)
        df["claim_qty"] = df["claim_qty"].astype(float).round(2)

    df["tracked_amount"] = df[["amount_ship", "claim_amount"]].min(axis=1)
    df["tracked_qty"] = df[["qty", "claim_qty"]].min(axis=1)

    df["gap_amount"] = (df["claim_amount"] - df["tracked_amount"]).round(2)
    df["gap_qty"] = (df["claim_qty"] - df["tracked_qty"]).round(2)

    df["coverage_ratio"] = (df["tracked_amount"] / df["claim_amount"]).fillna(1.0).round(4)
    df["gap_ratio"] = (df["gap_amount"] / df["claim_amount"]).fillna(0.0).round(4)
    df["tracking_quality_flag"] = df["coverage_ratio"].map(_quality_flag)

    cols = [
        "ship_id",
        "ship_date",
        "year_month",
        "year_quarter",
        "year",
        "territory_code",
        "brand",
        "qty",
        "amount_ship",
        "claim_qty",
        "claim_amount",
        "tracked_qty",
        "tracked_amount",
        "gap_qty",
        "gap_amount",
        "coverage_ratio",
        "gap_ratio",
        "tracking_quality_flag",
    ]
    existing = [c for c in cols if c in df.columns]
    return df[existing].copy()


def validate_tracking_tolerance(
    tracking_report_df: pd.DataFrame, tolerance: float = 1e-6
) -> tuple[bool, float]:
    """Validate arithmetic consistency: claim = tracked + gap."""
    df = tracking_report_df.copy()
    amount_diff = (
        df["claim_amount"].astype(float)
        - (df["tracked_amount"].astype(float) + df["gap_amount"].astype(float))
    ).abs()
    qty_diff = (
        df["claim_qty"].astype(float)
        - (df["tracked_qty"].astype(float) + df["gap_qty"].astype(float))
    ).abs()
    amount_max = float(amount_diff.max()) if len(amount_diff) else 0.0
    qty_max = float(qty_diff.max()) if len(qty_diff) else 0.0
    max_diff = max(amount_max, qty_max)
    return max_diff <= tolerance, max_diff


def build_trace_candidates(
    tracking_report_df: pd.DataFrame, min_coverage: float = 0.75
) -> pd.DataFrame:
    """Convert under-tracked rows to trace input format."""
    df = tracking_report_df.copy()
    cond = (df["coverage_ratio"].astype(float) < min_coverage) | (
        df["tracked_amount"].astype(float) <= 0
    )
    cand = df[cond].copy()
    if cand.empty:
        return pd.DataFrame(
            columns=[
                "case_id",
                "ship_id",
                "year_quarter",
                "territory_code",
                "brand",
                "gap_amount",
                "coverage_ratio",
                "trace_status",
                "trace_reason",
                "created_from",
            ]
        )

    def _case_id(r: pd.Series) -> str:
        raw = f"{r.get('ship_id')}|{r.get('territory_code')}|{r.get('brand')}"
        h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
        return f"TRC_{h}"

    cand["case_id"] = cand.apply(_case_id, axis=1)
    cand["trace_status"] = "Unverified"
    cand["trace_reason"] = cand.apply(
        lambda r: "no_tracking"
        if float(r.get("tracked_amount", 0.0)) <= 0
        else "low_coverage",
        axis=1,
    )
    cand["created_from"] = "tracking_validation"
    return cand[
        [
            "case_id",
            "ship_id",
            "year_quarter",
            "territory_code",
            "brand",
            "gap_amount",
            "coverage_ratio",
            "trace_status",
            "trace_reason",
            "created_from",
        ]
    ].copy()


def run_tracking_validation(
    input_dir: str | Path = "data/outputs",
    output_dir: str | Path = "data/outputs",
    min_coverage: float = 0.75,
) -> pd.DataFrame:
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mastered = _read_parquet_prefer_label(in_dir, "fact_ship_pharmacy_mastered")
    report = build_tracking_report(mastered)
    write_dual_outputs(report, out_dir, "tracking_report", include_default=False)
    trace_df = build_trace_candidates(report, min_coverage=min_coverage)
    write_dual_outputs(
        trace_df, out_dir, "tracking_trace_candidates", include_default=False
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tracking validation.")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    parser.add_argument("--min-coverage", type=float, default=0.75)
    args = parser.parse_args()
    run_tracking_validation(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        min_coverage=args.min_coverage,
    )


if __name__ == "__main__":
    main()
