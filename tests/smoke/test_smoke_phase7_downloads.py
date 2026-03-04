from __future__ import annotations

import pandas as pd
import pytest

import app.streamlit_app as ui


@pytest.mark.smoke
def test_download_helpers_generate_csv_and_xlsx_bytes():
    df = pd.DataFrame(
        [
            {"year_month": "2025-01", "amount_ship": 1000, "brand": "록소르정"},
            {"year_month": "2025-02", "amount_ship": 2000, "brand": "자누비아정"},
        ]
    )

    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    xlsx_bytes = ui._download_xlsx_bytes(df)

    # CSV BOM prefix for utf-8-sig
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    # XLSX is a zip container and should start with PK signature.
    assert xlsx_bytes[:2] == b"PK"
    assert len(xlsx_bytes) > 100
