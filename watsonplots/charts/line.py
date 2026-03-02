from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..layout import apply_theme
from ..themes import Theme, get_theme
from ..utils import (
    assign_colors,
    infer_axis_type,
    make_elapsed_xval,
    make_shared_elapsed_xval,
    resolve_groups,
    smart_title,
    tick_format_for,
)


@dataclass
class AxisRefs:
    is_time: bool
    ref_x: pd.Series
    ref_y: pd.Series
    ref_y_name: str


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

    if isinstance(data, list) and isinstance(data[0], pd.DataFrame):
        axes = _add_multi_df_traces(fig, data, x, y, labels, mode, line_shape)
    else:
        axes = _add_single_df_traces(
            fig, data, x, y, mode, line_shape, segment_color, resolved_theme.colorway
        )

    x_label = xlabel or ("Time (s)" if axes.is_time else x)
    apply_theme(fig, resolved_theme, title=title or smart_title(x_label, axes.ref_y_name))
    fig.update_xaxes(
        type=infer_axis_type(axes.ref_x), title_text=x_label, tickformat=tick_format_for(axes.ref_x)
    )
    fig.update_yaxes(
        type=infer_axis_type(axes.ref_y),
        title_text=ylabel or (y if isinstance(y, str) else ""),
        tickformat=tick_format_for(axes.ref_y),
    )
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def _add_multi_df_traces(
    fig: go.Figure,
    data: list[pd.DataFrame],
    x: str,
    y: str | list[str],
    labels: list[str] | None,
    mode: str,
    line_shape: str,
) -> AxisRefs:
    y_cols = [y] * len(data) if isinstance(y, str) else list(y)
    trace_labels = labels if labels is not None else [str(i) for i in range(len(data))]
    is_time, xval = make_shared_elapsed_xval([(df, x) for df in data])
    for df, label, y_col in zip(data, trace_labels, y_cols):
        fig.add_trace(
            go.Scatter(
                x=xval(df, x), y=df[y_col], mode=mode, name=label, line={"shape": line_shape}
            )
        )
    ref_df = data[0]
    return AxisRefs(is_time, xval(ref_df, x), ref_df[y_cols[0]], y_cols[0])


def _add_single_df_traces(
    fig: go.Figure,
    data: DataFormats,
    x: str,
    y: str | list[str],
    mode: str,
    line_shape: str,
    segment_color: str | None,
    colorway: list[str],
) -> AxisRefs:
    y_cols = [y] if isinstance(y, str) else list(y)
    groups, ref_df = resolve_groups(data)
    is_time, xval = make_elapsed_xval(x, ref_df[x])
    for group_df, group_label in groups:
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
    if segment_color:
        _add_segment_backgrounds(
            fig, ref_df.assign(**{x: xval(ref_df)}), x, segment_color, colorway
        )
    return AxisRefs(is_time, xval(ref_df), ref_df[y_cols[0]], y_cols[0])


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

    previous_value = df[segment_col].iloc[0]
    segment_start = df[x].iloc[0]

    for row_idx in range(1, len(df)):
        current_value = df[segment_col].iloc[row_idx]
        if current_value != previous_value:
            fig.add_vrect(
                x0=segment_start,
                x1=df[x].iloc[row_idx],
                fillcolor=color_for[previous_value],
                opacity=0.15,
                layer="below",
                line_width=0,
            )
            segment_start = df[x].iloc[row_idx]
            previous_value = current_value

    fig.add_vrect(
        x0=segment_start,
        x1=df[x].iloc[-1],
        fillcolor=color_for[previous_value],
        opacity=0.15,
        layer="below",
        line_width=0,
    )
