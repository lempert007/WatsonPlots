import numpy as np
import pandas as pd
import pytest

import watsonplots as wp


@pytest.fixture
def chart(time_df):
    return wp.line(time_df, x="date", y="revenue")


@pytest.fixture
def time_df():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "date": dates,
            "revenue": rng.normal(1000, 100, 30),
            "cost": rng.normal(600, 80, 30),
            "region": ["North", "South"] * 15,
        }
    )
