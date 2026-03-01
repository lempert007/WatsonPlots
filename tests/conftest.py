import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def time_df():
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "date": dates,
        "revenue": rng.normal(1000, 100, 30),
        "cost": rng.normal(600, 80, 30),
        "region": ["North", "South"] * 15,
    })


@pytest.fixture
def numeric_df():
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "x": rng.normal(0, 1, 100),
        "y": rng.normal(0, 1, 100),
        "size_col": rng.uniform(5, 50, 100),
        "category": ["A", "B", "C", "D"] * 25,
    })


@pytest.fixture
def dist_df():
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "value": np.concatenate([rng.normal(10, 2, 100), rng.normal(15, 3, 100)]),
        "group": ["Low"] * 100 + ["High"] * 100,
    })
