from collections.abc import Callable
from enum import Enum

import pandas as pd
import plotly.graph_objects as go

from .consts import TIME_LABEL, DataFormats
from .themes import Theme

_LARGE_NUMBER_THRESHOLD = 10_000
NO_LABEL = ""


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
    x: str, *series: pd.Series
) -> tuple[bool, Callable[[pd.DataFrame], pd.Series]]:
    """Build an x-value extractor that converts datetime columns to elapsed seconds.

    Pass one series for a single DataFrame, or multiple to share a global t0
    (so all traces use the same elapsed-time origin).

    Returns (is_time, xval) where xval(df) → pd.Series.
    Non-datetime columns are returned as-is.
    """
    is_datetime = pd.api.types.is_datetime64_any_dtype(series[0])

    if not is_datetime:

        def get_column(df: pd.DataFrame) -> pd.Series:
            return df[x]

        return False, get_column

    t0 = min(s.min() for s in series)

    def to_elapsed_seconds(df: pd.DataFrame) -> pd.Series:
        return (df[x] - t0).dt.total_seconds()

    return True, to_elapsed_seconds


def assign_colors(unique_values: list, colorway: list[str]) -> dict:
    """Map each unique value to a color from the colorway (cycling if needed)."""
    return {value: colorway[index % len(colorway)] for index, value in enumerate(unique_values)}


def finalize_axes(
    fig: go.Figure,
    theme: Theme,
    *,
    ref_x: pd.Series,
    ref_y: pd.Series,
    x_col: str,
    y_col: str,
    title: str | None,
    xlabel: str | None,
    ylabel: str | None,
    is_time: bool,
    show_legend: bool,
) -> None:
    """Apply theme, axis labels, tick formats, and legend visibility to a figure."""
    from .layout import apply_theme  # local import avoids circular dependency

    x_label = xlabel or (TIME_LABEL if is_time else x_col)
    apply_theme(fig, theme, title=title or smart_title(x_label, y_col))

    x_type = infer_axis_type(ref_x)
    x_tick_fmt = tick_format_for(ref_x)
    fig.update_xaxes(type=x_type, title_text=x_label, tickformat=x_tick_fmt)

    y_type = infer_axis_type(ref_y)
    y_tick_fmt = tick_format_for(ref_y)
    fig.update_yaxes(type=y_type, title_text=ylabel or y_col, tickformat=y_tick_fmt)

    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)


def to_traces(
    data: DataFormats,
    labels: list[str] | None = None,
) -> list[tuple[pd.DataFrame, str]]:
    is_multi_df = isinstance(data, list) and isinstance(data[0], pd.DataFrame)

    if is_multi_df:
        auto_labels = [str(i) for i in range(len(data))]
        trace_labels = labels if labels is not None else auto_labels
        return list(zip(data, trace_labels))

    return [(pd.DataFrame(data), NO_LABEL)]
