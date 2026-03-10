import io
import os
from dataclasses import dataclass, field

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .chart import Chart
from .consts import A4_HEIGHT, A4_WIDTH, SKIP_AXIS_KEYS
from .layout import apply_theme
from .text import Text
from .themes import DARK, Theme, get_theme

_PDF_MARGIN = {"l": 80, "r": 30, "t": 60, "b": 80}

_REPORT_TITLE = "Flight Report"

_COVER_TITLE_SIZE = 36
_COVER_DATE_SIZE = 14
_COVER_TOC_HDR_SIZE = 16
_COVER_TOC_ITEM_SIZE = 13
_COVER_TOC_LINE_GAP = 0.055  # paper-fraction spacing per TOC entry

# Horizontal legend below the chart — frees up full chart width, no top collision
_PDF_LEGEND = dict(
    orientation="h",
    yanchor="top",
    y=-0.08,
    xanchor="left",
    x=0,
)

_HEADER_YSHIFT_START = 30  # px above plot top — must clear subplot-1 title (~20 px)
_PDF_AXIS_TITLE_SIZE = 10  # axis label font size for PDF
_PDF_TICK_SIZE = 9  # tick label font size for PDF


# ── Cover page ────────────────────────────────────────────────────────────────


def _extract_toc_entries(items: list) -> list[str]:
    """Return heading-level Text items as TOC section names (body text excluded)."""
    return [item.text for item in items if isinstance(item, Text) and not item._is_body()]


def _render_cover_page(toc_entries: list[str], theme: Theme) -> bytes:
    from datetime import date  # noqa: PLC0415

    date_str = date.today().strftime("%B %d, %Y")
    font = dict(color=theme.font_color, family=theme.font_family)

    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=theme.paper_bgcolor,
        plot_bgcolor=theme.plot_bgcolor,
        font=font,
        margin={"l": 80, "r": 80, "t": 80, "b": 80},
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    fig.add_annotation(
        text=_REPORT_TITLE,
        x=0.5,
        y=0.85,
        xref="paper",
        yref="paper",
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_TITLE_SIZE},
    )
    fig.add_annotation(
        text=date_str,
        x=0.5,
        y=0.77,
        xref="paper",
        yref="paper",
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_DATE_SIZE},
    )
    fig.add_shape(
        type="line",
        x0=0.05,
        x1=0.95,
        y0=0.71,
        y1=0.71,
        xref="paper",
        yref="paper",
        line=dict(color=theme.gridcolor, width=1),
    )
    fig.add_annotation(
        text="Table of Contents",
        x=0.1,
        y=0.66,
        xref="paper",
        yref="paper",
        xanchor="left",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_TOC_HDR_SIZE},
    )

    y_pos = 0.59
    for index, entry in enumerate(toc_entries, 1):
        fig.add_annotation(
            text=f"{index}.  {entry}",
            x=0.12,
            y=y_pos,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="middle",
            showarrow=False,
            font={**font, "size": _COVER_TOC_ITEM_SIZE},
        )
        underline_y = y_pos - (_COVER_TOC_ITEM_SIZE * 0.5 / (A4_HEIGHT - 160))
        fig.add_shape(
            type="line",
            x0=0.12,
            x1=0.88,
            y0=underline_y,
            y1=underline_y,
            xref="paper",
            yref="paper",
            line=dict(color=theme.gridcolor, width=0.5),
        )
        y_pos -= _COVER_TOC_LINE_GAP

    return fig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


# ── Page model ────────────────────────────────────────────────────────────────


@dataclass
class _Page:
    header: list[Text] = field(default_factory=list)
    charts: list[Chart] = field(default_factory=list)


def _build_pages(items: list, per_page: int) -> list[_Page]:
    pages: list[_Page] = []
    current = _Page()

    for item in items:
        if isinstance(item, Text):
            if current.charts:  # text mid-batch → flush, start fresh
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


# ── Header annotations ────────────────────────────────────────────────────────


def _header_height(texts: list[Text]) -> int:
    total = _HEADER_YSHIFT_START
    for item in texts:
        total += int(item.pdf_font_size() * 1.6)
    return total + 10


def _add_page_header(fig, texts: list[Text], font_color: str, font_family: str) -> None:
    y_offset = _HEADER_YSHIFT_START
    for text_item in reversed(texts):  # closest-to-chart item first
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


# ── Axis helpers (unchanged) ──────────────────────────────────────────────────


def _axis_props(axis) -> dict:
    return {
        key: value
        for key, value in axis.to_plotly_json().items()
        if key not in SKIP_AXIS_KEYS and value is not None
    }


def _remap_axis_refs(plotly_obj, subplot_row: int) -> dict:
    props = {key: value for key, value in plotly_obj.to_plotly_json().items() if value is not None}
    suffix = "" if subplot_row == 1 else str(subplot_row)

    xref = props.get("xref", "")
    if xref == "x":
        props["xref"] = f"x{suffix}"
    elif xref == "x domain":
        props["xref"] = f"x{suffix} domain"

    yref = props.get("yref", "")
    if yref == "y":
        props["yref"] = f"y{suffix}"
    elif yref in ("y domain", "paper"):
        props["yref"] = f"y{suffix} domain"

    return props


# ── Figure composition helpers ────────────────────────────────────────────────

_3D_TRACE_TYPES = {"scatter3d", "surface", "mesh3d", "cone", "streamtube", "isosurface", "volume"}


