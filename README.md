# watsonplots

Easy, high-quality interactive plots powered by Plotly.

```python
import watsonplots as wp
import pandas as pd

df = pd.read_csv("sales.csv", parse_dates=["date"])
wp.line(df, x="date", y="revenue", color="region", theme="watson").show()
```

## Install

```bash
# Core (interactive HTML charts)
pip install watsonplots

# With PDF export
pip install "watsonplots[pdf]"

# Development
pip install "watsonplots[dev]"
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra pdf
```

## Chart types

| Function | Description |
|---|---|
| `wp.line()` | Line chart with optional multi-series and smooth interpolation |
| `wp.area()` | Filled area chart, optionally stacked |
| `wp.scatter()` | Scatter plot with optional color grouping, size encoding, and hover data |
| `wp.histogram()` | Distribution histogram with optional grouping and overlay/stack modes |

## Usage

### Line

```python
wp.line(df, x="date", y="revenue", theme="watson").show()

# Multi-series via list
wp.line(df, x="date", y=["revenue", "cost"], theme="dark").show()

# Split by category column
wp.line(df, x="date", y="revenue", color="region", smooth=True).show()
```

### Area

```python
wp.area(df, x="date", y=["revenue", "cost"], stacked=True, theme="dark").show()
```

### Scatter

```python
wp.scatter(df, x="age", y="salary", color="dept",
           hover_data=["exp_years"], theme="light").show()

# Bubble chart (size encodes a third variable)
wp.scatter(df, x="age", y="salary", size="exp_years", color="dept").show()
```

### Histogram

```python
wp.histogram(df, x="score", color="group",
             bins=25, barmode="overlay", theme="watson").show()
```

## Chart object

Every chart function returns a `Chart` object:

```python
chart = wp.line(df, x="date", y="revenue")

chart.show()               # display in browser or notebook
chart.save("chart.html")   # write self-contained HTML file
chart.to_html()            # HTML string for embedding
chart.to_fig()             # raw plotly.graph_objects.Figure
chart.update(title="New")  # update layout, returns self
```

## PDF export

Requires `pip install "watsonplots[pdf]"` (`kaleido` + `pypdf`).

Pages are fixed **A4 portrait** (595 × 842 pt). When `per_page > 1`, charts are
composed using Plotly subplots so positioning is always exact.

```python
charts = [
    wp.line(df, x="date", y="revenue", theme="watson"),
    wp.histogram(df, x="score", color="group"),
    wp.scatter(df, x="age", y="salary", color="dept"),
    wp.area(df, x="date", y=["revenue", "cost"], stacked=True),
]

# One chart per page (default)
wp.save_pdf(charts, "report.pdf")

# Two charts per page, stacked vertically
wp.save_pdf(charts, "report.pdf", per_page=2)
```

## Themes

Four built-in themes, passed as a string or `Theme` object:

| Name | Description |
|---|---|
| `"dark"` | GitHub-style dark background |
| `"light"` | Clean light background |
| `"minimal"` | White background, serif font, invisible spines |
| `"watson"` | Deep navy with monospace font |

```python
wp.line(df, x="date", y="revenue", theme="watson")
wp.line(df, x="date", y="revenue", theme=wp.themes.DARK)

# Custom theme
from watsonplots import Theme

my_theme = Theme(
    name="corporate",
    paper_bgcolor="#003087",
    plot_bgcolor="#001f5b",
    font_color="#ffffff",
    font_family="Arial, sans-serif",
    font_size=14,
    gridcolor="#1a3a7a",
    gridwidth=0.5,
    zerolinecolor="#2a4a8a",
    linecolor="#1a3a7a",
    show_grid=True,
    colorway=["#FFD700", "#FF6B6B", "#4ECDC4"],
    margin={"l": 60, "r": 30, "t": 60, "b": 60},
    legend_bgcolor="#001f5b",
    legend_bordercolor="#1a3a7a",
    legend_borderwidth=1,
)
wp.line(df, x="date", y="revenue", theme=my_theme).show()
```

## Plotly escape hatch

Access the underlying `go.Figure` for anything the high-level API doesn't cover:

```python
fig = wp.line(df, x="date", y="revenue", theme="watson").to_fig()

fig.add_annotation(x="2024-06-01", y=15000, text="Peak", showarrow=True)
fig.write_html("annotated.html")
```

## Requirements

- Python ≥ 3.12
- `plotly ≥ 5.0`
- `pandas ≥ 2.0`
- PDF export: `kaleido ≥ 0.2`, `pypdf ≥ 4.0`
