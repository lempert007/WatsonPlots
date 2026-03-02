import os

import plotly.graph_objects as go

from .themes import Theme

_THRESHOLD_COLOR = "red"
_THRESHOLD_DASH = "dash"
_THRESHOLD_WIDTH = 1.5


class Chart:
    """
    Thin wrapper around a Plotly Figure. All chart functions return this type.

    Methods
    -------
    .show()                → display in notebook or browser, returns self
    .save(path)            → write HTML file, returns self
    .to_html()             → HTML string for embedding
    .to_fig()              → raw go.Figure for full Plotly control
    .update(**kwargs)      → fig.update_layout passthrough, returns self
    """

    def __init__(self, fig: go.Figure, theme: Theme) -> None:
        self._fig = fig
        self._theme = theme

    def show(self) -> "Chart":
        self._fig.show()
        return self

    def save(self, path: str | os.PathLike, *, include_plotlyjs: bool | str = "cdn") -> "Chart":
        path = str(path)
        if not path.endswith(".html"):
            path += ".html"
        self._fig.write_html(path, include_plotlyjs=include_plotlyjs)
        return self

    def to_html(self, *, include_plotlyjs: bool | str = "cdn") -> str:
        return self._fig.to_html(include_plotlyjs=include_plotlyjs)

    def to_fig(self) -> go.Figure:
        return self._fig

    def update(self, **kwargs) -> "Chart":
        self._fig.update_layout(**kwargs)
        return self

    def add_threshold(self, value: float, *, slope: float = 0, label: str | None = None) -> "Chart":
        """
        Add a red dashed threshold line.

        value: y-value of the line (left edge when slope != 0).
        slope: total y change from the left to the right edge of the chart.
               0 (default) draws a flat horizontal line.
        label: optional annotation text shown at the right end of the line.
        """
        line_style = {"color": _THRESHOLD_COLOR, "dash": _THRESHOLD_DASH, "width": _THRESHOLD_WIDTH}
        if slope == 0:
            self._fig.add_hline(
                y=value,
                line_color=_THRESHOLD_COLOR,
                line_dash=_THRESHOLD_DASH,
                line_width=_THRESHOLD_WIDTH,
                annotation_text=label,
                annotation_position="top right" if label else None,
            )
        else:
            self._fig.add_shape(
                type="line",
                x0=0,
                y0=value,
                x1=1,
                y1=value + slope,
                xref="paper",
                yref="y",
                line=line_style,
            )
            if label:
                self._fig.add_annotation(
                    x=1,
                    y=value + slope,
                    xref="paper",
                    yref="y",
                    text=label,
                    showarrow=False,
                    xanchor="right",
                    font={"color": _THRESHOLD_COLOR},
                )
        return self

    def __repr__(self) -> str:
        return f"<Chart theme='{self._theme.name}' traces={len(self._fig.data)}>"
