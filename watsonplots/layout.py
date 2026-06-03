import plotly.graph_objects as go

from watsonplots.themes import Theme


def apply_theme(fig: go.Figure, theme: Theme, title: str = "") -> go.Figure:
    axis = {
        "gridcolor": theme.gridcolor,
        "gridwidth": theme.gridwidth,
        "showgrid": theme.show_grid,
        "zerolinecolor": theme.zerolinecolor,
        "linecolor": theme.linecolor,
    }
    fig.update_layout(
        title=title,
        paper_bgcolor=theme.paper_bgcolor,
        plot_bgcolor=theme.plot_bgcolor,
        font=dict(color=theme.font_color, family=theme.font_family, size=theme.font_size),
        colorway=theme.colorway,
        margin=theme.margin,
        legend=dict(
            bgcolor=theme.legend_bgcolor,
            bordercolor=theme.legend_bordercolor,
            borderwidth=theme.legend_borderwidth,
            font=dict(color=theme.font_color),
        ),
        xaxis=axis,
        yaxis=axis,
    )
    return fig
