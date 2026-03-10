import base64
import math
import ssl
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import NamedTuple

import pandas as pd
import plotly.graph_objects as go

from ..chart import Chart
from ..consts import DEFAULT_THEME, DataFormats
from ..themes import Theme, get_theme
from ..utils import assign_colors, consecutive_runs, finalize_axes

# OSM tiles are public images; skip cert verification to avoid macOS Python.org SSL issues
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

_TILE_SIZE = 256
_SATELLITE_TILE_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
_USER_AGENT = "watsonplots/0.1.0 (github.com/watsonplots)"
_MERC_MAX = 20037508.342789244  # Web Mercator half-circumference in metres


class TileExtent(NamedTuple):
    """Bounding box of the fetched tile grid in UTM coordinates."""

    west: float
    east: float
    south: float
    north: float


def route(
    data: DataFormats,
    *,
    x: str,
    y: str,
    color: str | None = None,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    theme: str | Theme = DEFAULT_THEME,
    map_background: bool = False,
    utm_zone: int | None = None,
    utm_hemisphere: str = "N",
    map_padding: float = 0.1,
    tiles_cache_dir: str | None = None,
) -> Chart:
    """
    Create a drone route chart from UTM coordinate data.

    Parameters
    ----------
    data:             DataFrame or coercible input with easting/northing columns.
    x:                Column name for easting (UTM x).
    y:                Column name for northing (UTM y).
    color:            Column to split into multiple route traces.
    map_background:   If True, fetch OSM tiles and embed as background.
                      Requires utm and Pillow: pip install watsonplots[map]
    utm_zone:         UTM zone number (e.g. 36). Required when map_background=True.
    utm_hemisphere:   "N" or "S". Default "N".
    map_padding:      Fractional padding around the route bounding box (default 0.1).
    tiles_cache_dir:  Directory to cache downloaded tiles for offline reuse.
    """
    resolved_theme = get_theme(theme)
    df = pd.DataFrame(data)

    runs = consecutive_runs(df, color)
    unique_vals = list(dict.fromkeys(r[0] for r in runs))
    color_map = assign_colors(unique_vals, resolved_theme.colorway)

    fig = go.Figure()

    if map_background:
        if utm_zone is None:
            raise ValueError("utm_zone is required when map_background=True")
        tile_extent = _add_map_background(
            fig, df, x, y, utm_zone, utm_hemisphere, map_padding, tiles_cache_dir
        )
    else:
        tile_extent = None

    seen: set[str] = set()
    for name, run_df in runs:
        _add_route_segment(fig, run_df, x, y, name, color, color_map, seen)

    if color is not None and len(runs) > 1:
        _add_transition_markers(fig, runs, x, y)

    label_color = "white" if tile_extent is not None else resolved_theme.font_color
    end_x, end_y = float(df[x].iloc[-1]), float(df[y].iloc[-1])
    _add_end_marker(fig, end_x, end_y, label_color)

    finalize_axes(
        fig,
        resolved_theme,
        ref_x=df[x],
        ref_y=df[y],
        x_col=x,
        y_col=y,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        is_time=False,
        show_legend=color is not None,
    )

    _apply_axis_ranges(fig, df, x, y, tile_extent)

    return Chart(fig, resolved_theme)


# --- Trace builders ---


def _add_route_segment(
    fig: go.Figure,
    run_df: pd.DataFrame,
    x: str,
    y: str,
    name: str,
    color_col: str | None,
    color_map: dict,
    seen: set[str],
) -> None:
    """Add a shadow trace (for contrast) and a colored route trace for one run segment."""
    fig.add_trace(
        go.Scatter(
            x=run_df[x],
            y=run_df[y],
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
            line={"color": "black", "width": 7},
        )
    )
    hovertemplate = _build_hovertemplate(x, y, color_col, name)
    fig.add_trace(
        go.Scatter(
            x=run_df[x],
            y=run_df[y],
            mode="lines",
            name=name,
            showlegend=name not in seen,
            hovertemplate=hovertemplate,
            line={"color": color_map[name], "width": 4},
        )
    )
    seen.add(name)


