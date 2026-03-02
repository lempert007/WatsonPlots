from collections.abc import Callable
from enum import Enum

import pandas as pd

from .consts import DataFormats

_LARGE_NUMBER_THRESHOLD = 10_000


class AxisType(str, Enum):
    DATE = "date"
    NUMERIC = "-"  # Plotly's auto-detect sentinel; resolves to linear for numeric data
    CATEGORY = "category"


class TickFormat(str, Enum):
    LARGE_NUMBER = ",.0f"  # thousands separator, no decimals


AXIS_TYPE_CHECKS: list[tuple[Callable, AxisType]] = [
    (pd.api.types.is_datetime64_any_dtype, AxisType.DATE),
    (pd.api.types.is_numeric_dtype, AxisType.NUMERIC),
]


def _is_large_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and series.abs().max() >= _LARGE_NUMBER_THRESHOLD


TICK_FORMAT_CHECKS: list[tuple[Callable, TickFormat]] = [
    (_is_large_numeric, TickFormat.LARGE_NUMBER),
]


def infer_axis_type(series: pd.Series) -> AxisType:
    """Return the Plotly axis type for a series based on its dtype."""
    for check, axis_type in AXIS_TYPE_CHECKS:
        if check(series):
            return axis_type
    return AxisType.CATEGORY


def smart_title(x: str | None, y: str | None) -> str:
    """Generate a default chart title from column names."""
    if x and y:
        return f"{y} vs {x}"
    return ""


def tick_format_for(series: pd.Series) -> TickFormat | None:
    """Return a Plotly tickformat string for the series, or None."""
    for check, fmt in TICK_FORMAT_CHECKS:
        if check(series):
            return fmt
    return None


def make_elapsed_xval(
    x: str, series: pd.Series
) -> tuple[bool, Callable[[pd.DataFrame], pd.Series]]:
    """Build an x-value extractor that converts datetime columns to elapsed seconds.

    Returns (is_time, xval) where xval(df) → pd.Series.
    Non-datetime columns are returned as-is.
    """
    if not pd.api.types.is_datetime64_any_dtype(series):
        return False, lambda df: df[x]
    t0 = series.min()
    return True, lambda df: (df[x] - t0).dt.total_seconds()


def make_shared_elapsed_xval(
    df_col_pairs: list[tuple[pd.DataFrame, str]],
) -> tuple[bool, Callable[[pd.DataFrame, str], pd.Series]]:
    """Build a shared x-value extractor for multiple DataFrames with different x columns.

    When the x columns are datetime, all DataFrames share a common t0 (global minimum)
    so elapsed-seconds values are consistent across traces.

    Returns (is_time, xval) where xval(df, col) → pd.Series.
    """
    first_series = df_col_pairs[0][0][df_col_pairs[0][1]]
    if not pd.api.types.is_datetime64_any_dtype(first_series):
        return False, lambda df, col: df[col]
    t0 = min(df[col].min() for df, col in df_col_pairs)
    return True, lambda df, col: (df[col] - t0).dt.total_seconds()


def assign_colors(unique_values: list, colorway: list[str]) -> dict:
    """Map each unique value to a color from the colorway (cycling if needed)."""
    return {value: colorway[index % len(colorway)] for index, value in enumerate(unique_values)}


def resolve_groups(
    data: DataFormats,
    labels: list[str] | None = None,
) -> tuple[list[tuple[pd.DataFrame, str | None]], pd.DataFrame]:
    """
    Resolve any supported data input into ([(group_df, label), ...], ref_df).

    label is None for a single DataFrame — callers fall back to the column name.
    A list of DataFrames produces one trace per DataFrame, labeled by index unless
    labels are provided.
    """
    if isinstance(data, list) and data and isinstance(data[0], pd.DataFrame):
        trace_labels = labels if labels is not None else [str(i) for i in range(len(data))]
        return list(zip(data, trace_labels)), data[0]
    df = pd.DataFrame(data)
    return [(df, None)], df
