"""Validation report builder with structured issue rows and quality flags."""

from __future__ import annotations

import argparse
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
    return pd.DataFrame()


def _make_issue_row(
    issue_type: str,
    severity: str,
    metric_value: float,
    threshold: float,
    note: str,
    year_quarter: str | None = None,
) -> dict[str, object]:
    status = "pass" if metric_value <= threshold else ("warn" if severity != "high" else "fail")
    return {
        "rule_name": f"{issue_type}_count",
        "metric_value": float(metric_value),
        "threshold": float(threshold),
        "status": status,
        "note": note,
        "issue_type": issue_type,
        "severity": severity,
        "entity_id": None,
        "year_quarter": year_quarter,
        "details": note,
    }


def build_validation_report(
    share_df: pd.DataFrame,
    trace_candidates_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if share_df.empty:
        rows.append(
            _make_issue_row(
                issue_type="EMPTY_INPUT",
                severity="high",
                metric_value=1,
                threshold=0,
                note="share_settlement is empty",
            )
        )
        return pd.DataFrame(rows)

    unmapped = int((share_df.get("mapping_quality_flag", pd.Series(dtype=object)) == "UNMAPPED").sum())
    rows.append(
        _make_issue_row(
            issue_type="UNMAPPED_PHARMACY",
            severity="high",
            metric_value=unmapped,
            threshold=0,
            note=f"unmapped pharmacy rows={unmapped}",
        )
    )

    no_territory = int(share_df.get("territory_code", pd.Series(dtype=object)).isna().sum())
    rows.append(
        _make_issue_row(
            issue_type="NO_TERRITORY",
            severity="high",
            metric_value=no_territory,
            threshold=0,
            note=f"territory missing rows={no_territory}",
        )
    )

    low_coverage = int((share_df.get("coverage_ratio", pd.Series(dtype=float)).astype(float) < 0.75).sum())
    rows.append(
        _make_issue_row(
            issue_type="LOW_COVERAGE",
            severity="med",
            metric_value=low_coverage,
            threshold=max(1, int(len(share_df) * 0.2)),
            note=f"coverage < 0.75 rows={low_coverage}",
        )
    )

    rule_none = int((share_df.get("share_rule_source", pd.Series(dtype=object)) == "none").sum())
    rows.append(
        _make_issue_row(
            issue_type="RULE_MISSING",
            severity="high",
            metric_value=rule_none,
            threshold=0,
            note=f"share_rule_source=none rows={rule_none}",
        )
    )

    rule_extended = int((share_df.get("share_rule_source", pd.Series(dtype=object)) == "extended").sum())
    rows.append(
        _make_issue_row(
            issue_type="RULE_EXTENDED",
            severity="low",
            metric_value=rule_extended,
            threshold=max(1, int(len(share_df) * 0.3)),
            note=f"share_rule_source=extended rows={rule_extended}",
        )
    )

    trace_open = int(len(trace_candidates_df))
    rows.append(
        _make_issue_row(
            issue_type="TRACE_OPEN_CASE",
            severity="med",
            metric_value=trace_open,
            threshold=max(1, int(len(share_df) * 0.2)),
            note=f"open trace candidates rows={trace_open}",
        )
    )

    return pd.DataFrame(rows)


def build_data_quality_flag(validation_report_df: pd.DataFrame) -> pd.DataFrame:
    df = validation_report_df.copy()
    if df.empty:
        return pd.DataFrame(
            [{"year_quarter": "ALL", "issue_count_total": 0, "issue_count_high": 0, "data_quality_flag": "fail"}]
        )
    issue_total = int((df["status"] != "pass").sum())
    issue_high = int(((df["status"] == "fail") | (df["severity"] == "high") & (df["status"] != "pass")).sum())
    flag = "pass" if issue_total == 0 else "fail"
    return pd.DataFrame(
        [
            {
                "year_quarter": "ALL",
                "issue_count_total": issue_total,
                "issue_count_high": issue_high,
                "data_quality_flag": flag,
            }
        ]
    )


def run_validation(
    input_dir: str | Path = "data/outputs",
    output_dir: str | Path = "data/outputs",
) -> dict[str, pd.DataFrame]:
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    share = _read_parquet_prefer_label(in_dir, "share_settlement")
    trace_candidates = _read_parquet_prefer_label(in_dir, "tracking_trace_candidates")

    validation_report = build_validation_report(share, trace_candidates)
    quality_flag = build_data_quality_flag(validation_report)

    write_dual_outputs(validation_report, out_dir, "validation_report", include_default=False)
    write_dual_outputs(quality_flag, out_dir, "data_quality_flag", include_default=False)
    return {"validation_report": validation_report, "data_quality_flag": quality_flag}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build structured validation report.")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    args = parser.parse_args()
    run_validation(input_dir=args.input_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
