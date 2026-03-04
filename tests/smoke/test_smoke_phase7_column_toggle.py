from __future__ import annotations

import inspect

import pandas as pd
import pytest

import app.streamlit_app as ui


@pytest.mark.smoke
def test_streamlit_column_toggle_exists_and_canonical_transform_works():
    src = inspect.getsource(ui.main)
    assert "원본 컬럼명(영문) 토글" in src

    df = pd.DataFrame(
        [{"ship_date (출고일)": "2025-01-01", "amount_ship (출고금액)": 1000, "brand (브랜드)": "록소르정"}]
    )
    out = ui._to_canonical_headers(df)
    assert out.columns.tolist() == ["ship_date", "amount_ship", "brand"]
