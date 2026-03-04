import pandas as pd
import pytest

from src.generate_synth import build_dimensions
from src.mastering import (
    build_pharmacy_uid_map,
    make_pharmacy_key,
    territory_from_pharmacy_uid,
)


@pytest.mark.unit
def test_uid_generation_rule_is_deterministic_and_unique():
    ref = pd.DataFrame(
        [
            {
                "pharmacy_name": "A약국",
                "pharmacy_addr": "서울시 A로 1",
                "pharmacy_tel": "02-1111-1111",
                "pharmacy_provider_id": "X1",
                "source_file": "s.xlsx",
                "source_row_id": "1",
            },
            {
                "pharmacy_name": "A약국",
                "pharmacy_addr": "서울시 A로 1",
                "pharmacy_tel": "02-1111-1111",
                "pharmacy_provider_id": "X2",
                "source_file": "s.xlsx",
                "source_row_id": "2",
            },
            {
                "pharmacy_name": "B약국",
                "pharmacy_addr": "부산시 B로 2",
                "pharmacy_tel": "051-222-2222",
                "pharmacy_provider_id": "Y1",
                "source_file": "s.xlsx",
                "source_row_id": "3",
            },
        ]
    )
    uid_map = build_pharmacy_uid_map(ref)
    assert uid_map["pharmacy_uid"].nunique() == 2
    assert uid_map["pharmacy_uid"].str.match(r"^P\d{6}$").all()

    key1 = make_pharmacy_key("A약국", "서울시 A로 1", "02-1111-1111")
    key2 = make_pharmacy_key("A약국", "서울시 A로 1", "02-1111-1111")
    assert key1 == key2


@pytest.mark.unit
def test_territory_mapping_rule_output_range():
    values = {territory_from_pharmacy_uid(f"P{i:06d}") for i in range(1, 101)}
    assert all(v.startswith("T") for v in values)
    assert all(len(v) == 3 for v in values)
    assert values.issubset({f"T{i:02d}" for i in range(1, 11)})


@pytest.mark.unit
def test_branch_and_rep_names_are_korean():
    dims = build_dimensions(seed=42)
    branch = dims["dim_branch"]
    rep = dims["dim_rep"]

    assert branch["branch_name"].str.contains(r"[가-힣]").all()
    assert rep["rep_name"].str.contains(r"[가-힣]").all()