def _add_transition_markers(
    fig: go.Figure,
    runs: list[tuple[str, pd.DataFrame]],
    x: str,
    y: str,
) -> None:
    """Add white dot markers at points where the color value changes."""
    tx = [run_df[x].iloc[0] for _, run_df in runs[1:]]
    ty = [run_df[y].iloc[0] for _, run_df in runs[1:]]
    fig.add_trace(
        go.Scatter(
            x=tx,
            y=ty,
            mode="markers",
            showlegend=False,
            hoverinfo="skip",
            marker={"color": "white", "size": 8, "line": {"color": "black", "width": 1.5}},
        )
    )


def _add_end_marker(fig: go.Figure, x1: float, y1: float, label_color: str) -> None:
    """Add a labeled marker at the final point of the route."""
    fig.add_trace(
        go.Scatter(
            x=[x1],
            y=[y1],
            mode="markers+text",
            showlegend=False,
            hoverinfo="skip",
            marker={"color": label_color, "size": 10, "line": {"color": "black", "width": 2}},
            text=[f"End ({int(x1)}, {int(y1)})"],
            textposition="top right",
            textfont={"color": label_color, "size": 11},
        )
    )


def _build_hovertemplate(x: str, y: str, color_col: str | None, color_val: str) -> str:
    """Build the hover tooltip text for a route trace."""
    base = f"{x}: %{{x}}<br>{y}: %{{y}}"
    color_line = f"<br>{color_col}: {color_val}" if color_col else ""
    return base + color_line + "<extra></extra>"


def _apply_axis_ranges(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y: str,
    tile_extent: TileExtent | None,
) -> None:
    """Set axis ranges — locked to tile grid when a map is present, padded otherwise."""
    if tile_extent is not None:
        fig.update_xaxes(
            range=[tile_extent.west, tile_extent.east],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        )
        fig.update_yaxes(
            range=[tile_extent.south, tile_extent.north],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        )
    else:
        x_pad = (df[x].max() - df[x].min()) * 0.05
        y_pad = (df[y].max() - df[y].min()) * 0.05
        fig.update_xaxes(range=[df[x].min() - x_pad, df[x].max() + x_pad])
        fig.update_yaxes(range=[df[y].min() - y_pad, df[y].max() + y_pad])


# --- Map background ---


def _add_map_background(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y: str,
    utm_zone: int,
    utm_hemisphere: str,
    map_padding: float,
    tiles_cache_dir: str | None,
) -> TileExtent:
    try:
        import utm
        from PIL import Image  # noqa: F401 — validate installation early
    except ImportError as exc:
        raise ImportError(
            "Map background requires utm and Pillow. " "Install with: pip install watsonplots[map]"
        ) from exc

    northern = utm_hemisphere.upper() == "N"

    xmin, xmax, ymin, ymax = _pad_bbox(df, x, y, map_padding)
    south, west, north, east = _bbox_to_latlon(xmin, ymin, xmax, ymax, utm_zone, northern, utm)

    zoom = _choose_zoom(west, south, east, north)

    tx_min, ty_min = _latlon_to_tile(north, west, zoom)
    tx_max, ty_max = _latlon_to_tile(south, east, zoom)

    grid_img = _assemble_tile_grid(tx_min, ty_min, tx_max, ty_max, zoom, tiles_cache_dir)

    img_west_m, img_north_m = _tile_to_web_merc(tx_min, ty_min, zoom)
    img_east_m, img_south_m = _tile_to_web_merc(tx_max + 1, ty_max + 1, zoom)

    ext_west, ext_south = _web_merc_to_utm(img_west_m, img_south_m, utm_zone, utm)
    ext_east, ext_north = _web_merc_to_utm(img_east_m, img_north_m, utm_zone, utm)

    extent = TileExtent(west=ext_west, east=ext_east, south=ext_south, north=ext_north)
    _embed_map_image(fig, grid_img, extent)

    return extent


