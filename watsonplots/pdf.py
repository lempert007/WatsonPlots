import io
import os

from plotly.subplots import make_subplots

from .chart import Chart
from .consts import A4_HEIGHT, A4_WIDTH, SKIP_AXIS_KEYS
from .layout import apply_theme
from .themes import DARK, Theme, get_theme

_PDF_MARGIN = {"l": 80, "r": 30, "t": 60, "b": 60}


def _axis_props(axis) -> dict:
    return {
        key: value
        for key, value in axis.to_plotly_json().items()
        if key not in SKIP_AXIS_KEYS and value is not None
    }


def _remap_axis_refs(plotly_obj, subplot_row: int) -> dict:
    props = {key: value for key, value in plotly_obj.to_plotly_json().items() if value is not None}
    suffix = "" if subplot_row == 1 else str(subplot_row)
    if props.get("xref") == "x":
        props["xref"] = f"x{suffix}"
    if props.get("yref") == "y":
        props["yref"] = f"y{suffix}"
    if props.get("yref") == "paper":
        props["yref"] = f"y{suffix} domain"
    return props


def _render_batch(
    charts: list[Chart], override_theme: Theme | None = None, per_page: int = 1
) -> bytes:
    figs = [c.to_fig() for c in charts]
    if override_theme is not None:
        for fig in figs:
            apply_theme(fig, override_theme, title=fig.layout.title.text or "")
    if per_page == 1:
        return _render_single_to_pdf(figs[0])
    return _render_multi_to_pdf(figs, total_rows=per_page)


def _render_single_to_pdf(fig) -> bytes:
    fig.update_layout(margin=_PDF_MARGIN)
    fig.update_xaxes(automargin=False)
    fig.update_yaxes(automargin=False)
    return fig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


def _render_multi_to_pdf(figs, total_rows: int | None = None) -> bytes:
    subfig = _compose_subplots(figs, total_rows=total_rows)
    _apply_subplot_theme(subfig, source_layout=figs[0].layout)
    subfig.update_xaxes(automargin=False)
    subfig.update_yaxes(automargin=False)
    return subfig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


def _compose_subplots(figs, total_rows: int | None = None):
    rows = total_rows if total_rows is not None else len(figs)
    titles = [fig.layout.title.text or "" for fig in figs] + [""] * (rows - len(figs))
    subfig = make_subplots(rows=rows, cols=1, vertical_spacing=0.10, subplot_titles=titles)
    for subplot_row, fig in enumerate(figs, 1):
        for trace in fig.data:
            subfig.add_trace(trace, row=subplot_row, col=1)
        subfig.update_xaxes(row=subplot_row, col=1, **_axis_props(fig.layout.xaxis))
        subfig.update_yaxes(row=subplot_row, col=1, **_axis_props(fig.layout.yaxis))
        for shape in fig.layout.shapes:
            subfig.add_shape(**_remap_axis_refs(shape, subplot_row))
        for annotation in fig.layout.annotations:
            subfig.add_annotation(**_remap_axis_refs(annotation, subplot_row))
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
        margin={"l": _PDF_MARGIN["l"], "r": _PDF_MARGIN["r"], "t": 30, "b": 30},
    )
    if source_layout.colorway:
        subfig.update_layout(colorway=list(source_layout.colorway))


def save_pdf(
    charts: list[Chart],
    path: str | os.PathLike,
    *,
    per_page: int = 1,
    theme: str | Theme | None = None,
) -> None:
    """
    Export a list of Chart objects to a single multi-page PDF.

    Pages are fixed A4 portrait (595 × 842 pt). When per_page > 1 charts
    are composed as Plotly subplots, so positioning is always exact.

    Requires kaleido and pypdf:  pip install "watsonplots[pdf]"

    Parameters
    ----------
    charts:   List of Chart objects to include.
    path:     Output file path. '.pdf' extension added if absent.
    per_page: Charts stacked vertically per page (default 1).
    theme:    Override theme for all charts (name string or Theme object).
              If omitted each chart keeps its own theme.
    """
    try:
        import pypdf  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError("PDF export requires pypdf: pip install pypdf") from exc

    path = str(path)
    if not path.endswith(".pdf"):
        path += ".pdf"

    override = get_theme(theme) if theme is not None else None

    writer = pypdf.PdfWriter()
    for start in range(0, len(charts), per_page):
        pdf_bytes = _render_batch(charts[start : start + per_page], override, per_page=per_page)
        writer.add_page(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages[0])

    with open(path, "wb") as f:
        writer.write(f)
