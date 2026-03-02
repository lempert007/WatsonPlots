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


def _make_logs(lag_seconds: float = 5.0, n: int = 200, seed: int = 42):
    """Two logs of a shared physical signal where df2 starts lag_seconds later.

    Both sensors record the same underlying random-walk signal, but df2 captures
    a later window — as happens when sensor clocks are offset or one starts later.
    Cross-correlation can then detect the lag from the shifted value sequences.
    """
    rng = np.random.default_rng(seed)
    lag_at_500ms = round(lag_seconds / 0.5)
    # Generate enough signal for both windows
    signal = np.cumsum(rng.normal(0, 1, n + lag_at_500ms))

    t1 = pd.date_range("2024-01-01 00:00:00", periods=n, freq="500ms", tz="UTC")
    t2 = t1 + pd.Timedelta(seconds=lag_seconds)

    df1 = pd.DataFrame({"ts": t1.strftime(TIME_FORMAT), "voltage": signal[:n]})
    # df2 observes the physical signal lag_at_500ms samples later, reported at t2
    df2 = pd.DataFrame(
        {"ts": t2.strftime(TIME_FORMAT), "voltage": signal[lag_at_500ms : lag_at_500ms + n]}
    )
    return df1, df2


# --- happy path ---


def test_sync_returns_two_dataframes():
    df1, df2 = _make_logs()
    out1, out2 = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")
    assert isinstance(out1, pd.DataFrame) and isinstance(out2, pd.DataFrame)


def test_sync_preserves_row_counts():
    df1, df2 = _make_logs()
    out1, out2 = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")
    assert len(out1) == len(df1)
    assert len(out2) == len(df2)


def test_sync_lag_within_one_sample():
    """After sync, df2's timestamps should be shifted within ~1 sample (500 ms) of df1."""
    lag = 5.0
    df1, df2 = _make_logs(lag_seconds=lag)
    out1, out2 = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")

    t1 = pd.to_datetime(out1["ts"], utc=True)
    t2 = pd.to_datetime(out2["ts"], utc=True)
    residual = abs((t2.iloc[0] - t1.iloc[0]).total_seconds())
    assert residual < 0.6  # within one 500 ms sample


def test_sync_tuple_on():
    """on= accepts a (col_df1, col_df2) tuple when column names differ."""
    df1, df2 = _make_logs()
    df2 = df2.rename(columns={"voltage": "volt2"})
    out1, out2 = wp.sync(df1, df2, on=("voltage", "volt2"), time1="ts", time2="ts")
    assert len(out1) == len(df1)


def test_sync_timestamp_converted_to_utc():
    """Output timestamp columns should be UTC-aware datetime objects."""
    df1, df2 = _make_logs()
    out1, out2 = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")
    assert pd.to_datetime(out1["ts"], utc=True).dt.tz is not None


def test_sync_other_columns_untouched():
    """Non-time, non-sync columns must be preserved exactly."""
    df1, df2 = _make_logs()
    df1["extra"] = 99
    out1, _ = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")
    assert (out1["extra"] == 99).all()


def test_sync_timezone_mismatch_does_not_crash():
    """Logs with timestamps appearing in different timezones (both naive) should still sync.

    This is the real-world case where one log stores UTC and another stores local time
    (e.g. UTC+5), both without timezone info. The absolute timestamps look 5 hours apart
    but the signal content is the same physical session. sync() must not raise and should
    still find the correct signal lag.
    """
    df1, df2 = _make_logs(lag_seconds=5.0)
    # Simulate UTC vs UTC+5 mismatch: push df2 timestamps 5 hours into the future.
    # The signal values are unchanged — only the timestamp labels are "wrong".
    df2["ts"] = (pd.to_datetime(df2["ts"], utc=True) + pd.Timedelta(hours=5)).dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%f+00:00"
    )

    out1, out2 = wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")
    assert len(out1) == len(df1)
    assert len(out2) == len(df2)


# --- error cases ---


def test_sync_missing_sync_col_df1():
    df1, df2 = _make_logs()
    with pytest.raises(ColumnNotFoundError, match="sync column 'bad'"):
        wp.sync(df1, df2, on="bad", time1="ts", time2="ts")


def test_sync_missing_sync_col_df2():
    df1, df2 = _make_logs()
    with pytest.raises(ColumnNotFoundError, match="df2"):
        wp.sync(df1, df2, on=("voltage", "bad"), time1="ts", time2="ts")


def test_sync_missing_time_col():
    df1, df2 = _make_logs()
    with pytest.raises(ColumnNotFoundError, match="time column 'bad'"):
        wp.sync(df1, df2, on="voltage", time1="bad", time2="ts")


def test_sync_constant_column_raises():
    df1, df2 = _make_logs()
    df1["voltage"] = 5.0  # constant
    with pytest.raises(ConstantColumnError, match="constant"):
        wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")


def test_sync_bad_time_format_raises():
    df1, df2 = _make_logs()
    df1["ts"] = "not-a-date"
    with pytest.raises(TimeParseError, match="cannot parse"):
        wp.sync(df1, df2, on="voltage", time1="ts", time2="ts")


def test_sync_low_correlation_warns():
    """Independent white-noise signals reliably produce a low-correlation warning.

    n=2000 at 500ms → ~10 000 resampled samples. For two independent white-noise
    signals of this length, corr.max()/n ≈ 0.07–0.09, safely below the 0.1 threshold
    across many seeds.
    """
    rng = np.random.default_rng(0)
    n = 2000
    t = pd.date_range("2024-01-01", periods=n, freq="500ms", tz="UTC")
    df1 = pd.DataFrame({"ts": t.strftime(TIME_FORMAT), "v": rng.normal(0, 1, n)})
    df2 = pd.DataFrame({"ts": t.strftime(TIME_FORMAT), "v": rng.normal(0, 1, n)})
    with pytest.warns(UserWarning, match="low correlation"):
        wp.sync(df1, df2, on="v", time1="ts", time2="ts")
