import itertools

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
    mark_changes: str | None = None,
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
    data:         DataFrame, coercible (dict of lists, list of dicts),
                  or a list of DataFrames (one trace per DataFrame).
    x:            Column name for the x-axis.
    y:            Column name(s) for the y-axis. A list produces multiple traces.
    color:        Column name to split a single DataFrame into traces, or a list
                  of label strings when data is a list of DataFrames.
    mark_changes: Column name to watch for value changes. A hollow dot is placed
                  on the line at each point where the column value changes.
    title:        Chart title. Auto-generated if omitted.
    xlabel:       X-axis label override.
    ylabel:       Y-axis label override.
    theme:        Built-in theme name or Theme instance.
    mode:         Plotly scatter mode — "lines", "lines+markers", or "markers".
    smooth:       If True, use spline interpolation for smoother curves.
    show_legend:  Show the legend (auto-disabled for single-series charts).
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    line_shape = "spline" if smooth else "linear"
    groups, ref_df = resolve_groups(data, color)

    fig = go.Figure()
    for (sub_df, group_label), y_col in itertools.product(groups, y_cols):
        fig.add_trace(
            go.Scatter(
                x=sub_df[x],
                y=sub_df[y_col],
                mode=mode,
                name=group_label or y_col,
                line={"shape": line_shape},
            )
        )

    if mark_changes:
        change_markers = _build_change_markers(groups, x, y_cols, mark_changes, resolved_theme)
        if change_markers:
            fig.add_trace(change_markers)

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


def _build_change_markers(
    groups: list,
    x: str,
    y_cols: list[str],
    change_col: str,
    theme: Theme,
) -> go.Scatter | None:
    """Return a marker trace at each point where change_col changes value, or None."""
    xs, ys, labels = [], [], []
    for sub_df, _ in groups:
        rows = sub_df.reset_index(drop=True)
        for y_col in y_cols:
            for i in range(1, len(rows)):
                if rows[change_col].iloc[i] != rows[change_col].iloc[i - 1]:
                    xs.append(rows[x].iloc[i])
                    ys.append(rows[y_col].iloc[i])
                    labels.append(str(rows[change_col].iloc[i]))
    if not xs:
        return None
    return go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        name=change_col,
        marker={
            "size": 9,
            "color": theme.paper_bgcolor,
            "line": {"color": theme.font_color, "width": 2},
        },
        text=labels,
        hovertemplate=f"{change_col}: %{{text}}<extra></extra>",
        showlegend=False,
    )
