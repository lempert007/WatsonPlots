import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..defaults import infer_axis_type, resolve_groups, smart_title
from ..layout import apply_theme
from ..themes import Theme, get_theme


def area(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
    color: str | list[str] | None = None,
    segment_color: str | None = None,
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
    data:           DataFrame, coercible, or a list of DataFrames.
    stacked:        If True, subsequent traces are stacked on top of previous ones.
    color:          Column name (single DataFrame) or list of labels (list of DataFrames).
    segment_color:  Column name whose value determines the fill color of each contiguous
                    segment. When the column value changes, the area color changes.
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    groups, ref_df = resolve_groups(data, color)

    fig = go.Figure()
    trace_count = 0
    for sub_df, group_label in groups:
        for y_col in y_cols:
            if segment_color:
                _add_segmented_traces(
                    fig,
                    sub_df.reset_index(drop=True),
                    x,
                    y_col,
                    segment_color,
                    resolved_theme.colorway,
                )
            else:
                fill = "tonexty" if (stacked and trace_count > 0) else "tozeroy"
                fig.add_trace(
                    go.Scatter(
                        x=sub_df[x],
                        y=sub_df[y_col],
                        mode="lines",
                        name=group_label or y_col,
                        fill=fill,
                        line={"width": 1},
                    )
                )
            trace_count += 1

    apply_theme(fig, resolved_theme, title=title or smart_title(x, y_cols[0]))
    fig.update_xaxes(type=infer_axis_type(ref_df[x]), title_text=xlabel or x)
    fig.update_yaxes(title_text=ylabel or (y if isinstance(y, str) else ""))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def _iter_segments(df: pd.DataFrame, col: str):
    """Yield (segment_df, value) for each contiguous run of equal values in col.

    Each segment includes one extra overlapping row at the end to avoid visual
    gaps between adjacent filled areas.
    """
    i = 0
    while i < len(df):
        val = df[col].iloc[i]
        j = i + 1
        while j < len(df) and df[col].iloc[j] == val:
            j += 1
        end = j + 1 if j < len(df) else j  # one-row overlap to close the gap
        yield df.iloc[i:end], val
        i = j


def _add_segmented_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y_col: str,
    segment_col: str,
    colorway: list[str],
) -> None:
    """Add one filled trace per contiguous segment, coloured by segment value."""
    unique_vals = list(dict.fromkeys(df[segment_col]))
    color_for = {val: colorway[i % len(colorway)] for i, val in enumerate(unique_vals)}
    shown_in_legend: set = set()
    for seg_df, val in _iter_segments(df, segment_col):
        seg_color = color_for[val]
        fig.add_trace(
            go.Scatter(
                x=seg_df[x],
                y=seg_df[y_col],
                mode="lines",
                name=str(val),
                fill="tozeroy",
                line={"width": 1, "color": seg_color},
                fillcolor=seg_color,
                showlegend=(val not in shown_in_legend),
                legendgroup=str(val),
            )
        )
        shown_in_legend.add(val)
