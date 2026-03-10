import os

import plotly.graph_objects as go

from .chart import Chart
from .layout import apply_theme
from .text import Text
from .themes import DARK, Theme, get_theme


def save_html(
    charts: list[Chart | Text],
    path: str | os.PathLike,
    *,
    title: str = "Report",
    theme: str | Theme | None = None,
) -> None:
    """
    Export a list of Chart and Text objects to a single scrollable HTML page.

    Each chart is full-width and interactive. Text objects render as section
    titles (default) or body paragraphs (variant="body").

    Parameters
    ----------
    charts:  List of Chart and/or Text objects to include.
    path:    Output file path. '.html' extension added if absent.
    title:   Page <title> and heading.
    theme:   Override every chart's theme for the HTML output. Accepts a theme
             name string or Theme instance. The page background and font colors
             are derived from the same theme. Does not modify the Chart objects.
    """
    resolved_theme = get_theme(theme) if theme is not None else None
    page_theme = resolved_theme or DARK

    charts_only = [item for item in charts if isinstance(item, Chart)]
    rendered = [_render_chart(c, i, resolved_theme) for i, c in enumerate(charts_only)]
    rendered_iter = iter(rendered)

    body_parts = [
        (
            item.html_tag()
            if isinstance(item, Text)
            else f'<div class="chart">{next(rendered_iter)}</div>'
        )
        for item in charts
    ]

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
    .block-title {{
      color: {page_theme.font_color};
      font-size: 1.35rem;
      font-weight: 700;
      max-width: 1200px;
      margin: 44px auto 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid {page_theme.gridcolor};
      letter-spacing: -0.01em;
    }}
    .block-text {{
      color: {page_theme.font_color};
      font-size: 0.9rem;
      line-height: 1.75;
      max-width: 1200px;
      margin: 6px auto 24px;
      text-align: left;
      opacity: 0.72;
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
  {''.join(body_parts)}
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
