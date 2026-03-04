"""Ingest source files and build normalized merge-ready raw datasets."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import re

import pandas as pd

from src.io_utils import write_dual_outputs


HOSPITAL_FILE_GLOB = "1.*.xlsx"
PHARMACY_FILE_GLOB = "2.*.xlsx"
WHOLESALER_FILE_GLOB = "*.csv"

PROVIDER_ALLOWED_TYPES = {"의원", "병원", "종합병원", "상급종합병원"}
PHARMACY_REQUIRED_TYPE = "약국"


def _canonical_col(name: str) -> str:
    m = re.match(r"^([a-z0-9_]+)\(", str(name))
    return m.group(1) if m else str(name).strip()


def _find_one(raw_dir: Path, pattern: str) -> Path:
    files = sorted(raw_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file matched pattern: {pattern} in {raw_dir}")
    return files[0]


def _attach_lineage(df: pd.DataFrame, source_file: str, source_sheet: str | None) -> pd.DataFrame:
    out = df.copy()
    out["source_file"] = source_file
    out["source_sheet"] = source_sheet
    out["source_row_id"] = (out.index + 1).astype(str)
    return out


def _load_provider_ref(raw_dir: Path) -> pd.DataFrame:
    path = _find_one(raw_dir, HOSPITAL_FILE_GLOB)
    sheet = "hospBasisList"
    df = pd.read_excel(path, sheet_name=sheet)
    df = df.rename(columns={c: _canonical_col(c) for c in df.columns})

    required = [
        "provider_id",
        "provider_name",
        "provider_type_code",
        "provider_type_name",
        "provider_addr",
        "provider_tel",
        "coord_x",
        "coord_y",
        "opened_date",
    ]
    optional = [
        "sido_code",
        "sido_name",
        "sigungu_code",
        "sigungu_name",
        "eup_myeon_dong",
        "zip_code",
    ]
    cols = required + [c for c in optional if c in df.columns]
    out = df[cols].copy()
    out = out[out["provider_type_name"].isin(PROVIDER_ALLOWED_TYPES)].reset_index(drop=True)
    return _attach_lineage(out, path.name, sheet)


def _load_pharmacy_ref(raw_dir: Path) -> pd.DataFrame:
    path = _find_one(raw_dir, PHARMACY_FILE_GLOB)
    sheet = "parmacyBasisList"
    df = pd.read_excel(path, sheet_name=sheet)
    df = df.rename(columns={c: _canonical_col(c) for c in df.columns})

    required = [
        "pharmacy_provider_id",
        "pharmacy_name",
        "pharmacy_type_code",
        "pharmacy_type_name",
        "pharmacy_addr",
        "pharmacy_tel",
        "pharmacy_coord_x",
        "pharmacy_coord_y",
        "pharmacy_opened_date",
    ]
    optional = [
        "sido_code",
        "sido_name",
        "sigungu_code",
        "sigungu_name",
        "eup_myeon_dong",
        "zip_code",
    ]
    cols = required + [c for c in optional if c in df.columns]
    out = df[cols].copy()
    out = out[out["pharmacy_type_name"] == PHARMACY_REQUIRED_TYPE].reset_index(drop=True)
    return _attach_lineage(out, path.name, sheet)


def _load_wholesaler_ref(raw_dir: Path) -> pd.DataFrame:
    files = sorted(p for p in raw_dir.glob(WHOLESALER_FILE_GLOB) if "도매" in p.name)
    if not files:
        files = sorted(raw_dir.glob(WHOLESALER_FILE_GLOB))
    if not files:
        raise FileNotFoundError(f"No csv source in {raw_dir}")
    path = files[0]

    df = pd.read_csv(path, encoding="utf-8")
    df = df.rename(columns={c: _canonical_col(c) for c in df.columns})

    required = [
        "facility_name",
        "business_type",
        "road_address",
        "jibun_address",
        "phone",
        "latitude",
        "longitude",
        "business_status",
        "as_of_date",
        "provider_org_code",
        "provider_org_name",
    ]
    optional = ["has_transport_vehicle", "has_storage_facility", "supervising_agency"]
    cols = required + [c for c in optional if c in df.columns]
    out = df[cols].copy()
    out = out.rename(
        columns={
            "facility_name": "wholesaler_name",
            "business_type": "biz_type",
            "road_address": "wholesaler_addr_road",
            "jibun_address": "wholesaler_addr_jibun",
            "phone": "wholesaler_tel",
            "latitude": "lat",
            "longitude": "lon",
        }
    )
    out["active_flag"] = out["business_status"].fillna("").str.contains("영업", na=False)
    out["is_valid_wholesaler"] = out["biz_type"].fillna("").str.contains("의약품", na=False)
    out = out.reset_index(drop=True)
    out["wholesaler_id"] = [f"W{i:05d}" for i in range(1, len(out) + 1)]
    return _attach_lineage(out, path.name, None)


def _to_year_quarter(dt: pd.Timestamp) -> str:
    q = ((dt.month - 1) // 3) + 1
    return f"{dt.year}-Q{q}"


def build_fact_ship_pharmacy_raw(
    ref_pharmacy: pd.DataFrame, ref_wholesaler: pd.DataFrame, seed: int
) -> pd.DataFrame:
    rng = random.Random(seed)
    brands = ["brand_a", "brand_b", "brand_c"]

    wholes = ref_wholesaler[
        (ref_wholesaler["active_flag"] == True) & (ref_wholesaler["is_valid_wholesaler"] == True)
    ].copy()
    if wholes.empty:
        wholes = ref_wholesaler.copy()

    rows = []
    ship_seq = 1
    for _, p in ref_pharmacy.iterrows():
        n_rows = rng.randint(1, 2)
        for _ in range(n_rows):
            w = wholes.iloc[rng.randrange(len(wholes))]
            ship_date = pd.Timestamp(2025, rng.randint(1, 12), rng.randint(1, 28))
            qty = rng.randint(5, 200)
            amount_ship = float(qty * rng.randint(9000, 30000))
            amount_supply = float(round(amount_ship * 0.9, 2))
            rows.append(
                {
                    "ship_id": f"S{ship_seq:08d}",
                    "ship_date": ship_date.date().isoformat(),
                    "year_month": ship_date.strftime("%Y-%m"),
                    "year_quarter": _to_year_quarter(ship_date),
                    "year": int(ship_date.year),
                    "wholesaler_id": w["wholesaler_id"],
                    "wholesaler_name": w["wholesaler_name"],
                    "wholesaler_raw_name": w["wholesaler_name"],
                    "pharmacy_name": p["pharmacy_name"],
                    "pharmacy_addr": p["pharmacy_addr"],
                    "pharmacy_tel": p["pharmacy_tel"],
                    "pharmacy_account_id": None,
                    "brand": rng.choice(brands),
                    "sku": None,
                    "qty": qty,
                    "amount_ship": amount_ship,
                    "amount_supply": amount_supply,
                    "amount_pre_share": amount_ship,
                    "amount_post_share": amount_ship,
                    "data_source": "hybrid_simulated",
                }
            )
            ship_seq += 1

    return pd.DataFrame(rows)


def run_ingest_merge(raw_dir: str | Path = "data/raw", output_dir: str | Path = "data/raw", seed: int = 42) -> dict[str, pd.DataFrame]:
    raw = Path(raw_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ref_provider = _load_provider_ref(raw)
    ref_pharmacy = _load_pharmacy_ref(raw)
    ref_wholesaler = _load_wholesaler_ref(raw)
    fact_raw = build_fact_ship_pharmacy_raw(ref_pharmacy, ref_wholesaler, seed=seed)

    artifacts = {
        "ref_provider_address": ref_provider,
        "ref_pharmacy_address": ref_pharmacy,
        "ref_wholesaler_master": ref_wholesaler,
        "fact_ship_pharmacy_raw": fact_raw,
    }
    for name, df in artifacts.items():
        write_dual_outputs(df, out, name, include_default=False)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest source files and build merge-ready raw.")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_ingest_merge(raw_dir=args.raw_dir, output_dir=args.output_dir, seed=args.seed)


if __name__ == "__main__":
    main()
