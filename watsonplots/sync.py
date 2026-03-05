import warnings

import pandas as pd

from .exceptions import ColumnNotFoundError, ConstantColumnError, TimeParseError

# Both signals are resampled to this uniform grid before cross-correlation.
# Finer resolution catches smaller time offsets; 100 ms is a practical default.
_RESAMPLE_FREQ = "100ms"

# Ratio of peak correlation to signal length below which we warn the user.
# Empirically, well-correlated signals score > 0.3; unrelated signals score < 0.05.
_MIN_CORRELATION_SCORE = 0.1


def sync(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    common_columns: str | tuple[str, str],
    time1: str,
    time2: str,
    time_format: str = "ISO8601",
    new_column_name: str | None = None,
    new_time_name: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Align two time-series logs to a common time reference.

    Uses cross-correlation on a shared signal to find the constant time offset,
    then shifts df2's timestamps by that lag. Both DataFrames keep their original
    rows and sample rates — only the timestamp column in df2 is adjusted.

    Parameters
    ----------
    df1, df2       : DataFrames to align.
    common_columns : Column to correlate on. Either a column name str (same name in both
                     DataFrames), or a (col_in_df1, col_in_df2) tuple when names differ.
    time1          : Timestamp column name in df1.
    time2          : Timestamp column name in df2.
    time_format    : pandas datetime format string for both timestamp columns.
                     Defaults to "ISO8601". Pass "mixed" for variable formats,
                     or any strptime format string (e.g. "%Y-%m-%d %H:%M:%S").
    column_name    : If given, rename the common column to this name in both output DataFrames.
    time_name      : If given, rename the time column to this name in both output DataFrames.

    Returns
    -------
    (df1, df2) — both with normalized timestamp columns, df2 shifted by the
    discovered lag. All other columns are untouched.
    """
    col1, col2 = (
        (common_columns, common_columns) if isinstance(common_columns, str) else common_columns
    )

    _require_column(df1, time1)
    _require_column(df2, time2)
    _require_column(df1, col1)
    _require_column(df2, col2)

    for column, df in [(col1, df1), (col2, df2)]:
        if df[column].std() == 0:
            raise ConstantColumnError(f"column '{column}' is constant — cannot use for sync")

    timestamps_1 = _parse_time(df1, time1, time_format)
    timestamps_2 = _parse_time(df2, time2, time_format)

    indexed_signal_1 = pd.Series(df1[col1].to_numpy(), index=timestamps_1)
    indexed_signal_2 = pd.Series(df2[col2].to_numpy(), index=timestamps_2)
    lag = _compute_lag(indexed_signal_1, indexed_signal_2, col1, col2)

    df1_synced = df1.copy()
    df1_synced[time1] = timestamps_1

    df2_synced = df2.copy()
    df2_synced[time2] = timestamps_2 - lag

    if new_column_name is not None:
        df1_synced = df1_synced.rename(columns={col1: new_column_name})
        df2_synced = df2_synced.rename(columns={col2: new_column_name})

    if new_time_name is not None:
        df1_synced = df1_synced.rename(columns={time1: new_time_name})
        df2_synced = df2_synced.rename(columns={time2: new_time_name})

    return df1_synced, df2_synced


def _require_column(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        raise ColumnNotFoundError(f"column '{col}' not found. Available: {list(df.columns)}")


def _parse_time(df: pd.DataFrame, col: str, time_format: str) -> pd.Series:
    try:
        return pd.to_datetime(df[col], format=time_format, utc=True)
    except Exception as exc:
        raise TimeParseError(
            f"cannot parse time column '{col}' with format='{time_format}'. "
            "Try passing time_format='mixed' or a custom strptime format."
        ) from exc


def _resample(signal: pd.Series) -> pd.Series:
    return signal.resample(_RESAMPLE_FREQ).mean().interpolate()


def _normalize(signal: pd.Series) -> pd.Series:
    return ((signal - signal.mean()) / signal.std()).fillna(0)


def _compute_lag(
    signal_1: pd.Series,
    signal_2: pd.Series,
    col1: str,
    col2: str,
) -> pd.Timedelta:
    try:
        from scipy.signal import correlate  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("sync requires scipy: pip install scipy") from exc

    resampled_1 = _resample(signal_1)
    resampled_2 = _resample(signal_2)

    cross_correlation = correlate(
        _normalize(resampled_1),
        _normalize(resampled_2),
    )

    correlation_quality_score = cross_correlation.max() / min(len(resampled_1), len(resampled_2))
    if correlation_quality_score < _MIN_CORRELATION_SCORE:
        warnings.warn(
            f"sync signals '{col1}' and '{col2}' show low correlation — "
            "result may be unreliable. Try a different 'common_column'.",
            stacklevel=4,
        )

    zero_lag_index = len(resampled_2) - 1
    peak_index = int(cross_correlation.argmax())
    lag_in_samples = peak_index - zero_lag_index
    return pd.Timedelta(_RESAMPLE_FREQ) * lag_in_samples
