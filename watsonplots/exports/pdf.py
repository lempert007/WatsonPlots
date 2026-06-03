import io
import os

from watsonplots.chart import Chart
from watsonplots.exceptions import MissingDependencyError
from watsonplots.exports._pdf_cover import extract_toc_entries, render_cover_page
from watsonplots.exports._pdf_page import build_pages, render_page
from watsonplots.text import Text
from watsonplots.themes import DARK, Theme, get_theme


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
        import pypdf  # optional dependency
    except ImportError as exc:
        raise MissingDependencyError("PDF export requires pypdf: pip install pypdf") from exc

    path = str(path)
    if not path.endswith(".pdf"):
        path += ".pdf"

    override = get_theme(theme) if theme is not None else None
    cover_theme = override or DARK

    pages = build_pages(charts, per_page)
    toc_entries = extract_toc_entries(charts)

    writer = pypdf.PdfWriter()
    cover_bytes = render_cover_page(toc_entries, cover_theme)
    writer.add_page(pypdf.PdfReader(io.BytesIO(cover_bytes)).pages[0])

    for page in pages:
        pdf_bytes = render_page(page, override, per_page)
        writer.add_page(pypdf.PdfReader(io.BytesIO(pdf_bytes)).pages[0])

    with open(path, "wb") as f:
        writer.write(f)
