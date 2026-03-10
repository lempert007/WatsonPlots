import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..layout import apply_theme
from ..themes import Theme, get_theme
from ..utils import (
    assign_colors,
    slice_by_fraction,
    smart_title,
    to_traces,
)


def scatter3d(
    data: DataFormats,
    *,
    x: str,
    y: str,
    z: str,
    color: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    zlabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    show_legend: bool = True,
    data_start: float = 0.0,
    data_end: float = 1.0,
) -> Chart:
    """
    Create a 3D scatter plot.

    Parameters
    ----------
    data:    DataFrame, coercible, or a list of DataFrames.
    x:       Column for x-axis.
    y:       Column for y-axis.
    z:       Column for z-axis.
    color:   Column whose unique values split data into separate marker groups.
    xlabel:  X-axis label (defaults to column name).
    ylabel:  Y-axis label (defaults to column name).
    zlabel:  Z-axis label (defaults to column name).
    """
    resolved_theme = get_theme(theme)
    first_df, _ = to_traces(data, None)[0]
    df = slice_by_fraction(first_df, data_start, data_end)

    fig = go.Figure()

    if color is not None:
        unique_vals = list(df[color].unique())
        color_map = assign_colors(unique_vals, resolved_theme.colorway)
        for val in unique_vals:
            subset = df[df[color] == val]
            fig.add_trace(
                go.Scatter3d(
                    x=subset[x],
                    y=subset[y],
                    z=subset[z],
                    mode="markers",
                    name=str(val),
                    marker=dict(color=color_map[val], size=4),
                )
            )
    else:
        fig.add_trace(
            go.Scatter3d(
                x=df[x],
                y=df[y],
                z=df[z],
                mode="markers",
                name="",
                marker=dict(size=4),
            )
        )

    _finalize_3d(
        fig,
        resolved_theme,
        x_col=x,
        y_col=y,
        z_col=z,
        xlabel=xlabel,
        ylabel=ylabel,
        zlabel=zlabel,
        title=title,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def line3d(
    data: DataFormats,
    *,
    x: str,
    y: str,
    z: str,
    color: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    zlabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    show_legend: bool = True,
    data_start: float = 0.0,
    data_end: float = 1.0,
) -> Chart:
    """
    Create a 3D line chart.

    Parameters
    ----------
    data:    DataFrame, coercible, or a list of DataFrames.
    x:       Column for x-axis.
    y:       Column for y-axis.
    z:       Column for z-axis.
    color:   Column whose unique values split data into separate colored lines.
    xlabel:  X-axis label (defaults to column name).
    ylabel:  Y-axis label (defaults to column name).
    zlabel:  Z-axis label (defaults to column name).
    """
    resolved_theme = get_theme(theme)
    first_df, _ = to_traces(data, None)[0]
    df = slice_by_fraction(first_df, data_start, data_end)

    fig = go.Figure()

    if color is not None:
        unique_vals = list(df[color].unique())
        color_map = assign_colors(unique_vals, resolved_theme.colorway)
        for val in unique_vals:
            subset = df[df[color] == val]
            fig.add_trace(
                go.Scatter3d(
                    x=subset[x],
                    y=subset[y],
                    z=subset[z],
                    mode="lines",
                    name=str(val),
                    line=dict(color=color_map[val], width=3),
                )
            )
    else:
        fig.add_trace(
            go.Scatter3d(
                x=df[x],
                y=df[y],
                z=df[z],
                mode="lines",
                name="",
                line=dict(width=3),
            )
        )

    _finalize_3d(
        fig,
        resolved_theme,
        x_col=x,
        y_col=y,
        z_col=z,
        xlabel=xlabel,
        ylabel=ylabel,
        zlabel=zlabel,
        title=title,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _finalize_3d(
    fig: go.Figure,
    theme: Theme,
    *,
    x_col: str,
    y_col: str,
    z_col: str,
    xlabel: str | None,
    ylabel: str | None,
    zlabel: str | None,
    title: str | None,
    show_legend: bool,
) -> None:
    apply_theme(fig, theme, title=title or smart_title(x_col, f"{z_col} / {y_col}"))
    axis_style = dict(
        gridcolor=theme.gridcolor,
        gridwidth=theme.gridwidth,
        zerolinecolor=theme.zerolinecolor,
        linecolor=theme.linecolor,
        color=theme.font_color,
        showbackground=True,
        backgroundcolor=theme.plot_bgcolor,
    )
    fig.update_scenes(
        xaxis=dict(**axis_style, title_text=xlabel or x_col),
        yaxis=dict(**axis_style, title_text=ylabel or y_col),
        zaxis=dict(**axis_style, title_text=zlabel or z_col),
    )
    fig.update_layout(showlegend=show_legend and len(fig.data) > 1)
