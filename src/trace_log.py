"""Trace log builder and state transition engine."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import re
from pathlib import Path

import pandas as pd

from src.io_utils import write_dual_outputs


ALLOWED_STATUS = {"Unverified", "Inquired", "Confirmed", "Rejected"}
ALLOWED_TRANSITIONS = {
    "Unverified": {"Inquired"},
    "Inquired": {"Confirmed", "Rejected"},
    "Confirmed": set(),
    "Rejected": set(),
}


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


def can_transition(from_status: str, to_status: str) -> bool:
    if from_status not in ALLOWED_STATUS or to_status not in ALLOWED_STATUS:
        return False
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def build_initial_trace_log(trace_candidates_df: pd.DataFrame) -> pd.DataFrame:
    if trace_candidates_df.empty:
        return pd.DataFrame(
            columns=[
                "case_id",
                "ship_id",
                "year_quarter",
                "territory_code",
                "brand",
                "trace_status",
                "trace_reason",
                "note",
                "updated_by",
                "updated_at",
                "created_from",
            ]
        )
    out = trace_candidates_df.copy()
    out["trace_status"] = out.get("trace_status", "Unverified")
    out["note"] = ""
    out["updated_by"] = "system"
    out["updated_at"] = datetime.now(timezone.utc).isoformat()
    return out[
        [
            "case_id",
            "ship_id",
            "year_quarter",
            "territory_code",
            "brand",
            "trace_status",
            "trace_reason",
            "note",
            "updated_by",
            "updated_at",
            "created_from",
        ]
    ].copy()


def apply_trace_actions(trace_log_df: pd.DataFrame, actions_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    log = trace_log_df.copy()
    history_rows: list[dict[str, object]] = []
    if actions_df.empty:
        return log, pd.DataFrame(columns=["case_id", "from_status", "to_status", "updated_by", "updated_at", "note", "result"])

    now = datetime.now(timezone.utc).isoformat()
    for _, act in actions_df.iterrows():
        case_id = str(act.get("case_id", "")).strip()
        to_status = str(act.get("to_status", "")).strip()
        note = str(act.get("note", "") or "")
        updated_by = str(act.get("updated_by", "operator"))
        updated_at = str(act.get("updated_at", now))

        idx = log.index[log["case_id"].astype(str) == case_id]
        if len(idx) == 0:
            history_rows.append(
                {
                    "case_id": case_id,
                    "from_status": None,
                    "to_status": to_status,
                    "updated_by": updated_by,
                    "updated_at": updated_at,
                    "note": note,
                    "result": "case_not_found",
                }
            )
            continue

        i = idx[0]
        from_status = str(log.at[i, "trace_status"])
        if can_transition(from_status, to_status):
            log.at[i, "trace_status"] = to_status
            log.at[i, "note"] = note
            log.at[i, "updated_by"] = updated_by
            log.at[i, "updated_at"] = updated_at
            result = "applied"
        else:
            result = "invalid_transition"

        history_rows.append(
            {
                "case_id": case_id,
                "from_status": from_status,
                "to_status": to_status,
                "updated_by": updated_by,
                "updated_at": updated_at,
                "note": note,
                "result": result,
            }
        )

    return log, pd.DataFrame(history_rows)


def run_trace_log(
    input_dir: str | Path = "data/outputs",
    output_dir: str | Path = "data/outputs",
    actions_base_name: str = "trace_actions",
) -> dict[str, pd.DataFrame]:
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = _read_parquet_prefer_label(in_dir, "tracking_trace_candidates")
    trace_log = build_initial_trace_log(candidates)

    actions = _read_parquet_prefer_label(in_dir, actions_base_name)
    trace_log_after, trace_history = apply_trace_actions(trace_log, actions)

    write_dual_outputs(trace_log_after, out_dir, "trace_log", include_default=False)
    write_dual_outputs(trace_history, out_dir, "trace_history", include_default=False)
    return {"trace_log": trace_log_after, "trace_history": trace_history}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build trace log and apply state transitions.")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    parser.add_argument("--actions-base-name", default="trace_actions")
    args = parser.parse_args()
    run_trace_log(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        actions_base_name=args.actions_base_name,
    )


if __name__ == "__main__":
    main()
