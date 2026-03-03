import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..themes import Theme, get_theme
from ..utils import finalize_axes, make_elapsed_xval, to_traces

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
    trace_inputs = to_traces(data, labels)
    ref_df = trace_inputs[0][0]
    is_time, xval = make_elapsed_xval(x, ref_df[x])
    hover_template = _build_hover_template(x, y, size) if size else None

    fig = go.Figure()

    if gradient_colors is not None:
        merged_df = pd.concat([gdf for gdf, _ in trace_inputs], ignore_index=True)
        traces = [(merged_df, y)]
    else:
        traces = [(gdf, label or y) for gdf, label in trace_inputs]

    for df, name in traces:
        fig.add_trace(
            go.Scatter(
                x=xval(df),
                y=df[y],
                mode="markers",
                name=name,
                marker=_build_marker(df, size, opacity, gradient_colors),
                customdata=df[[size]].values if size else None,
                hovertemplate=hover_template,
            )
        )

    if size is not None:
        _add_size_legend(fig, ref_df[size].astype(float), size, opacity)

    ref_x = xval(ref_df)
    finalize_axes(
        fig,
        resolved_theme,
        ref_x=ref_x,
        ref_y=ref_df[y],
        x_col=x,
        y_col=y,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        is_time=is_time,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _build_marker(
    df: pd.DataFrame,
    size: str | None,
    opacity: float,
    gradient: tuple[str, str] | None,
) -> dict:
    marker: dict = {"opacity": opacity}
    if size is not None:
        marker["size"] = _scale_bubble_sizes(df[size].astype(float))
        marker["sizemode"] = "diameter"
    if gradient is not None:
        n = len(df)
        start, end = gradient
        colorbar = {
            "tickvals": [0, n - 1],
            "ticktext": ["First", "Last"],
            "thickness": 12,
            "len": 0.5,
        }
        marker.update(
            {
                "color": list(range(n)),
                "colorscale": [[0, start], [1, end]],
                "showscale": True,
                "colorbar": colorbar,
            }
        )
    return marker


def _scale_bubble_sizes(series: pd.Series) -> list:
    """Scale a series of values to pixel diameters in [_BUBBLE_SIZE_MIN_PX, _BUBBLE_SIZE_MAX_PX]."""
    value_range = series.max() - series.min()
    normalized = (series - series.min()) / (value_range if value_range > 0 else 1)
    pixel_range = _BUBBLE_SIZE_MAX_PX - _BUBBLE_SIZE_MIN_PX
    scaled = _BUBBLE_SIZE_MIN_PX + (pixel_range * normalized)
    return scaled.tolist()


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


def _build_hover_template(x: str, y: str, size_col: str) -> str:
    """Build a Plotly hovertemplate string that includes the size column."""
    return f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}<br><b>{size_col}</b>: %{{customdata[0]}}<extra></extra>"
