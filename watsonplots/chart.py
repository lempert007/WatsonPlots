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

    def add_y_threshold(
        self, value: float, *, label: str | None = None, color: str | None = None
    ) -> "Chart":
        self._fig.add_hline(
            y=value,
            line_color=color or _THRESHOLD_COLOR,
            line_dash=_THRESHOLD_DASH,
            line_width=_THRESHOLD_WIDTH,
            annotation_text=label,
            annotation_position="top right" if label else None,
        )
        return self

    def add_x_threshold(
        self, value: float, *, label: str | None = None, color: str | None = None
    ) -> "Chart":
        self._fig.add_vline(
            x=value,
            line_color=color or _THRESHOLD_COLOR,
            line_dash=_THRESHOLD_DASH,
            line_width=_THRESHOLD_WIDTH,
            annotation_text=label,
            annotation_position="top right" if label else None,
        )
        return self

    def add_annotation(self, x: float, y: float, text: str, *, color: str | None = None) -> "Chart":
        c = color or self._theme.font_color
        self._fig.add_annotation(
            x=x,
            y=y,
            text=text,
            showarrow=True,
            arrowhead=2,
            arrowwidth=1.5,
            arrowcolor=c,
            font=dict(color=c),
            bgcolor=self._theme.paper_bgcolor,
            bordercolor=c,
            borderwidth=1,
            ax=0,
            ay=-40,
        )
        return self

    def highlight(
        self,
        *,
        x_start=None,
        x_end=None,
        y_start=None,
        y_end=None,
        label: str | None = None,
        color: str | None = None,
    ) -> "Chart":
        fill = color or "#ffffff"
        ann = dict(text=label) if label else None
        if x_start is not None and x_end is not None:
            self._fig.add_vrect(
                x0=x_start,
                x1=x_end,
                fillcolor=fill,
                opacity=0.12,
                layer="below",
                line_width=0,
                annotation=ann,
            )
        elif y_start is not None and y_end is not None:
            self._fig.add_hrect(
                y0=y_start,
                y1=y_end,
                fillcolor=fill,
                opacity=0.12,
                layer="below",
                line_width=0,
                annotation=ann,
            )
        return self

    def __repr__(self) -> str:
        return f"<Chart theme='{self._theme.name}' traces={len(self._fig.data)}>"
