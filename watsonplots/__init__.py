"""
watsonplots — Easy, high-quality interactive plots powered by Plotly.

Quick start
-----------
    import watsonplots as wp
    import pandas as pd

    df = pd.DataFrame({"date": [...], "value": [...]})
    wp.line(df, x="date", y="value", title="My Chart", theme="dark").show()

Chart functions (all return a Chart object)
-------------------------------------------
    wp.line(data, *, x, y, title, xlabel, ylabel, theme, mode, smooth, show_legend)
    wp.area(data, *, x, y, title, xlabel, ylabel, theme, stacked, show_legend)
    wp.histogram(data, *, x, bins, title, xlabel, ylabel, theme, barmode, opacity, show_legend)

Chart object methods
--------------------
    chart.show()                 → display in notebook or browser
    chart.save("output.html")    → write HTML file
    chart.to_html()              → HTML string for embedding
    chart.to_fig()               → raw plotly.graph_objects.Figure
    chart.update(**layout_kwargs) → tweak layout, returns self

Themes
------
    wp.themes.DARK / LIGHT / MINIMAL / WATSON
    wp.line(df, x=..., y=..., theme="watson")   # by name
    wp.line(df, x=..., y=..., theme=wp.themes.DARK)  # by object
    custom = wp.Theme(name="corp", ...)           # custom theme
"""

from . import themes
from .chart import Chart
from .charts import area, histogram, line, scatter
from .pdf import save_pdf
from .report import save_html
from .sync import sync
from .themes import Theme, get_theme

__all__ = [
    "line",
    "area",
    "scatter",
    "histogram",
    "Chart",
    "Theme",
    "themes",
    "get_theme",
    "save_pdf",
    "save_html",
    "sync",
]

__version__ = "0.1.0"
