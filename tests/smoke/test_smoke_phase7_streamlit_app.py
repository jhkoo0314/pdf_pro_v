from __future__ import annotations

import pandas as pd
import pytest

import app.streamlit_app as ui


@pytest.mark.smoke
def test_streamlit_app_module_loads_and_main_exists():
    assert callable(ui.main)


@pytest.mark.smoke
def test_amount_to_thousand_display_conversion_is_integer():
    df = pd.DataFrame(
        [
            {
                "amount_ship": 1234567.0,
                "amount_pre_share": 2000.0,
                "total_post_share": 9876543.0,
                "price_per_pack": 33000.0,
                "discount_rate": 0.1,
            }
        ]
    )
    out = ui._amount_to_thousand(df)
    assert int(out.loc[0, "amount_ship"]) == 1235
    assert int(out.loc[0, "amount_pre_share"]) == 2
    assert int(out.loc[0, "total_post_share"]) == 9877
    assert int(out.loc[0, "price_per_pack"]) == 33
    # Non-money column should stay untouched.
    assert float(out.loc[0, "discount_rate"]) == 0.1
