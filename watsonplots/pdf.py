import io
import os

from .chart import Chart
from .consts import A4_H, A4_W, SKIP_AXIS_KEYS
from .themes import Theme, get_theme


def _axis_props(axis) -> dict:
    return {k: v for k, v in axis.to_plotly_json().items()
            if k not in SKIP_AXIS_KEYS and v is not None}


def _render_batch(charts: list[Chart], override_theme: Theme | None = None) -> bytes:
    """Render one or more charts as a single full-A4 PDF page."""
    figs = [c.to_fig() for c in charts]

    if override_theme is not None:
        from .layout import apply_theme
        for fig in figs:
            apply_theme(fig, override_theme, title=fig.layout.title.text or "")

    if len(charts) == 1:
        return figs[0].to_image(format="pdf", width=A4_W, height=A4_H)

    from plotly.subplots import make_subplots

    n = len(charts)
    base = figs[0].layout

    subfig = make_subplots(rows=n, cols=1, vertical_spacing=0.06)

    for row, fig in enumerate(figs, 1):
        for trace in fig.data:
            subfig.add_trace(trace, row=row, col=1)
        subfig.update_xaxes(row=row, col=1, **_axis_props(fig.layout.xaxis))
        subfig.update_yaxes(row=row, col=1, **_axis_props(fig.layout.yaxis))

    subfig.update_layout(
        paper_bgcolor=base.paper_bgcolor or "#0d1117",
        plot_bgcolor=base.plot_bgcolor or "#161b22",
        font=base.font.to_plotly_json(),
        margin={"l": 60, "r": 30, "t": 30, "b": 30},
    )
    if base.colorway:
        subfig.update_layout(colorway=list(base.colorway))

    return subfig.to_image(format="pdf", width=A4_W, height=A4_H)


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
        import pypdf
    except ImportError:
        raise ImportError("PDF export requires pypdf: pip install pypdf")

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
