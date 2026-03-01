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
) -> Chart:
    """
    Create a scatter plot (or bubble chart when size= is provided).

    Parameters
    ----------
    data:       DataFrame, coercible, or a list of DataFrames.
    x:          Column for x-axis
    y:          Column for y-axis
    color:      Column name (single DataFrame) or list of labels (list of DataFrames).
    size:       Column whose values control marker diameter (bubble mode).
                Values are auto-scaled to an 8–60px range.
    hover_data: Extra columns to include in hover tooltips.
    opacity:    Marker opacity (0.0–1.0).
    """
    resolved_theme = get_theme(theme)
    groups, ref_df = resolve_groups(data, color)

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
            x=sub_df[x],
            y=sub_df[y],
            mode="markers",
            name=name,
            marker=marker,
            customdata=customdata,
            hovertemplate=hovertemplate,
        )

    fig = go.Figure()
    for sub_df, group_label in groups:
        fig.add_trace(_make_trace(sub_df, group_label or y))

    apply_theme(fig, resolved_theme, title=title or smart_title(x, y))
    fig.update_xaxes(title_text=xlabel or x, tickformat=tick_format_for(ref_df[x]))
    fig.update_yaxes(title_text=ylabel or y, tickformat=tick_format_for(ref_df[y]))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)
