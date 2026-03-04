"""Synthetic dimension generators with deterministic seed behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import argparse
import random

import pandas as pd

from src.io_utils import write_dual_outputs, write_csv


@dataclass(frozen=True)
class BranchSpec:
    branch_id: str
    territory_code: str
    branch_name: str
    region_group: str
    clinic_reps: int
    hospital_reps: int


BRANCH_SPECS: tuple[BranchSpec, ...] = (
    BranchSpec("BR01", "T01", "서울동부지점", "metro", 9, 8),
    BranchSpec("BR02", "T02", "서울서부지점", "metro", 8, 6),
    BranchSpec("BR03", "T03", "경기북부지점", "capital", 10, 7),
    BranchSpec("BR04", "T04", "경기남부지점", "capital", 5, 3),
    BranchSpec("BR05", "T05", "강원지점", "east", 6, 4),
    BranchSpec("BR06", "T06", "대전충청지점", "central", 6, 5),
    BranchSpec("BR07", "T07", "대구경북지점", "southeast", 7, 5),
    BranchSpec("BR08", "T08", "부산울산지점", "southeast", 4, 3),
    BranchSpec("BR09", "T09", "광주전라지점", "southwest", 3, 2),
    BranchSpec("BR10", "T10", "제주지점", "jeju", 2, 2),
)


LAST_NAMES = [
    "김",
    "이",
    "박",
    "최",
    "정",
    "강",
    "조",
    "윤",
    "장",
    "임",
    "한",
    "오",
    "서",
    "신",
    "권",
    "황",
    "안",
    "송",
    "류",
    "전",
]

GIVEN_NAMES = [
    "민준",
    "서준",
    "도윤",
    "예준",
    "시우",
    "주원",
    "지호",
    "지후",
    "하준",
    "준우",
    "서연",
    "서윤",
    "지우",
    "하은",
    "하윤",
    "민서",
    "지아",
    "채원",
    "윤서",
    "지민",
    "현우",
    "지훈",
    "성민",
    "동현",
    "승현",
    "정우",
    "우진",
    "은우",
    "태윤",
    "건우",
    "수빈",
    "다은",
    "유진",
    "소연",
    "나연",
    "가은",
    "예린",
    "보민",
    "아린",
    "채린",
    "태훈",
    "성호",
    "영수",
    "영희",
    "준호",
    "재훈",
    "미정",
    "현정",
    "유정",
    "혜진",
    "승아",
    "수아",
    "연우",
    "시윤",
    "하랑",
    "주희",
    "민아",
    "은지",
    "재원",
    "정민",
]


def _random_hire_date(rng: random.Random) -> date:
    start = date(2017, 1, 1)
    end = date(2025, 12, 31)
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def _build_name_pool(count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    combos = [f"{ln}{gn}" for ln in LAST_NAMES for gn in GIVEN_NAMES]
    if count > len(combos):
        raise ValueError("Not enough unique Korean name combinations.")
    return rng.sample(combos, count)


def generate_branch_dim(valid_from: str = "2026-01-01") -> pd.DataFrame:
    rows = []
    for spec in BRANCH_SPECS:
        rows.append(
            {
                "branch_id": spec.branch_id,
                "branch_name": spec.branch_name,
                "territory_code": spec.territory_code,
                "region_group": spec.region_group,
                "active_flag": True,
                "valid_from": valid_from,
                "valid_to": None,
            }
        )
    return pd.DataFrame(rows)


def generate_rep_dim(seed: int, valid_from: str = "2026-01-01") -> pd.DataFrame:
    rng = random.Random(seed)
    grades = ["senior", "principal", "lead", "associate"]
    names = _build_name_pool(count=105, seed=seed)

    rows = []
    clinic_seq = 1
    hospital_seq = 1
    clinic_name_idx = 0
    hospital_name_idx = 60

    for spec in BRANCH_SPECS:
        for _ in range(spec.clinic_reps):
            rep_id = f"RC{clinic_seq:03d}"
            rows.append(
                {
                    "rep_id": rep_id,
                    "rep_name": names[clinic_name_idx],
                    "rep_role": "clinic",
                    "branch_id": spec.branch_id,
                    "territory_code": spec.territory_code,
                    "hire_date": _random_hire_date(rng).isoformat(),
                    "grade": rng.choice(grades),
                    "active_flag": True,
                    "valid_from": valid_from,
                    "valid_to": None,
                }
            )
            clinic_seq += 1
            clinic_name_idx += 1

        for _ in range(spec.hospital_reps):
            rep_id = f"RH{hospital_seq:03d}"
            rows.append(
                {
                    "rep_id": rep_id,
                    "rep_name": names[hospital_name_idx],
                    "rep_role": "hospital",
                    "branch_id": spec.branch_id,
                    "territory_code": spec.territory_code,
                    "hire_date": _random_hire_date(rng).isoformat(),
                    "grade": rng.choice(grades),
                    "active_flag": True,
                    "valid_from": valid_from,
                    "valid_to": None,
                }
            )
            hospital_seq += 1
            hospital_name_idx += 1

    return pd.DataFrame(rows)


def generate_rep_assign_dim(rep_df: pd.DataFrame) -> pd.DataFrame:
    return rep_df[["rep_id", "territory_code", "valid_from", "valid_to"]].assign(
        assign_source="seeded_generation"
    )


def build_dimensions(seed: int, valid_from: str = "2026-01-01") -> dict[str, pd.DataFrame]:
    branch_df = generate_branch_dim(valid_from=valid_from)
    rep_df = generate_rep_dim(seed=seed, valid_from=valid_from)
    assign_df = generate_rep_assign_dim(rep_df)
    return {
        "dim_branch": branch_df,
        "dim_rep": rep_df,
        "dim_rep_assign": assign_df,
    }


def save_dimensions(
    dims: dict[str, pd.DataFrame], output_dir: str | Path, fmt: str = "parquet"
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, df in dims.items():
        if fmt == "parquet":
            write_dual_outputs(df, out, name, include_default=False)
        else:
            path = out / f"{name}.csv"
            write_csv(df, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate seeded synthetic dimensions.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--valid-from", default="2026-01-01")
    parser.add_argument("--output-dir", default="data/outputs")
    args = parser.parse_args()

    dims = build_dimensions(seed=args.seed, valid_from=args.valid_from)
    save_dimensions(dims, args.output_dir, fmt="parquet")


if __name__ == "__main__":
    main()
