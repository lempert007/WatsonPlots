import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import infer_axis_type, resolve_groups, smart_title, tick_format_for
from ..layout import apply_theme
from ..themes import Theme, get_theme


def line(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
    color: str | list[str] | None = None,
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
    data:        DataFrame, coercible (dict of lists, list of dicts),
                 or a list of DataFrames (one trace per DataFrame).
    x:           Column name for the x-axis.
    y:           Column name(s) for the y-axis. A list produces multiple traces.
    color:       Column name to split a single DataFrame into traces, or a list
                 of label strings when data is a list of DataFrames.
    title:       Chart title. Auto-generated if omitted.
    xlabel:      X-axis label override.
    ylabel:      Y-axis label override.
    theme:       Built-in theme name or Theme instance.
    mode:        Plotly scatter mode — "lines", "lines+markers", or "markers".
    smooth:      If True, use spline interpolation for smoother curves.
    show_legend: Show the legend (auto-disabled for single-series charts).
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    line_shape = "spline" if smooth else "linear"
    groups, ref_df = resolve_groups(data, color)

    fig = go.Figure()
    for sub_df, group_label in groups:
        for y_col in y_cols:
            fig.add_trace(go.Scatter(
                x=sub_df[x], y=sub_df[y_col],
                mode=mode, name=group_label or y_col,
                line=dict(shape=line_shape),
            ))

    apply_theme(fig, resolved_theme, title=title or smart_title(x, y_cols[0]))
    fig.update_xaxes(
        type=infer_axis_type(ref_df[x]),
        title_text=xlabel or x,
        tickformat=tick_format_for(ref_df[x]),
    )
    fig.update_yaxes(
        type=infer_axis_type(ref_df[y_cols[0]]),
        title_text=ylabel or (y if isinstance(y, str) else ""),
        tickformat=tick_format_for(ref_df[y_cols[0]]),
    )
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def area(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
    color: str | list[str] | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    stacked: bool = False,
    show_legend: bool = True,
) -> Chart:
    """
    Create a filled area chart.

    Parameters
    ----------
    data:    DataFrame, coercible, or a list of DataFrames.
    stacked: If True, subsequent traces are stacked on top of previous ones.
    color:   Column name (single DataFrame) or list of labels (list of DataFrames).
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    groups, ref_df = resolve_groups(data, color)

    fig = go.Figure()
    trace_n = 0
    for sub_df, group_label in groups:
        for y_col in y_cols:
            fig.add_trace(go.Scatter(
                x=sub_df[x], y=sub_df[y_col],
                mode="lines", name=group_label or y_col,
                fill="tonexty" if (stacked and trace_n > 0) else "tozeroy",
                line=dict(width=1),
            ))
            trace_n += 1

    apply_theme(fig, resolved_theme, title=title or smart_title(x, y_cols[0]))
    fig.update_xaxes(type=infer_axis_type(ref_df[x]), title_text=xlabel or x)
    fig.update_yaxes(title_text=ylabel or (y if isinstance(y, str) else ""))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)
