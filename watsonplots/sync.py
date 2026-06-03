import warnings

import pandas as pd

from watsonplots.exceptions import (
    ColumnNotFoundError,
    ConstantColumnError,
    MissingDependencyError,
    TimeParseError,
)

_RESAMPLE_FREQ = "10ms"
_LOW_CORRELATION_THRESHOLD = 0.3


def sync(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    common_columns: str | tuple[str, str],
    time1: str,
    time2: str,
    time_format: str = "mixed",
    new_column_name: str | None = None,
    new_time_name: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Time-align two DataFrames by cross-correlating a shared signal column.

    Parameters
    ----------
    df1, df2:          DataFrames to align.
    common_columns:    Signal column used for cross-correlation. Pass a single
                       string when both DataFrames share the same column name,
                       or a (col1, col2) tuple when the names differ.
    time1, time2:      Timestamp columns (one per DataFrame).
    time_format:       strptime format string, or "mixed" for auto-detection.
    new_column_name:   Rename both signal columns to this in the output.
    new_time_name:     Rename both time columns to this in the output.
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
        from scipy.signal import correlate  # optional dependency
    except ImportError as exc:
        raise MissingDependencyError("sync requires scipy: pip install scipy") from exc

    resampled_1 = _resample(signal_1)
    resampled_2 = _resample(signal_2)

    common_index = resampled_1.index.union(resampled_2.index)
    aligned_1 = resampled_1.reindex(common_index).interpolate().fillna(0)
    aligned_2 = resampled_2.reindex(common_index).interpolate().fillna(0)

    norm_1 = _normalize(aligned_1)
    norm_2 = _normalize(aligned_2)

    correlation = correlate(norm_1, norm_2, mode="full")
    lag_index = correlation.argmax() - (len(norm_2) - 1)
    freq = pd.tseries.frequencies.to_offset(_RESAMPLE_FREQ)
    lag = pd.Timedelta(freq.nanos * lag_index, unit="ns")

    max_correlation = float(correlation.max() / len(norm_1))
    if max_correlation < _LOW_CORRELATION_THRESHOLD:
        warnings.warn(
            f"low correlation ({max_correlation:.2f}) between '{col1}' and '{col2}'. "
            "Sync result may be unreliable.",
            stacklevel=3,
        )

    return lag
