from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats, Trace
from ..themes import Theme, get_theme
from ..utils import (
    assign_colors,
    finalize_axes,
    make_elapsed_xval,
    slice_by_fraction,
    to_traces,
    try_parse_datetime,
)

_FILL_ZERO = "tozeroy"
_FILL_STACK = "tonexty"
_AREA_LINE_WIDTH = 1


def area(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
    labels: list[str] | None = None,
    segment_color: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    stacked: bool = False,
    show_legend: bool = True,
    data_start: float = 0.0,
    data_end: float = 1.0,
) -> Chart:
    """
    Create a filled area chart.

    Parameters
    ----------
    data:           DataFrame, coercible, or a list of DataFrames.
    labels:         Trace names when data is a list of DataFrames.
    stacked:        If True, subsequent traces are stacked on top of previous ones.
    segment_color:  Column whose value determines the fill color of each contiguous segment.
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    traces = _build_traces(data, y_cols, labels, data_start, data_end)
    xval, is_datetime = _build_xval(x, traces[0].df)

    fig = go.Figure()
    for trace in traces:
        _add_area_trace(fig, xval, trace, x, stacked, segment_color, resolved_theme.colorway)

    finalize_axes(
        fig,
        resolved_theme,
        ref_x=xval(traces[0].df),
        ref_y=traces[0].df[traces[0].y_col],
        x_col=x,
        y_col=traces[0].y_col,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        is_time=is_datetime,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _build_traces(
    data: DataFormats,
    y_cols: list[str],
    labels: list[str] | None,
    data_start: float,
    data_end: float,
) -> list[Trace]:
    """Expand input data into one Trace per (group × y_col) combination."""
    return [
        Trace(df=slice_by_fraction(df, data_start, data_end), y_col=y_col, name=label or y_col)
        for df, label in to_traces(data, labels)
        for y_col in y_cols
    ]


def _build_xval(x: str, ref_df: pd.DataFrame) -> tuple[Callable, bool]:
    """Detect whether x is datetime and build the appropriate x-value accessor."""
    parsed_x = try_parse_datetime(ref_df[x])
    is_datetime = pd.api.types.is_datetime64_any_dtype(parsed_x)
    xval = make_elapsed_xval(x, is_datetime, parsed_x)
    return xval, is_datetime


def _add_area_trace(
    fig: go.Figure,
    xval: Callable,
    trace: Trace,
    x: str,
    stacked: bool,
    segment_color: str | None,
    colorway: list[str],
) -> None:
    """Add one area trace to the figure — either segmented or plain."""
    if segment_color:
        _add_segmented_traces(
            fig, trace.df.assign(**{x: xval(trace.df)}), x, trace.y_col, segment_color, colorway
        )
    else:
        fill = _FILL_STACK if stacked and len(fig.data) > 0 else _FILL_ZERO
        fig.add_trace(_build_area_scatter(xval, trace, fill))


def _build_area_scatter(xval: Callable, trace: Trace, fill: str) -> go.Scatter:
    """Build a plain filled Scatter trace for one area series."""
    return go.Scatter(
        x=xval(trace.df),
        y=trace.df[trace.y_col],
        mode="lines",
        name=trace.name,
        fill=fill,
        line={"width": _AREA_LINE_WIDTH},
    )


def _iter_segments(df: pd.DataFrame, col: str):
    """Yield (segment_df, value) for each contiguous run of equal values in col.
    Each segment includes one extra overlapping row to avoid visual gaps.
    """
    df = df.reset_index(drop=True)
    runs = df[col].ne(df[col].shift()).cumsum()
    for _, group in df.groupby(runs, sort=False):
        end = min(group.index[-1] + 2, len(df))
        yield df.iloc[group.index[0] : end], group[col].iloc[0]


def _add_segmented_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y_col: str,
    segment_col: str,
    colorway: list[str],
) -> None:
    """Add one filled trace per contiguous segment, coloured by segment value."""
    unique_values = list(dict.fromkeys(df[segment_col]))
    color_for = assign_colors(unique_values, colorway)
    shown_in_legend: set = set()
    for segment_df, value in _iter_segments(df, segment_col):
        color = color_for[value]
        fig.add_trace(
            go.Scatter(
                x=segment_df[x],
                y=segment_df[y_col],
                mode="lines",
                name=str(value),
                fill=_FILL_ZERO,
                line={"width": _AREA_LINE_WIDTH, "color": color},
                fillcolor=color,
                showlegend=(value not in shown_in_legend),
                legendgroup=str(value),
            )
        )
        shown_in_legend.add(value)
