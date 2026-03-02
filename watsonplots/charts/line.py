import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import (
    infer_axis_type,
    make_elapsed_xval,
    resolve_groups,
    smart_title,
    tick_format_for,
)
from ..layout import apply_theme
from ..themes import Theme, get_theme


def line(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
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
    data:          DataFrame, coercible (dict of lists, list of dicts),
                   or a list of DataFrames (one trace per DataFrame).
    x:             Column name for the x-axis.
    y:             Column name(s) for the y-axis. A list produces multiple traces.
    segment_color: Column name whose value defines background segments. Each contiguous
                   run of the same value gets a distinct semi-transparent background band.
    title:         Chart title. Auto-generated if omitted.
    xlabel:        X-axis label override.
    ylabel:        Y-axis label override.
    theme:         Built-in theme name or Theme instance.
    mode:          Plotly scatter mode — "lines", "lines+markers", or "markers".
    smooth:        If True, use spline interpolation for smoother curves.
    show_legend:   Show the legend (auto-disabled for single-series charts).
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    line_shape = "spline" if smooth else "linear"
    groups, ref_df = resolve_groups(data)

    is_time, xval = make_elapsed_xval(x, ref_df[x])

    fig = go.Figure()
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
            fig,
            ref_df.assign(**{x: xval(ref_df)}),
            x,
            segment_color,
            resolved_theme.colorway,
        )

    x_label = xlabel or ("Time (s)" if is_time else x)
    apply_theme(fig, resolved_theme, title=title or smart_title(x_label, y_cols[0]))
    fig.update_xaxes(
        type=infer_axis_type(xval(ref_df)),
        title_text=x_label,
        tickformat=tick_format_for(xval(ref_df)),
    )
    fig.update_yaxes(
        type=infer_axis_type(ref_df[y_cols[0]]),
        title_text=ylabel or (y if isinstance(y, str) else ""),
        tickformat=tick_format_for(ref_df[y_cols[0]]),
    )
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def _add_segment_backgrounds(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    segment_col: str,
    colorway: list[str],
) -> None:
    """Shade the chart background with a colored band for each contiguous segment.

    Each unique value in segment_col maps to a color from the theme's colorway.
    Bands are drawn below the data (layer='below') at low opacity so the lines
    remain clearly visible.
    """
    unique_values = list(dict.fromkeys(df[segment_col]))  # first-seen order
    color_for = {
        value: colorway[index % len(colorway)] for index, value in enumerate(unique_values)
    }

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

    # Close the final segment
    fig.add_vrect(
        x0=segment_start,
        x1=df[x].iloc[-1],
        fillcolor=color_for[previous_value],
        opacity=0.15,
        layer="below",
        line_width=0,
    )
