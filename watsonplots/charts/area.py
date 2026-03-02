import itertools

import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..layout import apply_theme
from ..themes import Theme, get_theme
from ..utils import assign_colors, infer_axis_type, make_elapsed_xval, resolve_groups, smart_title


def area(
    data: DataFormats,
    *,
    x: str,
    y: str | list[str],
    labels: list[str] | None = None,
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
    labels:         Trace names when data is a list of DataFrames.
    stacked:        If True, subsequent traces are stacked on top of previous ones.
    segment_color:  Column whose value determines the fill color of each contiguous segment.
    """
    resolved_theme = get_theme(theme)
    y_cols = [y] if isinstance(y, str) else list(y)
    groups, ref_df = resolve_groups(data, labels)
    is_time, xval = make_elapsed_xval(x, ref_df[x])

    fig = go.Figure()
    for group_df, group_label in groups:
        elapsed_df = group_df.assign(**{x: xval(group_df)}).reset_index(drop=True)
        for y_col in y_cols:
            if segment_color:
                _add_segmented_traces(
                    fig, elapsed_df, x, y_col, segment_color, resolved_theme.colorway
                )
            else:
                fill = "tonexty" if (stacked and len(fig.data) > 0) else "tozeroy"
                fig.add_trace(
                    go.Scatter(
                        x=elapsed_df[x],
                        y=elapsed_df[y_col],
                        mode="lines",
                        name=group_label or y_col,
                        fill=fill,
                        line={"width": 1},
                    )
                )

    x_label = xlabel or ("Time (s)" if is_time else x)
    apply_theme(fig, resolved_theme, title=title or smart_title(x_label, y_cols[0]))
    fig.update_xaxes(type=infer_axis_type(xval(ref_df)), title_text=x_label)
    fig.update_yaxes(title_text=ylabel or (y if isinstance(y, str) else ""))
    fig.update_layout(showlegend=show_legend if len(fig.data) > 1 else False)
    return Chart(fig, resolved_theme)


def _iter_segments(df, col: str):
    """Yield (segment_df, value) for each contiguous run of equal values in col.
    Each segment includes one extra overlapping row to avoid visual gaps.
    """
    for value, row_iter in itertools.groupby(
        range(len(df)), key=lambda row_idx: df[col].iloc[row_idx]
    ):
        row_indices = list(row_iter)
        yield df.iloc[row_indices[0] : min(row_indices[-1] + 2, len(df))], value


def _add_segmented_traces(
    fig: go.Figure,
    df,
    x: str,
    y_col: str,
    segment_col: str,
    colorway: list[str],
) -> None:
    """Add one filled trace per contiguous segment, coloured by segment value."""
    unique_values = list(dict.fromkeys(df[segment_col]))
    color_for = assign_colors(unique_values, colorway)
    shown_in_legend: set = set()
    for segment_df, value in _iter_segments(df, segment_col):
        color = color_for[value]
        fig.add_trace(
            go.Scatter(
                x=segment_df[x],
                y=segment_df[y_col],
                mode="lines",
                name=str(value),
                fill="tozeroy",
                line={"width": 1, "color": color},
                fillcolor=color,
                showlegend=(value not in shown_in_legend),
                legendgroup=str(value),
            )
        )
        shown_in_legend.add(value)
