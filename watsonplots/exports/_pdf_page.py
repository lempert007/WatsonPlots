from dataclasses import dataclass, field

import plotly.graph_objects as go

from watsonplots.chart import Chart
from watsonplots.exports._pdf_subplots import (
    apply_subplot_theme,
    compose_subplots,
    is_mapbox_fig,
    mapbox_fig_to_scatter_fig,
)
from watsonplots.layout import apply_theme
from watsonplots.text import Text
from watsonplots.themes import DARK, Theme

_A4_WIDTH = 595
_A4_HEIGHT = 842

_PDF_MARGIN = {"l": 80, "r": 30, "t": 60, "b": 80}
_PDF_LEGEND = dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0)
_HEADER_YSHIFT_START = 30  # px above plot top — must clear subplot-1 title (~20 px)
_PDF_AXIS_TITLE_SIZE = 10
_PDF_TICK_SIZE = 9


@dataclass
class _Page:
    header: list[Text] = field(default_factory=list)
    charts: list[Chart] = field(default_factory=list)


def build_pages(items: list, per_page: int) -> list[_Page]:
    pages: list[_Page] = []
    current = _Page()

    for item in items:
        if isinstance(item, Text):
            if current.charts:
                pages.append(current)
                current = _Page()
            current.header.append(item)
        else:
            current.charts.append(item)
            if len(current.charts) == per_page:
                pages.append(current)
                current = _Page()

    if current.charts or current.header:
        pages.append(current)

    return pages


def _header_height(texts: list[Text]) -> int:
    total = _HEADER_YSHIFT_START
    for item in texts:
        total += int(item.pdf_font_size() * 1.6)
    return total + 10


def _add_page_header(fig: go.Figure, texts: list[Text], font_color: str, font_family: str) -> None:
    y_offset = _HEADER_YSHIFT_START
    for text_item in reversed(texts):
        fig.add_annotation(
            text=text_item.text,
            x=0.0,
            y=1.0,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            yshift=y_offset,
            font=dict(size=text_item.pdf_font_size(), color=font_color, family=font_family),
        )
        y_offset += int(text_item.pdf_font_size() * 1.6)


def render_text_only_page(texts: list[Text], override_theme: Theme | None) -> bytes:
    t = override_theme or DARK
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=t.paper_bgcolor,
        plot_bgcolor=t.plot_bgcolor,
        font=dict(color=t.font_color, family=t.font_family),
        margin={"l": _PDF_MARGIN["l"], "r": _PDF_MARGIN["r"], "t": 80, "b": _PDF_MARGIN["b"]},
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    _add_page_header(fig, texts, t.font_color, t.font_family)
    return fig.to_image(format="pdf", width=_A4_WIDTH, height=_A4_HEIGHT)


def render_page(page: _Page, override_theme: Theme | None, per_page: int) -> bytes:
    if not page.charts:
        return render_text_only_page(page.header, override_theme)

    figs = [
        mapbox_fig_to_scatter_fig(fig) if is_mapbox_fig(fig) else fig
        for fig in (c.to_fig() for c in page.charts)
    ]
    if override_theme:
        for fig in figs:
            apply_theme(fig, override_theme, title=fig.layout.title.text or "")

    use_full_page = len(figs) == 1 and per_page == 1
    top_margin = _PDF_MARGIN["t"] if use_full_page else 30
    if page.header:
        top_margin += _header_height(page.header)

    if use_full_page:
        fig = go.Figure(figs[0].to_dict())
        fig.update_layout(margin={**_PDF_MARGIN, "t": top_margin})
    else:
        fig = compose_subplots(figs, total_rows=per_page)
        for row in range(len(figs) + 1, per_page + 1):
            fig.update_xaxes(visible=False, row=row, col=1)
            fig.update_yaxes(visible=False, row=row, col=1)
        apply_subplot_theme(fig, source_layout=figs[0].layout, pdf_margin=_PDF_MARGIN)
        fig.update_layout(
            margin={
                "l": _PDF_MARGIN["l"],
                "r": _PDF_MARGIN["r"],
                "t": top_margin,
                "b": _PDF_MARGIN["b"],
            }
        )

    if page.header:
        source = override_theme or DARK
        font_color = figs[0].layout.font.color or source.font_color
        font_family = figs[0].layout.font.family or source.font_family
        _add_page_header(fig, page.header, font_color, font_family)

    fig.update_layout(legend=_PDF_LEGEND)
    fig.update_xaxes(
        automargin=False, title_font_size=_PDF_AXIS_TITLE_SIZE, tickfont_size=_PDF_TICK_SIZE
    )
    fig.update_yaxes(
        automargin=False, title_font_size=_PDF_AXIS_TITLE_SIZE, tickfont_size=_PDF_TICK_SIZE
    )
    return fig.to_image(format="pdf", width=_A4_WIDTH, height=_A4_HEIGHT)
