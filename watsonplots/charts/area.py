import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..themes import Theme, get_theme
from ..utils import assign_colors, finalize_axes, make_elapsed_xval, to_traces

_FILL_ZERO = "tozeroy"
_FILL_STACK = "tonexty"
_AREA_LINE_WIDTH = 1


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
    traces = to_traces(data, labels)
    ref_df = traces[0][0]
    is_time, xval = make_elapsed_xval(x, ref_df[x])

    fig = go.Figure()
    for group_df, group_label in traces:
        x_vals = xval(group_df)
        for y_col in y_cols:
            if segment_color:
                _add_segmented_traces(
                    fig,
                    group_df.assign(**{x: x_vals}),
                    x,
                    y_col,
                    segment_color,
                    resolved_theme.colorway,
                )
            else:
                fill = _FILL_STACK if (stacked and len(fig.data) > 0) else _FILL_ZERO
                fig.add_trace(
                    go.Scatter(
                        x=x_vals,
                        y=group_df[y_col],
                        mode="lines",
                        name=group_label or y_col,
                        fill=fill,
                        line={"width": _AREA_LINE_WIDTH},
                    )
                )

    finalize_axes(
        fig,
        resolved_theme,
        ref_x=xval(ref_df),
        ref_y=ref_df[y_cols[0]],
        x_col=x,
        y_col=y_cols[0],
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        is_time=is_time,
        show_legend=show_legend,
    )
    return Chart(fig, resolved_theme)


def _iter_segments(df, col: str):
    """Yield (segment_df, value) for each contiguous run of equal values in col.
    Each segment includes one extra overlapping row to avoid visual gaps.
    """
    df = df.reset_index(drop=True)
    runs = df[col].ne(df[col].shift()).cumsum()
    for _, group in df.groupby(runs, sort=False):
        end = min(group.index[-1] + 2, len(df))
        yield df.iloc[group.index[0] : end], group[col].iloc[0]


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
                fill=_FILL_ZERO,
                line={"width": _AREA_LINE_WIDTH, "color": color},
                fillcolor=color,
                showlegend=(value not in shown_in_legend),
                legendgroup=str(value),
            )
        )
        shown_in_legend.add(value)
