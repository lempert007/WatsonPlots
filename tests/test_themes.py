import pytest

import watsonplots as wp
from watsonplots.themes import DARK, Theme, get_theme


def test_get_theme_by_string():
    assert get_theme("dark") is DARK


def test_get_theme_unknown_raises():
    with pytest.raises(ValueError, match="Unknown theme"):
        get_theme("neon")


def test_custom_theme_usable(time_df):
    custom = Theme(
        name="custom",
        paper_bgcolor="#000000",
        plot_bgcolor="#111111",
        font_color="#ffffff",
        font_family="Arial, sans-serif",
        font_size=12,
        gridcolor="#222222",
        gridwidth=1.0,
        zerolinecolor="#333333",
        linecolor="#222222",
        show_grid=True,
        colorway=["#ff0000", "#00ff00"],
        margin={"l": 60, "r": 30, "t": 60, "b": 60},
        legend_bgcolor="#111111",
        legend_bordercolor="#222222",
        legend_borderwidth=1,
    )
    chart = wp.line(time_df, x="date", y="revenue", theme=custom)
    assert chart.to_fig().layout.paper_bgcolor == "#000000"
