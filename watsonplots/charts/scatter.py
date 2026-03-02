import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import resolve_groups, smart_title, tick_format_for
from ..layout import apply_theme
from ..themes import Theme, get_theme


def scatter(
    data: DataFormats,
    *,
    x: str,
    y: str,
    color: str | list[str] | None = None,
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
    color:            Column name (single DataFrame) or list of labels (list of DataFrames).
                      Ignored when gradient_colors is set.
    size:             Column whose values control marker diameter (bubble mode).
                      Values are auto-scaled to an 8–60px range.
    hover_data:       Extra columns to include in hover tooltips.
    opacity:          Marker opacity (0.0–1.0).
    gradient_colors:  When provided as (start_color, end_color) hex strings, each point is
                      coloured by its row index along the gradient instead of grouping by color=.
    """
    resolved_theme = get_theme(theme)
    groups, ref_df = resolve_groups(data, color)

    # Convert datetime x-axis to elapsed seconds
    is_time = pd.api.types.is_datetime64_any_dtype(ref_df[x])
    t0 = ref_df[x].min() if is_time else None

    def xval(df: pd.DataFrame) -> pd.Series:
        return (df[x] - t0).dt.total_seconds() if is_time else df[x]

    def _make_trace(sub_df: pd.DataFrame, name: str) -> go.Scatter:
        marker: dict = {"opacity": opacity}
        if size is not None:
            s = sub_df[size].astype(float)
            rng = s.max() - s.min()
            marker["size"] = (8 + 52 * (s - s.min()) / (rng if rng > 0 else 1)).tolist()
            marker["sizemode"] = "diameter"
        if hover_data:
            customdata = sub_df[hover_data].values
            hovertemplate = (
                f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}"
                + "".join(
                    f"<br><b>{col}</b>: %{{customdata[{i}]}}" for i, col in enumerate(hover_data)
                )
                + "<extra></extra>"
            )
        else:
            customdata, hovertemplate = None, None
        return go.Scatter(
            x=xval(sub_df),
            y=sub_df[y],
            mode="markers",
            name=name,
            marker=marker,
            customdata=customdata,
            hovertemplate=hovertemplate,
        )

    fig = go.Figure()

    if gradient_colors is not None:
        merged_df = pd.concat([sub_df for sub_df, _ in groups], ignore_index=True)
        start_color, end_color = gradient_colors
        n = len(merged_df)
        marker: dict = {
            "opacity": opacity,
            "color": list(range(n)),
            "colorscale": [[0, start_color], [1, end_color]],
            "showscale": True,
            "colorbar": {
                "tickvals": [0, n - 1],
                "ticktext": ["First", "Last"],
                "thickness": 12,
                "len": 0.5,
            },
        }
        if size is not None:
            s = merged_df[size].astype(float)
            rng = s.max() - s.min()
            marker["size"] = (8 + 52 * (s - s.min()) / (rng if rng > 0 else 1)).tolist()
            marker["sizemode"] = "diameter"
        if hover_data:
            customdata = merged_df[hover_data].values
            hovertemplate = (
                f"<b>{x}</b>: %{{x}}<br><b>{y}</b>: %{{y}}"
                + "".join(
                    f"<br><b>{col}</b>: %{{customdata[{i}]}}" for i, col in enumerate(hover_data)
                )
                + "<extra></extra>"
            )
        else:
            customdata, hovertemplate = None, None
        fig.add_trace(
            go.Scatter(
                x=xval(merged_df),
                y=merged_df[y],
                mode="markers",
                name=y,
                marker=marker,
                customdata=customdata,
                hovertemplate=hovertemplate,
            )
        )
    else:
        for sub_df, group_label in groups:
            fig.add_trace(_make_trace(sub_df, group_label or y))

    x_label = xlabel or ("Time (s)" if is_time else x)
    apply_theme(fig, resolved_theme, title=title or smart_title(x_label, y))
    fig.update_xaxes(title_text=x_label, tickformat=tick_format_for(xval(ref_df)))
    fig.update_yaxes(title_text=ylabel or y, tickformat=tick_format_for(ref_df[y]))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)
