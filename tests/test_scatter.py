import plotly.graph_objects as go

import watsonplots as wp
from watsonplots.chart import Chart


def test_scatter_returns_chart(numeric_df):
    assert isinstance(wp.scatter(numeric_df, x="x", y="y"), Chart)


def test_scatter_mode_markers(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y").to_fig()
    assert fig.data[0].mode == "markers"


def test_scatter_single_trace(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y").to_fig()
    assert len(fig.data) == 1


def test_scatter_color_col(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y", color="category").to_fig()
    assert len(fig.data) == 4  # A, B, C, D


def test_scatter_size_col(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y", size="size_col").to_fig()
    assert fig.data[0].marker.size is not None


def test_scatter_hover_data(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y", hover_data=["category"]).to_fig()
    assert fig.data[0].customdata is not None


def test_scatter_opacity(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y", opacity=0.5).to_fig()
    assert fig.data[0].marker.opacity == 0.5


def test_scatter_trace_type(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y").to_fig()
    assert isinstance(fig.data[0], go.Scatter)


def test_scatter_no_legend_single(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y").to_fig()
    assert fig.layout.showlegend is False


def test_scatter_legend_multi(numeric_df):
    fig = wp.scatter(numeric_df, x="x", y="y", color="category").to_fig()
    assert fig.layout.showlegend is True


def test_scatter_df_list(numeric_df):
    fig = wp.scatter([numeric_df, numeric_df], x="x", y="y",
                     color=["Set A", "Set B"]).to_fig()
    assert len(fig.data) == 2
    assert fig.data[0].name == "Set A"