def _pad_bbox(
    df: pd.DataFrame, x: str, y: str, padding: float
) -> tuple[float, float, float, float]:
    """Return (xmin, xmax, ymin, ymax) with fractional padding applied."""
    xmin, xmax = float(df[x].min()), float(df[x].max())
    ymin, ymax = float(df[y].min()), float(df[y].max())
    x_pad = (xmax - xmin) * padding
    y_pad = (ymax - ymin) * padding
    return xmin - x_pad, xmax + x_pad, ymin - y_pad, ymax + y_pad


def _bbox_to_latlon(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    utm_zone: int,
    northern: bool,
    utm,
) -> tuple[float, float, float, float]:
    """Convert UTM bounding box corners to (south, west, north, east) in WGS84."""
    south, west = utm.to_latlon(xmin, ymin, utm_zone, northern=northern)
    north, east = utm.to_latlon(xmax, ymax, utm_zone, northern=northern)
    return south, west, north, east


def _assemble_tile_grid(
    tx_min: int,
    ty_min: int,
    tx_max: int,
    ty_max: int,
    zoom: int,
    cache_dir: str | None,
):
    """Download and stitch tiles into a single PIL Image covering the given tile range."""
    from PIL import Image

    cols = tx_max - tx_min + 1
    rows = ty_max - ty_min + 1
    grid = Image.new("RGB", (cols * _TILE_SIZE, rows * _TILE_SIZE))

    for row, ty in enumerate(range(ty_min, ty_max + 1)):
        for col, tx in enumerate(range(tx_min, tx_max + 1)):
            tile = _fetch_tile(zoom, tx, ty, cache_dir)
            grid.paste(tile, (col * _TILE_SIZE, row * _TILE_SIZE))

    return grid


def _embed_map_image(fig: go.Figure, grid_img, extent: TileExtent) -> None:
    """Encode the grid image as base64 and embed it as a Plotly layout image."""
    buf = BytesIO()
    grid_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    fig.update_layout(
        images=[
            dict(
                source=f"data:image/png;base64,{b64}",
                xref="x",
                yref="y",
                x=extent.west,
                y=extent.north,
                sizex=extent.east - extent.west,
                sizey=extent.north - extent.south,
                sizing="stretch",
                layer="below",
            )
        ]
    )


# --- Coordinate math helpers ---


def _web_merc_to_utm(mx: float, my: float, zone: int, utm) -> tuple[float, float]:
    """Web Mercator metres → UTM easting/northing."""
    lon = math.degrees(mx / _MERC_MAX * math.pi)
    lat = math.degrees(2 * math.atan(math.exp(my / _MERC_MAX * math.pi)) - math.pi / 2)
    easting, northing, _, _ = utm.from_latlon(lat, lon, force_zone_number=zone)
    return easting, northing


def _latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """WGS84 lat/lon → XYZ slippy tile index."""
    n = 2**zoom
    tx = int((lon + 180) / 360 * n)
    lat_r = math.radians(lat)
    ty = int((1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n)
    return tx, ty


def _tile_to_web_merc(tx: int, ty: int, zoom: int) -> tuple[float, float]:
    """Tile corner (tx, ty) → Web Mercator metres."""
    n = 2**zoom
    return tx / n * 2 * _MERC_MAX - _MERC_MAX, _MERC_MAX - ty / n * 2 * _MERC_MAX


def _choose_zoom(west: float, south: float, east: float, north: float) -> int:
    span = max(north - south, east - west)
    if span > 1.0:
        return 12
    if span > 0.1:
        return 14
    if span > 0.01:
        return 16
    return 17


def _fetch_tile(z: int, x: int, y: int, cache_dir: str | None):
    """Return a PIL Image for the given tile, using cache if available."""
    from PIL import Image

    if cache_dir is not None:
        cache_path = Path(cache_dir) / str(z) / str(y) / f"{x}.png"
        if cache_path.exists():
            return Image.open(cache_path).convert("RGB")

    req = urllib.request.Request(
        _SATELLITE_TILE_URL.format(z=z, x=x, y=y),
        headers={"User-Agent": _USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            data = resp.read()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch map tile {z}/{x}/{y}. "
            "Are you offline? Set tiles_cache_dir= and run once while online to pre-cache."
        ) from exc

    img = Image.open(BytesIO(data)).convert("RGB")

    if cache_dir is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(cache_path)

    return img
