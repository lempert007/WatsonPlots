import os

import plotly.graph_objects as go

from .themes import Theme


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

    def __repr__(self) -> str:
        return f"<Chart theme='{self._theme.name}' traces={len(self._fig.data)}>"
