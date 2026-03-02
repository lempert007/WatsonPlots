import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import resolve_groups, smart_title
from ..layout import apply_theme
from ..themes import Theme, get_theme


def histogram(
    data: DataFormats,
    *,
    x: str,
    bins: int | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    barmode: str = "overlay",
    opacity: float = 0.75,
    show_legend: bool = True,
) -> Chart:
    """
    Create a distribution histogram.

    Parameters
    ----------
    data:       DataFrame, coercible, or a list of DataFrames (one trace per DataFrame).
    x:          Column to plot the distribution of.
    bins:       Number of bins. Auto-determined by Plotly if omitted.
    barmode:    How multiple traces are drawn — "overlay", "stack", or "group".
    opacity:    Bar opacity (0.0–1.0).
    show_legend: Show the legend (auto-disabled for single-series charts).
    """
    resolved_theme = get_theme(theme)
    groups, _ = resolve_groups(data)

    def _make_trace(group_df, name: str) -> go.Histogram:
        trace_kwargs: dict = {"x": group_df[x], "name": name, "opacity": opacity}
        if bins is not None:
            trace_kwargs["nbinsx"] = bins
        return go.Histogram(**trace_kwargs)

    fig = go.Figure()
    for group_df, group_label in groups:
        fig.add_trace(_make_trace(group_df, group_label or x))

    apply_theme(fig, resolved_theme, title=title or smart_title(None, x))
    fig.update_xaxes(title_text=xlabel or x)
    fig.update_yaxes(title_text=ylabel or "Count")
    fig.update_layout(barmode=barmode, showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)
