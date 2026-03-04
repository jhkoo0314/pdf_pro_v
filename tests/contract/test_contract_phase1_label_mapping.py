from __future__ import annotations

import pytest

from src.column_labels import COLUMN_LABEL_KO, bilingual_column_name


@pytest.mark.contract
def test_label_mapping_is_one_to_one_non_empty_for_defined_keys():
    assert len(COLUMN_LABEL_KO) > 0
    values = [v for v in COLUMN_LABEL_KO.values() if isinstance(v, str)]
    assert all(v.strip() != "" for v in values)

    for k, v in COLUMN_LABEL_KO.items():
        out = bilingual_column_name(k)
        assert out == f"{k} ({v})"
