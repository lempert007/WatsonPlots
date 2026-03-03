import numpy as np
import pandas as pd
import pytest

import watsonplots as wp
from watsonplots.exceptions import (
    ColumnNotFoundError,
    ConstantColumnError,
    TimeParseError,
)

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f+00:00"


def _make_logs(lag_seconds: float = 5.0, length: int = 200, seed: int = 42):
    random_generator = np.random.default_rng(seed)
    lag_at_500ms = round(lag_seconds / 0.5)

    mock_voltage_values = np.cumsum(random_generator.normal(0, 1, length + lag_at_500ms))

    t1 = pd.date_range("2024-01-01 00:00:00", periods=length, freq="500ms", tz="UTC")
    t2 = t1 + pd.Timedelta(seconds=lag_seconds)

    df1 = pd.DataFrame({"time": t1.strftime(TIME_FORMAT), "voltage": mock_voltage_values[:length]})
    # df2 observes the physical signal lag_at_500ms samples later, reported at t2
    df2 = pd.DataFrame(
        {
            "time": t2.strftime(TIME_FORMAT),
            "voltage": mock_voltage_values[lag_at_500ms : lag_at_500ms + length],
        }
    )
    return df1, df2


def test_sync_preserves_row_counts():
    df1, df2 = _make_logs()
    out1, out2 = wp.sync(df1, df2, common_columns="voltage", time1="time", time2="time")
    assert len(out1) == len(df1)
    assert len(out2) == len(df2)


def test_sync_other_columns_untouched():
    df1, df2 = _make_logs()
    df1["extra"] = 99
    out1, _ = wp.sync(df1, df2, common_columns="voltage", time1="time", time2="time")
    assert (out1["extra"] == 99).all()


def test_sync_timezone_mismatch_does_not_crash():
    df1, df2 = _make_logs(lag_seconds=5.0)

    df2["time"] = (pd.to_datetime(df2["time"], utc=True) + pd.Timedelta(hours=5)).dt.strftime(
        TIME_FORMAT
    )
    out1, out2 = wp.sync(df1, df2, common_columns="voltage", time1="time", time2="time")
    assert len(out1) == len(df1)
    assert len(out2) == len(df2)


def test_sync_missing_time_col():
    df1, df2 = _make_logs()
    with pytest.raises(ColumnNotFoundError):
        wp.sync(df1, df2, common_columns="voltage", time1="bad", time2="time")


def test_sync_constant_column_raises():
    df1, df2 = _make_logs()
    df1["voltage"] = 5.0
    with pytest.raises(ConstantColumnError, match="constant"):
        wp.sync(df1, df2, common_columns="voltage", time1="time", time2="time")


def test_sync_bad_time_format_raises():
    df1, df2 = _make_logs()
    df1["time"] = "not-a-date"
    with pytest.raises(TimeParseError, match="cannot parse"):
        wp.sync(df1, df2, common_columns="voltage", time1="time", time2="time")


def test_sync_low_correlation_warns():
    random_generator = np.random.default_rng(0)
    n = 2000
    time_range = pd.date_range("2024-01-01", periods=n, freq="500ms", tz="UTC")
    df1 = pd.DataFrame(
        {"time1": time_range.strftime(TIME_FORMAT), "voltage_1": random_generator.normal(0, 1, n)}
    )
    df2 = pd.DataFrame(
        {"time2": time_range.strftime(TIME_FORMAT), "voltage_2": random_generator.normal(0, 1, n)}
    )
    with pytest.warns(UserWarning, match="low correlation"):
        wp.sync(df1, df2, common_columns=("voltage_1", "voltage_2"), time1="time1", time2="time2")
