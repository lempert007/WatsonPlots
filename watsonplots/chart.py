import os

import plotly.graph_objects as go

from .themes import Theme


class ThreshouldValues:
    COLOR = "red"
    DASH = "dash"
    WIDTH = 1.5


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

    def add_threshold(self, value: float, *, label: str | None = None) -> "Chart":
        self._fig.add_hline(
            y=value,
            line_color=ThreshouldValues.COLOR,
            line_dash=ThreshouldValues.DASH,
            line_width=ThreshouldValues.WIDTH,
            annotation_text=label,
            annotation_position="top right" if label else None,
        )
        return self

    def __repr__(self) -> str:
        return f"<Chart theme='{self._theme.name}' traces={len(self._fig.data)}>"
