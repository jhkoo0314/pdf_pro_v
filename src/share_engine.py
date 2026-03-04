"""Share settlement engine (MVP stage 2 bootstrap: overlap ON/OFF)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

import pandas as pd

from src.io_utils import write_dual_outputs


@dataclass(frozen=True)
class ShareConfig:
    overlap_enabled: bool = False
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
    rules: pd.DataFrame,
    year_quarter: str,
    territory_code: str,
    brand: str,
    participant_type: str,
    required_status: str,
    overlap_enabled: bool,
) -> tuple[str, pd.Series | None]:
    def _scope_match(df: pd.DataFrame) -> pd.DataFrame:
        if not overlap_enabled:
            return df
        if participant_type == "hosp":
            allowed = {"hosp_only", "mixed"}
        elif participant_type == "clinic":
            allowed = {"clinic_only", "mixed"}
        else:
            allowed = {"mixed"}
        return df[df["participant_scope"].isin(allowed)]

    def _pick(df: pd.DataFrame) -> pd.Series | None:
        if df.empty:
            return None
        picked = df.sort_values(["priority", "version"], ascending=[False, False]).iloc[0]
        return picked

    direct = _scope_match(rules[
        (rules["year_quarter"] == year_quarter)
        & (rules["territory_code"] == territory_code)
        & (rules["brand"] == brand)
        & (rules["status"] == required_status)
    ])
    picked_direct = _pick(direct)
    if picked_direct is not None:
        return "direct", picked_direct

    q = year_quarter
    for _ in range(8):
        q = _prev_quarter(q)
        ext = _scope_match(rules[
            (rules["year_quarter"] == q)
            & (rules["territory_code"] == territory_code)
            & (rules["brand"] == brand)
            & (rules["status"] == required_status)
        ])
        picked_ext = _pick(ext)
        if picked_ext is not None:
            return "extended", picked_ext
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
    keys["overlap_mode"] = "none"
    keys["participant_scope"] = "mixed"
    keys["priority"] = 100
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


def _redistribute_with_rounding_correction(
    clinic_rep_base_df: pd.DataFrame, clinic_pool_amount: float
) -> tuple[pd.DataFrame, float]:
    """Allocate clinic pool with deterministic residual correction to preserve totals."""
    if clinic_rep_base_df.empty:
        out = clinic_rep_base_df.copy()
        out["allocated_amount"] = 0.0
        return out, 0.0

    df = clinic_rep_base_df.copy()
    total_base = float(df["base_amount"].astype(float).sum())
    if total_base <= 0:
        df["allocated_amount"] = 0.0
        return df, 0.0

    exact = df["base_amount"].astype(float) / total_base * float(clinic_pool_amount)
    rounded = exact.round(2)
    residual = round(float(clinic_pool_amount) - float(rounded.sum()), 2)
    if abs(residual) > 0:
        idx = df["base_amount"].astype(float).idxmax()
        rounded.loc[idx] = round(float(rounded.loc[idx]) + residual, 2)

    df["allocated_amount"] = rounded
    return df, residual


def _row_hash(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest()[:8], 16)


def _resolve_participant_type(row: pd.Series, overlap_enabled: bool) -> str:
    manual = str(row.get("overlap_participant_type", "")).strip().lower()
    if manual in {"hosp", "clinic", "mixed"}:
        return manual
    if not overlap_enabled:
        return "mixed"
    h = _row_hash(str(row.get("ship_id", ""))) % 100
    if h < 35:
        return "hosp"
    if h < 70:
        return "clinic"
    return "mixed"


def _build_overlap_group_id(row: pd.Series, overlap_enabled: bool) -> str | None:
    if not overlap_enabled:
        return None
    yq = str(row.get("year_quarter", ""))
    territory = str(row.get("territory_code", ""))
    brand = str(row.get("brand", ""))
    key = f"{row.get('ship_id', '')}|{row.get('pharmacy_uid', '')}|{territory}|{brand}"
    bucket = (_row_hash(str(key)) % 5) + 1
    return f"OG_{yq}_{territory}_{brand}_{bucket:02d}"


def build_share_overlap_audit(settled_df: pd.DataFrame) -> pd.DataFrame:
    if settled_df.empty:
        return pd.DataFrame(
            columns=[
                "year_quarter",
                "territory_code",
                "brand",
                "overlap_group_id",
                "participant_count",
                "participant_type_set",
                "pool_amount_pre_share",
                "pool_amount_post_share",
                "pool_amount_hosp_share",
                "pool_amount_clinic_share",
                "rounding_delta_sum",
                "overlap_generated_rows",
                "share_rule_source_set",
                "conservation_gap",
            ]
        )

    grp = (
        settled_df.groupby(
            ["year_quarter", "territory_code", "brand", "overlap_group_id"],
            dropna=False,
        )
        .agg(
            participant_count=("ship_id", "count"),
            pool_amount_pre_share=("amount_pre_share", "sum"),
            pool_amount_post_share=("amount_post_share", "sum"),
            pool_amount_hosp_share=("amount_hosp_share", "sum"),
            pool_amount_clinic_share=("amount_clinic_share", "sum"),
            rounding_delta_sum=("allocation_rounding_delta", "sum"),
            overlap_generated_rows=("overlap_generated_flag", "sum"),
        )
        .reset_index()
    )

    type_set = (
        settled_df.groupby(
            ["year_quarter", "territory_code", "brand", "overlap_group_id"],
            dropna=False,
        )["overlap_participant_type"]
        .apply(lambda s: ",".join(sorted(set(s.astype(str)))))
        .reset_index(name="participant_type_set")
    )
    source_set = (
        settled_df.groupby(
            ["year_quarter", "territory_code", "brand", "overlap_group_id"],
            dropna=False,
        )["share_rule_source"]
        .apply(lambda s: ",".join(sorted(set(s.astype(str)))))
        .reset_index(name="share_rule_source_set")
    )

    out = grp.merge(type_set, on=["year_quarter", "territory_code", "brand", "overlap_group_id"], how="left")
    out = out.merge(source_set, on=["year_quarter", "territory_code", "brand", "overlap_group_id"], how="left")
    out["conservation_gap"] = (out["pool_amount_pre_share"] - out["pool_amount_post_share"]).round(2)
    return out


def apply_share_settlement(
    base_df: pd.DataFrame,
    rules_df: pd.DataFrame,
    config: ShareConfig = ShareConfig(),
) -> pd.DataFrame:
    df = base_df.copy()
    rules = rules_df.copy()
    if "overlap_mode" not in rules.columns:
        rules["overlap_mode"] = "none"
    if "participant_scope" not in rules.columns:
        rules["participant_scope"] = "mixed"
    if "priority" not in rules.columns:
        rules["priority"] = 100

    if "amount_pre_share" not in df.columns:
        df["amount_pre_share"] = df["amount_ship"].astype(float)

    outputs: list[dict[str, object]] = []
    for _, row in df.iterrows():
        participant_type = _resolve_participant_type(row, config.overlap_enabled)
        overlap_group_id = _build_overlap_group_id(row, config.overlap_enabled)
        source, rule_row = _find_rule_source_and_row(
            rules,
            str(row["year_quarter"]),
            str(row["territory_code"]),
            str(row["brand"]),
            participant_type,
            config.rule_status_required,
            config.overlap_enabled,
        )

        amount_pre = float(row["amount_pre_share"])
        if rule_row is None:
            ratio_hosp = config.default_ratio_hosp
            ratio_clinic = config.default_ratio_clinic
            version = None
            applied = False
            overlap_mode = "none"
            priority = None
        else:
            ratio_hosp = float(rule_row["ratio_hosp"])
            ratio_clinic = float(rule_row["ratio_clinic"])
            version = str(rule_row["version"])
            applied = True
            overlap_mode = str(rule_row.get("overlap_mode", "none"))
            priority = int(rule_row.get("priority", 100))

        overlap_generated_flag = bool(config.overlap_enabled and participant_type == "mixed")
        amount_hosp_share = round(amount_pre * ratio_hosp, 2)
        amount_clinic_share = round(amount_pre * ratio_clinic, 2)
        allocation_rounding_delta = 0.0
        if config.overlap_enabled and amount_clinic_share > 0:
            row_key = str(row.get("ship_id", ""))
            rep_count = 2 + (_row_hash(row_key) % 3)
            bases = [float(((_row_hash(f"{row_key}|{i}") % 100) + 1)) for i in range(rep_count)]
            alloc_df = pd.DataFrame({"rep_id": [f"R{i+1}" for i in range(rep_count)], "base_amount": bases})
            _, allocation_rounding_delta = _redistribute_with_rounding_correction(
                alloc_df, clinic_pool_amount=amount_clinic_share
            )
        amount_post = round(amount_hosp_share + amount_clinic_share, 2)
        rule_match_key = (
            f"{row.get('year_quarter')}|{row.get('territory_code')}|{row.get('brand')}|{participant_type}"
        )
        if source == "none":
            rule_resolution_path = "none"
        elif config.overlap_enabled and overlap_generated_flag and overlap_mode != "none":
            rule_resolution_path = "overlap_resolved"
        else:
            rule_resolution_path = source

        out = row.to_dict()
        out["ratio_hosp"] = ratio_hosp
        out["ratio_clinic"] = ratio_clinic
        out["amount_hosp_share"] = amount_hosp_share
        out["amount_clinic_share"] = amount_clinic_share
        out["amount_post_share"] = amount_post
        out["overlap_generated_flag"] = overlap_generated_flag
        out["overlap_participant_type"] = participant_type
        out["overlap_group_id"] = overlap_group_id
        out["share_applied_flag"] = bool(applied)
        out["share_rule_version"] = version
        out["share_rule_source"] = source
        out["rule_match_key"] = rule_match_key
        out["rule_resolution_path"] = rule_resolution_path
        out["allocation_rounding_delta"] = float(allocation_rounding_delta)
        out["share_rule_priority"] = priority
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
    overlap_audit = build_share_overlap_audit(settled)
    write_dual_outputs(settled, out_dir, "share_settlement", include_default=False)
    write_dual_outputs(overlap_audit, out_dir, "share_overlap_audit", include_default=False)
    return settled


def main() -> None:
    parser = argparse.ArgumentParser(description="Run share settlement (MVP stage 2 bootstrap).")
    parser.add_argument("--input-dir", default="data/outputs")
    parser.add_argument("--output-dir", default="data/outputs")
    parser.add_argument("--rules-base-name", default="share_rules")
    parser.add_argument("--overlap-enabled", action="store_true")
    args = parser.parse_args()

    run_share_settlement(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        rules_base_name=args.rules_base_name,
        config=ShareConfig(overlap_enabled=bool(args.overlap_enabled)),
    )


if __name__ == "__main__":
    main()
