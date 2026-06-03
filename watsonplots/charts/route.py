import pandas as pd
import plotly.graph_objects as go

from watsonplots.chart import Chart
from watsonplots.consts import DEFAULT_THEME, DataFormats
from watsonplots.themes import Theme, get_theme
from watsonplots.utils import assign_colors, consecutive_runs


def route(
    data: DataFormats,
    *,
    lat: str,
    lon: str,
    color: str | None = None,
    title: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    tile_url: str = "http://localhost:8080/tiles/{z}/{x}/{y}.png",
    show_legend: bool = True,
) -> Chart:
    """
    Create a route chart overlaid on an interactive map.

    Parameters
    ----------
    data:       DataFrame or coercible input with latitude/longitude columns.
    lat:        Column name for latitude.
    lon:        Column name for longitude.
    color:      Column to split into multiple color-coded route segments.
    tile_url:   Local tile server URL, e.g.
                "http://localhost:8080/tiles/{z}/{x}/{y}.png".
    """
    resolved_theme = get_theme(theme)
    df = pd.DataFrame(data)

    color_runs = consecutive_runs(df, color)
    unique_color_values = list(dict.fromkeys(run_name for run_name, _ in color_runs))
    color_map = assign_colors(unique_color_values, resolved_theme.colorway)

    fig = go.Figure()

    rendered: set[str] = set()
    for segment_name, segment_df in color_runs:
        fig.add_trace(
            go.Scattermapbox(
                lat=segment_df[lat],
                lon=segment_df[lon],
                mode="lines",
                name=segment_name,
                showlegend=bool(color) and segment_name not in rendered,
                line={"color": color_map[segment_name], "width": 3},
            )
        )
        rendered.add(segment_name)

    fig.add_trace(
        go.Scattermapbox(
            lat=[float(df[lat].iloc[-1])],
            lon=[float(df[lon].iloc[-1])],
            mode="markers+text",
            showlegend=False,
            marker={"size": 10, "color": resolved_theme.font_color},
            text=["End"],
            textposition="top right",
        )
    )

    fig.update_layout(
        title=title,
        mapbox=dict(
            style="white-bg",
            center=dict(lat=float(df[lat].mean()), lon=float(df[lon].mean())),
            zoom=12,
            layers=[dict(sourcetype="raster", source=[tile_url], below="traces")],
        ),
        showlegend=show_legend,
        margin=resolved_theme.margin,
        paper_bgcolor=resolved_theme.paper_bgcolor,
        font=dict(
            color=resolved_theme.font_color,
            family=resolved_theme.font_family,
            size=resolved_theme.font_size,
        ),
    )

    return Chart(fig, resolved_theme)
