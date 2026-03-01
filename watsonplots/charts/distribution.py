import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import resolve_groups
from ..layout import apply_theme
from ..themes import Theme, get_theme


def histogram(
    data: DataFormats,
    *,
    x: str,
    color: str | list[str] | None = None,
    bins: int | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str = "Count",
    theme: str | Theme = DEFAULT_THEME,
    barmode: str = "overlay",
    opacity: float = 0.7,
    show_legend: bool = True,
) -> Chart:
    """
    Create a histogram.

    Parameters
    ----------
    data:    DataFrame, coercible, or a list of DataFrames.
    x:       Column to compute distribution over.
    color:   Column name (single DataFrame) or list of labels (list of DataFrames).
    bins:    Number of bins. None lets Plotly auto-calculate.
    barmode: "overlay", "stack", or "group".
    opacity: Bar opacity (useful for overlay mode).
    """
    resolved_theme = get_theme(theme)
    groups, _ = resolve_groups(data, color)

    def _make_hist(sub_df, name: str) -> go.Histogram:
        kwargs: dict = {"x": sub_df[x], "name": name, "opacity": opacity}
        if bins is not None:
            kwargs["nbinsx"] = bins
        return go.Histogram(**kwargs)

    fig = go.Figure()
    for sub_df, group_label in groups:
        fig.add_trace(_make_hist(sub_df, group_label or x))

    apply_theme(fig, resolved_theme, title=title or f"Distribution of {x}")
    fig.update_layout(barmode=barmode)
    fig.update_xaxes(title_text=xlabel or x)
    fig.update_yaxes(title_text=ylabel)
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)
