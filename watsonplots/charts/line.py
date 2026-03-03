from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..themes import Theme, get_theme
from ..utils import (
    assign_colors,
    finalize_axes,
    make_elapsed_xval,
    to_traces,
)

# Type alias for the x-value extractor returned by make_elapsed_xval
XVal = Callable[[pd.DataFrame], pd.Series]


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
    fig = go.Figure()
    line_shape = "spline" if smooth else "linear"
    y_cols = [y] if isinstance(y, str) else list(y)

    if isinstance(data, list) and isinstance(data[0], pd.DataFrame):
        is_time, xval = make_elapsed_xval(x, *[df[x] for df in data])
        ref_df = data[0]
        _add_multi_df_traces(fig, data, y, labels, mode, line_shape, xval)
    else:
        traces = to_traces(data)
        ref_df = traces[0][0]
        is_time, xval = make_elapsed_xval(x, ref_df[x])
        _add_single_df_traces(fig, traces, y_cols, mode, line_shape, xval)
        if segment_color:
            elapsed_ref_df = ref_df.assign(**{x: xval(ref_df)})
            _add_segment_backgrounds(fig, elapsed_ref_df, x, segment_color, resolved_theme.colorway)

    y_label = ylabel or (y if isinstance(y, str) else "")
    finalize_axes(
        fig,
        resolved_theme,
        ref_x=xval(ref_df),
        ref_y=ref_df[y_cols[0]],
        x_col=x,
        y_col=y_cols[0],
        title=title,
        xlabel=xlabel,
        ylabel=y_label,
        is_time=is_time,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _add_multi_df_traces(
    fig: go.Figure,
    data: list[pd.DataFrame],
    y: str | list[str],
    labels: list[str] | None,
    mode: str,
    line_shape: str,
    xval: XVal,
) -> None:
    y_cols = [y] * len(data) if isinstance(y, str) else list(y)
    trace_labels = labels if labels is not None else [str(i) for i in range(len(data))]
    for df, label, y_col in zip(data, trace_labels, y_cols):
        fig.add_trace(
            go.Scatter(
                x=xval(df),
                y=df[y_col],
                mode=mode,
                name=label,
                line={"shape": line_shape},
            )
        )


def _add_single_df_traces(
    fig: go.Figure,
    traces: list[tuple[pd.DataFrame, str]],
    y_cols: list[str],
    mode: str,
    line_shape: str,
    xval: XVal,
) -> None:
    for group_df, group_label in traces:
        for y_col in y_cols:
            fig.add_trace(
                go.Scatter(
                    x=xval(group_df),
                    y=group_df[y_col],
                    mode=mode,
                    name=group_label or y_col,
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
            x0=x0,
            x1=x1,
            fillcolor=color_for[value],
            opacity=0.15,
            layer="below",
            line_width=0,
        )