def _is_3d_fig(fig) -> bool:
    return any(type(t).__name__.lower() in _3D_TRACE_TYPES for t in fig.data)


def _compose_subplots(figs, total_rows: int | None = None):
    rows = total_rows if total_rows is not None else len(figs)
    titles = [fig.layout.title.text or "" for fig in figs] + [""] * (rows - len(figs))

    fig_is_3d = [_is_3d_fig(fig) for fig in figs]
    specs = [
        [{"type": "scene"}] if (i < len(fig_is_3d) and fig_is_3d[i]) else [{"type": "xy"}]
        for i in range(rows)
    ]

    subfig = make_subplots(
        rows=rows, cols=1, vertical_spacing=0.10, subplot_titles=titles, specs=specs
    )
    for subplot_row, fig in enumerate(figs, 1):
        for trace in fig.data:
            subfig.add_trace(trace, row=subplot_row, col=1)
        if not fig_is_3d[subplot_row - 1]:
            subfig.update_xaxes(row=subplot_row, col=1, **_axis_props(fig.layout.xaxis))
            subfig.update_yaxes(row=subplot_row, col=1, **_axis_props(fig.layout.yaxis))
            for shape in fig.layout.shapes:
                subfig.add_shape(**_remap_axis_refs(shape, subplot_row))
            for annotation in fig.layout.annotations:
                subfig.add_annotation(**_remap_axis_refs(annotation, subplot_row))
            for image in fig.layout.images:
                subfig.add_layout_image(**_remap_axis_refs(image, subplot_row))
    return subfig


def _apply_subplot_theme(subfig, source_layout) -> None:
    font_color = source_layout.font.color or DARK.font_color
    font_family = source_layout.font.family or DARK.font_family
    for annotation in subfig.layout.annotations:
        annotation.update(font=dict(color=font_color, family=font_family))
    subfig.update_layout(
        paper_bgcolor=source_layout.paper_bgcolor or DARK.paper_bgcolor,
        plot_bgcolor=source_layout.plot_bgcolor or DARK.plot_bgcolor,
        font=source_layout.font.to_plotly_json(),
        margin={"l": _PDF_MARGIN["l"], "r": _PDF_MARGIN["r"], "t": 30, "b": _PDF_MARGIN["b"]},
    )
    if source_layout.colorway:
        subfig.update_layout(colorway=list(source_layout.colorway))


# ── Page rendering ────────────────────────────────────────────────────────────


def _render_text_only_page(texts: list[Text], override_theme: Theme | None) -> bytes:
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
    return fig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


def _render_page(page: _Page, override_theme: Theme | None, per_page: int) -> bytes:
    if not page.charts:
        return _render_text_only_page(page.header, override_theme)

    figs = [c.to_fig() for c in page.charts]
    if override_theme:
        for fig in figs:
            apply_theme(fig, override_theme, title=fig.layout.title.text or "")

    # Single chart filling the full page only when per_page==1.
    # When per_page>1 (even if only 1 chart landed on this page), keep
    # consistent proportional sizing via the subplot layout.
    use_full_page = len(figs) == 1 and per_page == 1
    top_margin = _PDF_MARGIN["t"] if use_full_page else 30
    if page.header:
        top_margin += _header_height(page.header)

    if use_full_page:
        fig = go.Figure(figs[0].to_dict())
        fig.update_layout(margin={**_PDF_MARGIN, "t": top_margin})
    else:
        fig = _compose_subplots(figs, total_rows=per_page)
        # Hide axes in unfilled rows so they don't render as blank chart areas
        for row in range(len(figs) + 1, per_page + 1):
            fig.update_xaxes(visible=False, row=row, col=1)
            fig.update_yaxes(visible=False, row=row, col=1)
        _apply_subplot_theme(fig, source_layout=figs[0].layout)
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
    return fig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


# ── Public API ────────────────────────────────────────────────────────────────


def save_pdf(
    charts: list[Chart | Text],
    path: str | os.PathLike,
    *,
    per_page: int = 1,
    theme: str | Theme | None = None,
) -> None:
    """
    Export a list of Chart and Text objects to a single multi-page PDF.

    Pages are fixed A4 portrait (595 × 842 pt). Text objects act as section
    headers: they force a page break and appear as margin annotations above
    the charts on the following page, taking no chart space.

    Requires kaleido and pypdf:  pip install "watsonplots[pdf]"

    Parameters
    ----------
    charts:   List of Chart and/or Text objects.
    path:     Output file path. '.pdf' extension added if absent.
    per_page: Charts stacked vertically per page (default 1).
    theme:    Override theme for all charts (name string or Theme object).
    """
    try:
        import pypdf  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError("PDF export requires pypdf: pip install pypdf") from exc

    path = str(path)
    if not path.endswith(".pdf"):
        path += ".pdf"

    override = get_theme(theme) if theme is not None else None
    cover_theme = override or DARK

    pages = _build_pages(charts, per_page)
    toc_entries = _extract_toc_entries(charts)

    writer = pypdf.PdfWriter()
    cover_bytes = _render_cover_page(toc_entries, cover_theme)
    writer.add_page(pypdf.PdfReader(io.BytesIO(cover_bytes)).pages[0])

    for page in pages:
        pdf_bytes = _render_page(page, override, per_page)
        writer.add_page(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages[0])

    with open(path, "wb") as f:
        writer.write(f)
