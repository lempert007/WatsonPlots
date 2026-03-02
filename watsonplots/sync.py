import warnings

import pandas as pd

from .exceptions import ColumnNotFoundError, ConstantColumnError, TimeParseError

# Both signals are resampled to this uniform grid before cross-correlation.
# Finer resolution catches smaller time offsets; 100 ms is a practical default.
_RESAMPLE_FREQ = "100ms"


def sync(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    on: str | tuple[str, str],
    time1: str,
    time2: str,
    time_format: str = "ISO8601",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align two time-series logs to a common time reference.

    Uses cross-correlation on a shared signal to find the constant time offset,
    then shifts df2's timestamps by that lag. Both DataFrames keep their original
    rows and sample rates — only the timestamp column in df2 is adjusted.

    Parameters
    ----------
    df1, df2    : DataFrames to align.
    on          : Column to correlate on. Either a column name str (same name in both
                  DataFrames), or a (col_in_df1, col_in_df2) tuple when names differ.
    time1       : Timestamp column name in df1.
    time2       : Timestamp column name in df2.
    time_format : pandas datetime format string for both timestamp columns.
                  Defaults to "ISO8601". Pass "mixed" for variable formats,
                  or any strptime format string (e.g. "%Y-%m-%d %H:%M:%S").

    Returns
    -------
    (df1, df2) — both with UTC-normalized timestamp columns, df2 shifted by the
    discovered lag. All other columns are untouched.

    Example
    -------
    binlog_sync, jetson_sync = wp.sync(
        binlog, jetson,
        on=("BAT_Volt", "bus_voltage_v"),
        time1="timestamp_local",
        time2="jetson_timestamp_local",
    )
    """
    col1, col2 = (on, on) if isinstance(on, str) else on

    _require_column(df1, time1, role="time", df_name="df1")
    _require_column(df2, time2, role="time", df_name="df2")
    _require_column(df1, col1, role="sync", df_name="df1")
    _require_column(df2, col2, role="sync", df_name="df2")

    for col, df, label in [(col1, df1, "df1"), (col2, df2, "df2")]:
        if df[col].std() == 0:
            raise ConstantColumnError(
                f"column '{col}' in {label} is constant — cannot use for sync"
            )

    t1 = _parse_time(df1, time1, time_format)
    t2 = _parse_time(df2, time2, time_format)

    # Attach parsed UTC timestamps as the Series index (required for resample in _compute_lag)
    s1 = pd.Series(df1[col1].to_numpy(), index=t1)
    s2 = pd.Series(df2[col2].to_numpy(), index=t2)
    lag = _compute_lag(s1, s2, col1, col2)

    out1 = df1.copy()
    out1[time1] = t1

    out2 = df2.copy()
    out2[time2] = t2 - lag

    return out1, out2


def _require_column(df: pd.DataFrame, col: str, role: str, df_name: str) -> None:
    if col not in df.columns:
        raise ColumnNotFoundError(
            f"{role} column '{col}' not found in {df_name}. Available: {list(df.columns)}"
        )


def _parse_time(df: pd.DataFrame, col: str, time_format: str) -> pd.Series:
    try:
        return pd.to_datetime(df[col], format=time_format, utc=True)
    except Exception as exc:
        raise TimeParseError(
            f"cannot parse time column '{col}' with format='{time_format}'. "
            "Try passing time_format='mixed' or a custom strptime format."
        ) from exc


def _compute_lag(s1: pd.Series, s2: pd.Series, col1: str, col2: str) -> pd.Timedelta:
    try:
        from scipy.signal import correlate  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("sync requires scipy: pip install scipy") from exc

    # Resample both signals onto a uniform time grid so scipy's correlate
    # (which treats inputs as plain arrays) operates in consistent time units.
    r1 = s1.resample(_RESAMPLE_FREQ).mean().interpolate()
    r2 = s2.resample(_RESAMPLE_FREQ).mean().interpolate()

    def normalize(s: pd.Series) -> pd.Series:
        return ((s - s.mean()) / s.std()).fillna(0)

    corr = correlate(normalize(r1), normalize(r2), mode="full")

    if corr.max() / min(len(r1), len(r2)) < 0.1:
        warnings.warn(
            f"sync signals '{col1}' and '{col2}' show low correlation — "
            "result may be unreliable. Try a different 'on' column.",
            stacklevel=3,
        )

    # scipy's full cross-correlation output has length N1 + N2 - 1.
    # The zero-lag position sits at index (N2 - 1), so the actual lag in
    # samples is the distance of the peak from that centre.
    lag_samples = int(corr.argmax()) - (len(r2) - 1)
    return pd.Timedelta(_RESAMPLE_FREQ) * lag_samples
