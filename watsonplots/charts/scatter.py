import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..layout import apply_theme
from ..themes import Theme, get_theme
from ..utils import (
    infer_axis_type,
    make_elapsed_xval,
    resolve_groups,
    smart_title,
    tick_format_for,
)

_BUBBLE_SIZE_MIN_PX = 8
_BUBBLE_SIZE_MAX_PX = 60


def scatter(
    data: DataFormats,
    *,
    x: str,
    y: str,
    labels: list[str] | None = None,
    size: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    opacity: float = 0.8,
    show_legend: bool = True,
    gradient_colors: tuple[str, str] | None = None,
) -> Chart:
    """
    Create a scatter plot (or bubble chart when size= is provided).

    Parameters
    ----------
    data:             DataFrame, coercible, or a list of DataFrames.
    x:                Column for x-axis
    y:                Column for y-axis
    labels:           Trace names when data is a list of DataFrames.
    size:             Column whose values control marker diameter (bubble mode).
                      Values are auto-scaled to an 8–60px range.
    opacity:          Marker opacity (0.0–1.0)
    gradient_colors:  When provided as (start_color, end_color) hex strings, each point is
                      coloured by its row index along the gradient instead of grouping by color=.
    """
    resolved_theme = get_theme(theme)
    groups, ref_df = resolve_groups(data, labels)
    is_time, xval = make_elapsed_xval(x, ref_df[x])

    all_hover_cols = [size] if size else []
    hover_template = _build_hover_template(x, y, all_hover_cols) if all_hover_cols else None

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
                customdata=merged_df[all_hover_cols].values if all_hover_cols else None,
                hovertemplate=hover_template,
            )
        )
    else:
        for group_df, group_label in groups:
            fixed_marker: dict = {"opacity": opacity}
            if size is not None:
                fixed_marker["size"] = _scale_bubble_sizes(group_df[size].astype(float))
                fixed_marker["sizemode"] = "diameter"
            fig.add_trace(
                go.Scatter(
                    x=xval(group_df),
                    y=group_df[y],
                    mode="markers",
                    name=group_label or y,
                    marker=fixed_marker,
                    customdata=group_df[all_hover_cols].values if all_hover_cols else None,
                    hovertemplate=hover_template,
                )
            )

    if size is not None:
        _add_size_legend(fig, ref_df[size].astype(float), size, opacity)

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


def _add_size_legend(
    fig: go.Figure,
    size_series: pd.Series,
    size_col: str,
    opacity: float,
) -> None:
    """Add three invisible legend traces showing min / mid / max bubble sizes."""
    min_val, max_val = size_series.min(), size_series.max()
    representative = [min_val, (min_val + max_val) / 2, max_val]
    scaled_sizes = _scale_bubble_sizes(pd.Series(representative))
    for index, (val, scaled) in enumerate(zip(representative, scaled_sizes)):
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=f"{val:.1f}",
                legendgroup=size_col,
                legendgrouptitle={"text": size_col} if index == 0 else None,
                marker={"size": scaled, "sizemode": "diameter", "opacity": opacity},
                showlegend=True,
            )
        )


def _build_hover_template(x: str, y: str, hover_data: list[str]) -> str:
    """Build a Plotly hovertemplate string that includes hover_data columns."""
    extra = "".join(
        f"<br><b>{column}</b>: %{{customdata[{index}]}}" for index, column in enumerate(hover_data)
    )
    return f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}{extra}<extra></extra>"
