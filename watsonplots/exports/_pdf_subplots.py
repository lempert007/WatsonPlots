import plotly.graph_objects as go
from plotly.subplots import make_subplots

from watsonplots.themes import DARK

_SKIP_AXIS_KEYS = frozenset({"domain", "anchor", "matches", "scaleanchor", "scaleratio"})
_3D_TRACE_TYPES = {"scatter3d", "surface", "mesh3d", "cone", "streamtube", "isosurface", "volume"}


def is_3d_fig(fig: go.Figure) -> bool:
    return any(type(t).__name__.lower() in _3D_TRACE_TYPES for t in fig.data)


def is_mapbox_fig(fig: go.Figure) -> bool:
    return any(isinstance(t, go.Scattermapbox) for t in fig.data)


def mapbox_fig_to_scatter_fig(fig: go.Figure) -> go.Figure:
    """Convert a Scattermapbox figure to plain Scatter for PDF rendering (kaleido has no WebGL)."""
    new_fig = go.Figure()
    for trace in fig.data:
        if isinstance(trace, go.Scattermapbox):
            new_fig.add_trace(
                go.Scatter(
                    x=list(trace.lon) if trace.lon is not None else [],
                    y=list(trace.lat) if trace.lat is not None else [],
                    mode=trace.mode,
                    name=trace.name,
                    showlegend=trace.showlegend,
                    line={"color": trace.line.color, "width": trace.line.width},
                    marker={"color": trace.marker.color, "size": trace.marker.size},
                    text=trace.text,
                    textposition=trace.textposition,
                )
            )
        else:
            new_fig.add_trace(trace)
    new_fig.update_layout(
        title=fig.layout.title,
        paper_bgcolor=fig.layout.paper_bgcolor,
        plot_bgcolor=fig.layout.plot_bgcolor,
        font=fig.layout.font.to_plotly_json(),
        colorway=list(fig.layout.colorway) if fig.layout.colorway else None,
        margin=fig.layout.margin.to_plotly_json(),
        legend=fig.layout.legend.to_plotly_json(),
    )
    new_fig.update_xaxes(title_text="Longitude")
    new_fig.update_yaxes(title_text="Latitude")
    return new_fig


def axis_props(axis) -> dict:
    return {
        key: value
        for key, value in axis.to_plotly_json().items()
        if key not in _SKIP_AXIS_KEYS and value is not None
    }


def remap_axis_refs(plotly_obj, subplot_row: int) -> dict:
    props = {key: value for key, value in plotly_obj.to_plotly_json().items() if value is not None}
    suffix = "" if subplot_row == 1 else str(subplot_row)

    xref = props.get("xref", "")
    if xref == "x":
        props["xref"] = f"x{suffix}"
    elif xref == "x domain":
        props["xref"] = f"x{suffix} domain"

    yref = props.get("yref", "")
    if yref == "y":
        props["yref"] = f"y{suffix}"
    elif yref in ("y domain", "paper"):
        props["yref"] = f"y{suffix} domain"

    return props


def compose_subplots(figs: list[go.Figure], total_rows: int | None = None) -> go.Figure:
    rows = total_rows if total_rows is not None else len(figs)
    titles = [fig.layout.title.text or "" for fig in figs] + [""] * (rows - len(figs))

    fig_is_3d = [is_3d_fig(fig) for fig in figs]
    specs = [
        [{"type": "scene"}] if (i < len(fig_is_3d) and fig_is_3d[i]) else [{"type": "xy"}]
        for i in range(rows)
    ]

    subfig = make_subplots(
        rows=rows, cols=1, vertical_spacing=0.10, subplot_titles=titles, specs=specs
    )
    for subplot_row, fig in enumerate(figs, 1):
        for trace in fig.data:
            subfig.add_trace(trace, row=subplot_row, col=1)
        if not fig_is_3d[subplot_row - 1]:
            subfig.update_xaxes(row=subplot_row, col=1, **axis_props(fig.layout.xaxis))
            subfig.update_yaxes(row=subplot_row, col=1, **axis_props(fig.layout.yaxis))
            for shape in fig.layout.shapes:
                subfig.add_shape(**remap_axis_refs(shape, subplot_row))
            for annotation in fig.layout.annotations:
                subfig.add_annotation(**remap_axis_refs(annotation, subplot_row))
            for image in fig.layout.images:
                subfig.add_layout_image(**remap_axis_refs(image, subplot_row))
    return subfig


def apply_subplot_theme(subfig: go.Figure, source_layout, pdf_margin: dict) -> None:
    font_color = source_layout.font.color or DARK.font_color
    font_family = source_layout.font.family or DARK.font_family
    for annotation in subfig.layout.annotations:
        annotation.update(font=dict(color=font_color, family=font_family))
    subfig.update_layout(
        paper_bgcolor=source_layout.paper_bgcolor or DARK.paper_bgcolor,
        plot_bgcolor=source_layout.plot_bgcolor or DARK.plot_bgcolor,
        font=source_layout.font.to_plotly_json(),
        margin={"l": pdf_margin["l"], "r": pdf_margin["r"], "t": 30, "b": pdf_margin["b"]},
    )
    if source_layout.colorway:
        subfig.update_layout(colorway=list(source_layout.colorway))
