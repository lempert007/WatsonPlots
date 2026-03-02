# watsonplots

Easy, high-quality interactive plots powered by Plotly.

## Install

```bash
pip install watsonplots
```

## Chart types

| Function | Description |
|---|---|
| `wp.line()` | Line chart with optional multi-series and smooth interpolation |
| `wp.area()` | Filled area chart, optionally stacked |
| `wp.scatter()` | Scatter plot with optional color grouping, size encoding, and hover data |
| `wp.sync()` | Align two time-series DataFrames via cross-correlation on a shared column |

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
# Bubble chart (size encodes a third variable)
wp.scatter(df, x="age", y="salary", size="exp_years", color="dept").show()
```

## Chart object

Every chart function returns a `Chart` object:

```python
chart = wp.line(df, x="date", y="revenue")

chart.show()                           # display in browser or notebook
chart.save("chart.html")               # write self-contained HTML file
chart.to_html()                        # HTML string for embedding
chart.to_fig()                         # raw plotly.graph_objects.Figure
chart.update(title="New")              # update layout, returns self
chart.add_threshold(100, label="Cap")  # horizontal reference line, returns self
```

## Sync

Align two time-series DataFrames that share a common signal but have different clock offsets.

```python
df1_synced, df2_synced = wp.sync(
    df1, df2,
    common_columns=("battery_v", "bus_voltage_v"),
    time1="timestamp",
    time2="device_timestamp",
)
```

Both DataFrames are returned with normalised timestamps. `df2`'s timestamps are shifted
by the discovered lag; all other columns are untouched.

## PDF export

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

## Requirements

- Python ≥ 3.12
- `plotly ≥ 5.0`, `pandas ≥ 2.0`, `kaleido ≥ 0.2`, `pypdf ≥ 4.0`, `scipy ≥ 1.0`
