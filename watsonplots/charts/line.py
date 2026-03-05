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


def line(
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
    mode: str = "lines",
    smooth: bool = False,
    show_legend: bool = True,
    data_start: float = 0.0,
    data_end: float = 1.0,
) -> Chart:
    """
    Create a line chart.

    Parameters
    ----------
    data:          DataFrame, coercible, or a list of DataFrames (one trace per DataFrame).
    x:             Column name for the x-axis. All DataFrames must share this column name.
    y:             Column name(s) for the y-axis. When data is a list of DataFrames, a list
                   of the same length maps each entry to its DataFrame's y column.
    labels:        Trace names when data is a list of DataFrames.
    segment_color: Column whose value shades background bands on the chart.
    mode:          Plotly scatter mode — "lines", "lines+markers", or "markers".
    smooth:        If True, use spline interpolation.
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    line_shape = "spline" if smooth else "linear"
    is_multi = _is_multi_df(data)

    if is_multi:
        traces = _prepare_multi_df_traces(data, y_cols, labels, data_start, data_end)
        xval_dfs = [t.df for t in traces]
    else:
        traces = _prepare_single_df_traces(data, y_cols, labels, data_start, data_end)
        xval_dfs = [traces[0].df]

    is_datetime = _is_datetime_col(x, traces[0].df)
    xval = _build_xval(x, xval_dfs, is_datetime)

    fig = go.Figure()
    for trace in traces:
        _add_scatter_trace(fig, xval, trace.df, trace.y_col, trace.name, mode, line_shape)

    if segment_color and not is_multi:
        first_df = traces[0].df
        _add_segment_backgrounds(
            fig, first_df.assign(**{x: xval(first_df)}), x, segment_color, resolved_theme.colorway
        )

    finalize_axes(
        fig,
        resolved_theme,
        ref_x=xval(traces[0].df),
        ref_y=traces[0].df[traces[0].y_col],
        x_col=x,
        y_col=traces[0].y_col,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel or (y if isinstance(y, str) else ""),
        is_time=is_datetime,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _is_multi_df(data: DataFormats) -> bool:
    return isinstance(data, list) and isinstance(data[0], pd.DataFrame)


def _is_datetime_col(x: str, df: pd.DataFrame) -> bool:
    return pd.api.types.is_datetime64_any_dtype(try_parse_datetime(df[x]))


def _build_xval(x: str, dataframes: list[pd.DataFrame], is_datetime: bool) -> Callable:
    parsed_cols = [try_parse_datetime(df[x]) for df in dataframes]
    return make_elapsed_xval(x, is_datetime, *parsed_cols)


def _prepare_multi_df_traces(
    data: list[pd.DataFrame],
    y_cols: list[str],
    labels: list[str] | None,
    data_start: float,
    data_end: float,
) -> list[Trace]:
    sliced = [slice_by_fraction(df, data_start, data_end) for df in data]
    y_per_df = y_cols if len(y_cols) == len(sliced) else y_cols * len(sliced)
    trace_labels = labels or [str(i) for i in range(len(sliced))]
    return [
        Trace(df=df, y_col=y_col, name=name)
        for df, y_col, name in zip(sliced, y_per_df, trace_labels)
    ]


def _prepare_single_df_traces(
    data: DataFormats,
    y_cols: list[str],
    labels: list[str] | None,
    data_start: float,
    data_end: float,
) -> list[Trace]:
    raw_traces = to_traces(data, labels)
    sliced = [(slice_by_fraction(df, data_start, data_end), label) for df, label in raw_traces]
    return [
        Trace(df=df, y_col=y_col, name=label or y_col) for df, label in sliced for y_col in y_cols
    ]


def _add_scatter_trace(
    fig: go.Figure,
    xval: Callable,
    df: pd.DataFrame,
    y_col: str,
    name: str,
    mode: str,
    line_shape: str,
) -> None:
    fig.add_trace(
        go.Scatter(
            x=xval(df),
            y=df[y_col],
            mode=mode,
            name=name,
            line={"shape": line_shape},
        )
    )


def _add_segment_backgrounds(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    segment_col: str,
    colorway: list[str],
) -> None:
    """Shade the chart background with a colored band for each contiguous segment."""
    unique_values = list(dict.fromkeys(df[segment_col]))
    color_for = assign_colors(unique_values, colorway)

    for value, color in color_for.items():
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=str(value),
                marker={"color": color, "size": 10, "symbol": "square"},
                showlegend=True,
            )
        )

    mask = df[segment_col].ne(df[segment_col].shift())
    seg_starts = df.loc[mask, x].tolist()
    seg_values = df.loc[mask, segment_col].tolist()
    seg_ends = seg_starts[1:] + [df[x].iloc[-1]]

    for value, x0, x1 in zip(seg_values, seg_starts, seg_ends):
        fig.add_vrect(
            x0=x0, x1=x1, fillcolor=color_for[value], opacity=0.15, layer="below", line_width=0
        )
