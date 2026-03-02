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


def _remap_yref(plotly_obj, new_yref: str) -> dict:
    """Serialize a Plotly shape or annotation and remap 'y' yref to the subplot's axis."""
    props = {key: value for key, value in plotly_obj.to_plotly_json().items() if value is not None}
    if props.get("yref") == "y":
        props["yref"] = new_yref
    return props


def _render_batch(charts: list[Chart], override_theme: Theme | None = None) -> bytes:
    """Render one or more charts as a single full-A4 PDF page."""
    figs = [c.to_fig() for c in charts]

    if override_theme is not None:
        for fig in figs:
            apply_theme(fig, override_theme, title=fig.layout.title.text or "")

    if len(charts) == 1:
        figs[0].update_layout(margin=_PDF_MARGIN)
        figs[0].update_xaxes(automargin=False)
        figs[0].update_yaxes(automargin=False)
        return figs[0].to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)

    chart_count = len(charts)
    first_layout = figs[0].layout
    subfig = make_subplots(rows=chart_count, cols=1, vertical_spacing=0.06)

    for subplot_row, fig in enumerate(figs, 1):
        for trace in fig.data:
            subfig.add_trace(trace, row=subplot_row, col=1)
        subfig.update_xaxes(row=subplot_row, col=1, **_axis_props(fig.layout.xaxis))
        subfig.update_yaxes(row=subplot_row, col=1, **_axis_props(fig.layout.yaxis))

        y_axis_ref = "y" if subplot_row == 1 else f"y{subplot_row}"
        for shape in fig.layout.shapes:
            subfig.add_shape(**_remap_yref(shape, y_axis_ref))
        for annotation in fig.layout.annotations:
            subfig.add_annotation(**_remap_yref(annotation, y_axis_ref))

    subfig.update_layout(
        paper_bgcolor=first_layout.paper_bgcolor or DARK.paper_bgcolor,
        plot_bgcolor=first_layout.plot_bgcolor or DARK.plot_bgcolor,
        font=first_layout.font.to_plotly_json(),
        margin={"l": _PDF_MARGIN["l"], "r": _PDF_MARGIN["r"], "t": 30, "b": 30},
    )
    if first_layout.colorway:
        subfig.update_layout(colorway=list(first_layout.colorway))
    subfig.update_xaxes(automargin=False)
    subfig.update_yaxes(automargin=False)

    return subfig.to_image(format="pdf", width=A4_WIDTH, height=A4_HEIGHT)


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
        pdf_bytes = _render_batch(charts[start : start + per_page], override)
        writer.add_page(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages[0])

    with open(path, "wb") as f:
        writer.write(f)
