import plotly.graph_objects as go

import watsonplots as wp
from watsonplots.chart import Chart


# --- histogram ---

def test_histogram_returns_chart(dist_df):
    assert isinstance(wp.histogram(dist_df, x="value"), Chart)


def test_histogram_trace_type(dist_df):
    fig = wp.histogram(dist_df, x="value").to_fig()
    assert isinstance(fig.data[0], go.Histogram)


def test_histogram_color_col(dist_df):
    fig = wp.histogram(dist_df, x="value", color="group").to_fig()
    assert len(fig.data) == 2


def test_histogram_barmode_overlay(dist_df):
    fig = wp.histogram(dist_df, x="value", color="group", barmode="overlay").to_fig()
    assert fig.layout.barmode == "overlay"


def test_histogram_bins(dist_df):
    fig = wp.histogram(dist_df, x="value", bins=20).to_fig()
    assert fig.data[0].nbinsx == 20


def test_histogram_no_legend_single(dist_df):
    fig = wp.histogram(dist_df, x="value").to_fig()
    assert fig.layout.showlegend is False


def test_histogram_legend_multi(dist_df):
    fig = wp.histogram(dist_df, x="value", color="group").to_fig()
    assert fig.layout.showlegend is True


def test_histogram_df_list(dist_df):
    import pandas as pd
    df2 = dist_df.copy()
    fig = wp.histogram([dist_df, df2], x="value",
                       color=["Flight 1", "Flight 2"]).to_fig()
    assert len(fig.data) == 2
    assert fig.data[1].name == "Flight 2"

