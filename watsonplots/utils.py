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
    NUMERIC = "-"
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
    for check, axis_type in AXIS_TYPE_CHECKS:
        if check(series):
            return axis_type
    return AxisType.CATEGORY


def smart_title(x: str | None, y: str | None) -> str:
    if x and y:
        return f"{y} vs {x}"
    return ""


def tick_format_for(series: pd.Series) -> TickFormat | None:
    for check, fmt in TICK_FORMAT_CHECKS:
        if check(series):
            return fmt
    return None


def try_parse_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    try:
        return pd.to_datetime(series, utc=True)
    except Exception:
        return series


def make_elapsed_xval(
    x: str, is_datetime: bool, *series: pd.Series
) -> Callable[[pd.DataFrame], pd.Series]:

    if not is_datetime:

        def get_column(df: pd.DataFrame) -> pd.Series:
            return df[x]

        return get_column

    t0 = min(s.min() for s in series)

    def to_elapsed_seconds(df: pd.DataFrame) -> pd.Series:
        parsed = try_parse_datetime(df[x])
        return (parsed - t0).dt.total_seconds()

    return to_elapsed_seconds


def consecutive_runs(df: pd.DataFrame, color: str | None) -> list[tuple[str, pd.DataFrame]]:
    """Split df into consecutive runs of equal color values, overlapping by 1 point so lines connect."""
    if color is None:
        return [("", df)]
    vals = df[color].tolist()
    runs = []
    start = 0
    for i in range(1, len(vals)):
        if vals[i] != vals[start]:
            runs.append((str(vals[start]), df.iloc[start : i + 1]))
            start = i
    runs.append((str(vals[start]), df.iloc[start:]))
    return runs


def assign_colors(unique_values: list, colorway: list[str]) -> dict:
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


def slice_by_fraction(df: pd.DataFrame, start: float, end: float) -> pd.DataFrame:
    n = len(df)
    start_idx = int(n * start)
    end_idx = int(n * end)
    return df.iloc[start_idx:end_idx]
