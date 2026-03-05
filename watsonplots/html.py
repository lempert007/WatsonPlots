import os

import plotly.graph_objects as go

from .chart import Chart
from .layout import apply_theme
from .themes import DARK, Theme, get_theme


def save_html(
    charts: list[Chart],
    path: str | os.PathLike,
    *,
    title: str = "Report",
    theme: str | Theme | None = None,
) -> None:
    """
    Export a list of Chart objects to a single scrollable HTML page.

    Each chart is full-width and interactive.

    Parameters
    ----------
    charts:  List of Chart objects to include.
    path:    Output file path. '.html' extension added if absent.
    title:   Page <title> and heading.
    theme:   Override every chart's theme for the HTML output. Accepts a theme
             name string or Theme instance. The page background and font colors
             are derived from the same theme. Does not modify the Chart objects.
    """
    resolved_theme = get_theme(theme) if theme is not None else None
    page_theme = resolved_theme or DARK

    divs = [_render_chart(chart, i, resolved_theme) for i, chart in enumerate(charts)]

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: {page_theme.paper_bgcolor};
      font-family: {page_theme.font_family};
      padding: 40px 24px;
    }}
    h1 {{
      color: {page_theme.font_color};
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 32px;
      letter-spacing: 0.02em;
    }}
    .chart {{
      width: 100%;
      max-width: 1200px;
      margin: 0 auto 32px;
      border-radius: 8px;
      overflow: hidden;
      background: {page_theme.plot_bgcolor};
      box-shadow: 0 1px 3px rgba(0,0,0,.4);
    }}
    .chart > div {{ width: 100% !important; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  {''.join(f'<div class="chart">{div}</div>' for div in divs)}
</body>
</html>"""

    path = str(path)
    if not path.endswith(".html"):
        path += ".html"

    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def _render_chart(chart: Chart, index: int, theme: Theme | None) -> str:
    include_plotlyjs = index == 0

    if theme is None:
        return chart.to_fig().to_html(full_html=False, include_plotlyjs=include_plotlyjs)

    # Copy the figure so the original Chart object is never mutated
    fig = go.Figure(chart.to_fig().to_dict())
    apply_theme(fig, theme, title=fig.layout.title.text or "")
    return fig.to_html(full_html=False, include_plotlyjs=include_plotlyjs)
