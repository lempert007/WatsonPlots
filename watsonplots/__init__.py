"""
watsonplots — Easy, high-quality interactive plots powered by Plotly.

Quick start
-----------
    import watsonplots as wp
    import pandas as pd

    df = pd.DataFrame({"date": [...], "value": [...]})
    wp.line(df, x="date", y="value", theme="dark").show()

Chart functions
---------------
    wp.line(data, *, x, y, color, theme, mode, smooth, show_legend, ...)
    wp.area(data, *, x, y, theme, stacked, show_legend, ...)
    wp.scatter(data, *, x, y, color, size, gradient_colors, theme, ...)
    wp.scatter3d(data, *, x, y, z, color, theme, ...)
    wp.line3d(data, *, x, y, z, color, theme, ...)
    wp.route(data, *, lat, lon, color, tile_url, theme, ...)

Chart methods
-------------
    chart.show()                  → display in notebook or browser
    chart.save("out.html")        → write HTML file
    chart.to_html()               → HTML string for embedding
    chart.to_fig()                → raw plotly.graph_objects.Figure
    chart.update(**layout_kwargs) → tweak layout, returns self
    chart.add_y_threshold(value)  → horizontal reference line
    chart.add_x_threshold(value)  → vertical reference line
    chart.highlight(x_start, x_end) → shaded region

Themes
------
    wp.themes.DARK / LIGHT / MINIMAL / WATSON
    wp.line(df, x=..., y=..., theme="watson")       # by name
    wp.line(df, x=..., y=..., theme=wp.themes.DARK)  # by object
    custom = wp.Theme(name="corp", ...)               # custom theme

Exports
-------
    wp.save_pdf([chart1, wp.Text("Section"), chart2], "report.pdf")
    wp.save_html([chart1, chart2], "report.html")
"""

from watsonplots import themes
from watsonplots.chart import Chart
from watsonplots.charts import area, line, line3d, route, scatter, scatter3d
from watsonplots.exceptions import (
    ColumnNotFoundError,
    ConstantColumnError,
    DataError,
    InvalidSliceRangeError,
    MissingDependencyError,
    MissingSeriesError,
    SyncError,
    TimeParseError,
    UnknownThemeError,
    WatsonPlotsError,
    YColumnMismatchError,
)
from watsonplots.exports import save_html, save_pdf
from watsonplots.sync import sync
from watsonplots.text import Text
from watsonplots.themes import Theme, get_theme

__all__ = [
    "line",
    "area",
    "scatter",
    "scatter3d",
    "line3d",
    "route",
    "Chart",
    "Text",
    "Theme",
    "themes",
    "get_theme",
    "save_pdf",
    "save_html",
    "sync",
    # Exceptions
    "WatsonPlotsError",
    "DataError",
    "SyncError",
    "UnknownThemeError",
    "MissingDependencyError",
    "InvalidSliceRangeError",
    "YColumnMismatchError",
    "MissingSeriesError",
    "ColumnNotFoundError",
    "ConstantColumnError",
    "TimeParseError",
]

__version__ = "0.1.0"
