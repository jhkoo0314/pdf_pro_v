"""Share settlement engine (MVP stage 1: overlap OFF)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from src.io_utils import write_dual_outputs


@dataclass(frozen=True)
class ShareConfig:
    overlap_enabled: bool = False  # MVP stage 1 fixed
    default_ratio_hosp: float = 1.0
    default_ratio_clinic: float = 0.0
    rule_status_required: str = "confirmed"


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


def _prev_quarter(q: str) -> str:
    y, qn = q.split("-Q")
    year = int(y)
    quarter = int(qn)
    if quarter == 1:
        return f"{year - 1}-Q4"
    return f"{year}-Q{quarter - 1}"


def _find_rule_source_and_row(
    rules: pd.DataFrame, year_quarter: str, territory_code: str, brand: str, required_status: str
) -> tuple[str, pd.Series | None]:
    direct = rules[
        (rules["year_quarter"] == year_quarter)
        & (rules["territory_code"] == territory_code)
        & (rules["brand"] == brand)
        & (rules["status"] == required_status)
    ]
    if not direct.empty:
        return "direct", direct.iloc[-1]

    q = year_quarter
    for _ in range(8):
        q = _prev_quarter(q)
        ext = rules[
            (rules["year_quarter"] == q)
            & (rules["territory_code"] == territory_code)
            & (rules["brand"] == brand)
            & (rules["status"] == required_status)
        ]
        if not ext.empty:
            return "extended", ext.iloc[-1]
    return "none", None


def generate_default_rules(base_df: pd.DataFrame) -> pd.DataFrame:
    keys = (
        base_df[["year_quarter", "territory_code", "brand"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    keys["ratio_hosp"] = 0.5
    keys["ratio_clinic"] = 0.5
    keys["version"] = "v1"
    keys["status"] = "confirmed"
    return keys


def redistribute_clinic_pool_by_base_amount(
    clinic_rep_base_df: pd.DataFrame, clinic_pool_amount: float
) -> pd.DataFrame:
    """Redistribute clinic pool by each clinic rep base_amount proportion."""
    if clinic_rep_base_df.empty:
        return clinic_rep_base_df.copy()

    df = clinic_rep_base_df.copy()
    total_base = float(df["base_amount"].astype(float).sum())
    if total_base <= 0:
        df["allocated_amount"] = 0.0
        return df

    df["allocated_amount"] = (
        df["base_amount"].astype(float) / total_base * float(clinic_pool_amount)
    ).round(2)
    return df


def apply_share_settlement(
    base_df: pd.DataFrame,
    rules_df: pd.DataFrame,
    config: ShareConfig = ShareConfig(),
) -> pd.DataFrame:
    df = base_df.copy()
    rules = rules_df.copy()

    if "amount_pre_share" not in df.columns:
        df["amount_pre_share"] = df["amount_ship"].astype(float)

    outputs: list[dict[str, object]] = []
    for _, row in df.iterrows():
        source, rule_row = _find_rule_source_and_row(
            rules,
            str(row["year_quarter"]),
            str(row["territory_code"]),
            str(row["brand"]),
            config.rule_status_required,
        )

        amount_pre = float(row["amount_pre_share"])
        if rule_row is None:
            ratio_hosp = config.default_ratio_hosp
            ratio_clinic = config.default_ratio_clinic
            version = None
            applied = False
        else:
            ratio_hosp = float(rule_row["ratio_hosp"])
            ratio_clinic = float(rule_row["ratio_clinic"])
            version = str(rule_row["version"])
            applied = True

        # MVP stage 1: no overlap generation and simple interpretation only.
        overlap_generated_flag = False
        amount_hosp_share = round(amount_pre * ratio_hosp, 2)
        amount_clinic_share = round(amount_pre * ratio_clinic, 2)
        amount_post = round(amount_hosp_share + amount_clinic_share, 2)

        out = row.to_dict()
        out["ratio_hosp"] = ratio_hosp
        out["ratio_clinic"] = ratio_clinic
        out["amount_hosp_share"] = amount_hosp_share
        out["amount_clinic_share"] = amount_clinic_share
        out["amount_post_share"] = amount_post
        out["overlap_generated_flag"] = overlap_generated_flag
        out["share_applied_flag"] = bool(applied)
        out["share_rule_version"] = version
        out["share_rule_source"] = source
        outputs.append(out)

    return pd.DataFrame(outputs)


def run_share_settlement(
    input_dir: str | Path = "data/outputs",
    output_dir: str | Path = "data/outputs",
    rules_base_name: str = "share_rules",
    config: ShareConfig = ShareConfig(),
) -> pd.DataFrame:
    in_dir = Path(input_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = _read_parquet_prefer_label(in_dir, "tracking_report")

    rules_path = in_dir / f"{rules_base_name}_label.parquet"
    if rules_path.exists():
        rules = _to_canonical_columns(pd.read_parquet(rules_path))
    else:
        rules = generate_default_rules(base)
        write_dual_outputs(rules, out_dir, rules_base_name, include_default=False)

    settled = apply_share_settlement(base, rules, config=config)
    write_dual_outputs(settled, out_dir, "share_settlement", include_default=False)
    return settled


def main() -> None:
    parser = argparse.ArgumentParser(description="Run share settlement (MVP stage 1).")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    parser.add_argument("--rules-base-name", default="share_rules")
    args = parser.parse_args()

    run_share_settlement(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        rules_base_name=args.rules_base_name,
        config=ShareConfig(overlap_enabled=False),
    )


if __name__ == "__main__":
    main()
