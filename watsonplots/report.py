import os

from .chart import Chart


def save_html(
    charts: list[Chart],
    path: str | os.PathLike,
    *,
    title: str = "Report",
    offline: bool = False,
) -> None:
    """
    Export a list of Chart objects to a single scrollable HTML page.

    Plotly is loaded once (CDN by default, or bundled inline when offline=True).
    Each chart is full-width and interactive.

    Parameters
    ----------
    charts:  List of Chart objects to include.
    path:    Output file path. '.html' extension added if absent.
    title:   Page <title> and heading.
    offline: If True, bundle Plotly JS inline (larger file, no internet needed).
    """
    include_plotlyjs = True if offline else "cdn"

    divs = [
        chart.to_fig().to_html(
            full_html=False,
            include_plotlyjs=include_plotlyjs if i == 0 else False,
        )
        for i, chart in enumerate(charts)
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
      background: #0d1117;
      font-family: Inter, system-ui, sans-serif;
      padding: 40px 24px;
    }}
    h1 {{
      color: #e6edf3;
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
      background: #161b22;
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
