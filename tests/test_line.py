import plotly.graph_objects as go

import watsonplots as wp
from watsonplots.chart import Chart


def test_line_returns_chart(time_df):
    assert isinstance(wp.line(time_df, x="date", y="revenue"), Chart)


def test_line_single_trace(time_df):
    chart = wp.line(time_df, x="date", y="revenue")
    assert len(chart.to_fig().data) == 1


def test_line_multi_y(time_df):
    chart = wp.line(time_df, x="date", y=["revenue", "cost"])
    assert len(chart.to_fig().data) == 2


def test_line_color_col(time_df):
    chart = wp.line(time_df, x="date", y="revenue", color="region")
    assert len(chart.to_fig().data) == 2


def test_line_trace_type(time_df):
    fig = wp.line(time_df, x="date", y="revenue").to_fig()
    assert isinstance(fig.data[0], go.Scatter)


def test_line_smooth(time_df):
    fig = wp.line(time_df, x="date", y="revenue", smooth=True).to_fig()
    assert fig.data[0].line.shape == "spline"


def test_line_no_smooth(time_df):
    fig = wp.line(time_df, x="date", y="revenue", smooth=False).to_fig()
    assert fig.data[0].line.shape == "linear"


def test_line_no_legend_single(time_df):
    fig = wp.line(time_df, x="date", y="revenue").to_fig()
    assert fig.layout.showlegend is False


def test_line_legend_multi(time_df):
    fig = wp.line(time_df, x="date", y=["revenue", "cost"]).to_fig()
    assert fig.layout.showlegend is True


def test_line_title(time_df):
    fig = wp.line(time_df, x="date", y="revenue", title="Hello").to_fig()
    assert fig.layout.title.text == "Hello"


def test_line_auto_title(time_df):
    fig = wp.line(time_df, x="date", y="revenue").to_fig()
    assert "revenue" in fig.layout.title.text
    assert "date" in fig.layout.title.text


def test_line_xlabel(time_df):
    fig = wp.line(time_df, x="date", y="revenue", xlabel="Time").to_fig()
    assert fig.layout.xaxis.title.text == "Time"


def test_line_coercion_dict():
    import pandas as pd
    data = {"date": pd.date_range("2024-01-01", periods=5), "value": [1, 2, 3, 4, 5]}
    chart = wp.line(data, x="date", y="value")
    assert isinstance(chart, Chart)


def test_area_returns_chart(time_df):
    assert isinstance(wp.area(time_df, x="date", y="revenue"), Chart)


def test_area_fill(time_df):
    fig = wp.area(time_df, x="date", y="revenue").to_fig()
    assert fig.data[0].fill == "tozeroy"


def test_area_stacked(time_df):
    fig = wp.area(time_df, x="date", y=["revenue", "cost"], stacked=True).to_fig()
    assert fig.data[0].fill == "tozeroy"
    assert fig.data[1].fill == "tonexty"


# --- list-of-DataFrames ---

def test_line_df_list(time_df):
    fig = wp.line([time_df, time_df], x="date", y="revenue").to_fig()
    assert len(fig.data) == 2


def test_line_df_list_labels(time_df):
    fig = wp.line([time_df, time_df], x="date", y="revenue",
                  color=["Alpha", "Beta"]).to_fig()
    assert fig.data[0].name == "Alpha"
    assert fig.data[1].name == "Beta"


def test_line_df_list_label_mismatch_raises(time_df):
    import pytest
    with pytest.raises(ValueError, match="label"):
        wp.line([time_df, time_df], x="date", y="revenue", color=["Only One"])
