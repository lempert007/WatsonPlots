from datetime import date

import plotly.graph_objects as go

from watsonplots.text import Text
from watsonplots.themes import Theme

_A4_WIDTH = 595
_A4_HEIGHT = 842

_REPORT_TITLE = "Flight Report"
_COVER_TITLE_SIZE = 36
_COVER_DATE_SIZE = 14
_COVER_TOC_HDR_SIZE = 16
_COVER_TOC_ITEM_SIZE = 13
_COVER_TOC_LINE_GAP = 0.055  # paper-fraction spacing per TOC entry


def extract_toc_entries(items: list) -> list[str]:
    """Return heading-level Text items as TOC section names (body text excluded)."""
    return [item.text for item in items if isinstance(item, Text) and not item._is_body()]


def render_cover_page(toc_entries: list[str], theme: Theme) -> bytes:
    date_str = date.today().strftime("%B %d, %Y")
    font = dict(color=theme.font_color, family=theme.font_family)

    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=theme.paper_bgcolor,
        plot_bgcolor=theme.plot_bgcolor,
        font=font,
        margin={"l": 80, "r": 80, "t": 80, "b": 80},
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    fig.add_annotation(
        text=_REPORT_TITLE,
        x=0.5,
        y=0.85,
        xref="paper",
        yref="paper",
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_TITLE_SIZE},
    )
    fig.add_annotation(
        text=date_str,
        x=0.5,
        y=0.77,
        xref="paper",
        yref="paper",
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_DATE_SIZE},
    )
    fig.add_shape(
        type="line",
        x0=0.05,
        x1=0.95,
        y0=0.71,
        y1=0.71,
        xref="paper",
        yref="paper",
        line=dict(color=theme.gridcolor, width=1),
    )
    fig.add_annotation(
        text="Table of Contents",
        x=0.1,
        y=0.66,
        xref="paper",
        yref="paper",
        xanchor="left",
        yanchor="middle",
        showarrow=False,
        font={**font, "size": _COVER_TOC_HDR_SIZE},
    )

    y_pos = 0.59
    for index, entry in enumerate(toc_entries, 1):
        fig.add_annotation(
            text=f"{index}.  {entry}",
            x=0.12,
            y=y_pos,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="middle",
            showarrow=False,
            font={**font, "size": _COVER_TOC_ITEM_SIZE},
        )
        underline_y = y_pos - (_COVER_TOC_ITEM_SIZE * 0.5 / (_A4_HEIGHT - 160))
        fig.add_shape(
            type="line",
            x0=0.12,
            x1=0.88,
            y0=underline_y,
            y1=underline_y,
            xref="paper",
            yref="paper",
            line=dict(color=theme.gridcolor, width=0.5),
        )
        y_pos -= _COVER_TOC_LINE_GAP

    return fig.to_image(format="pdf", width=_A4_WIDTH, height=_A4_HEIGHT)
