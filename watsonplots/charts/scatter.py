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

_BUBBLE_SIZE_MIN_PX = 8
_BUBBLE_SIZE_MAX_PX = 60


def scatter(
    data: DataFormats,
    *,
    x: str,
    y: str,
    size: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    opacity: float = 0.8,
    show_legend: bool = True,
    hover_data: list[str] | None = None,
    gradient_colors: tuple[str, str] | None = None,
) -> Chart:
    """
    Create a scatter plot (or bubble chart when size= is provided).

    Parameters
    ----------
    data:             DataFrame, coercible, or a list of DataFrames.
    x:                Column for x-axis
    y:                Column for y-axis
    size:             Column whose values control marker diameter (bubble mode).
                      Values are auto-scaled to an 8–60px range.
    hover_data:       Extra columns to include in hover tooltips.
    opacity:          Marker opacity (0.0–1.0)
    gradient_colors:  When provided as (start_color, end_color) hex strings, each point is
                      coloured by its row index along the gradient instead of grouping by color=.
    """
    resolved_theme = get_theme(theme)
    groups, ref_df = resolve_groups(data)
    is_time, xval = make_elapsed_xval(x, ref_df[x])

    def _make_trace(group_df: pd.DataFrame, name: str) -> go.Scatter:
        marker: dict = {"opacity": opacity}
        if size is not None:
            marker["size"] = _scale_bubble_sizes(group_df[size].astype(float))
            marker["sizemode"] = "diameter"
        return go.Scatter(
            x=xval(group_df),
            y=group_df[y],
            mode="markers",
            name=name,
            marker=marker,
            customdata=group_df[hover_data].values if hover_data else None,
            hovertemplate=_build_hover_template(x, y, hover_data) if hover_data else None,
        )

    fig = go.Figure()

    if gradient_colors is not None:
        merged_df = pd.concat([group_df for group_df, _ in groups], ignore_index=True)
        start_color, end_color = gradient_colors
        total_points = len(merged_df)
        marker: dict = {
            "opacity": opacity,
            "color": list(range(total_points)),
            "colorscale": [[0, start_color], [1, end_color]],
            "showscale": True,
            "colorbar": {
                "tickvals": [0, total_points - 1],
                "ticktext": ["First", "Last"],
                "thickness": 12,
                "len": 0.5,
            },
        }
        if size is not None:
            marker["size"] = _scale_bubble_sizes(merged_df[size].astype(float))
            marker["sizemode"] = "diameter"
        fig.add_trace(
            go.Scatter(
                x=xval(merged_df),
                y=merged_df[y],
                mode="markers",
                name=y,
                marker=marker,
                customdata=merged_df[hover_data].values if hover_data else None,
                hovertemplate=_build_hover_template(x, y, hover_data) if hover_data else None,
            )
        )
    else:
        for group_df, group_label in groups:
            fig.add_trace(_make_trace(group_df, group_label or y))

    x_label = xlabel or ("Time (s)" if is_time else x)
    apply_theme(fig, resolved_theme, title=title or smart_title(x_label, y))
    fig.update_xaxes(
        type=infer_axis_type(xval(ref_df)),
        title_text=x_label,
        tickformat=tick_format_for(xval(ref_df)),
    )
    fig.update_yaxes(title_text=ylabel or y, tickformat=tick_format_for(ref_df[y]))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def _scale_bubble_sizes(series: pd.Series) -> list:
    """Scale a series of values to pixel diameters in [_BUBBLE_SIZE_MIN_PX, _BUBBLE_SIZE_MAX_PX]."""
    value_range = series.max() - series.min()
    normalized = (series - series.min()) / (value_range if value_range > 0 else 1)
    return (_BUBBLE_SIZE_MIN_PX + (_BUBBLE_SIZE_MAX_PX - _BUBBLE_SIZE_MIN_PX) * normalized).tolist()


def _build_hover_template(x: str, y: str, hover_data: list[str]) -> str:
    """Build a Plotly hovertemplate string that includes hover_data columns."""
    extra = "".join(
        f"<br><b>{column}</b>: %{{customdata[{index}]}}" for index, column in enumerate(hover_data)
    )
    return f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}{extra}<extra></extra>"
