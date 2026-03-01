import os
import tempfile

import plotly.graph_objects as go
import pytest

import watsonplots as wp


@pytest.fixture
def chart(time_df):
    return wp.line(time_df, x="date", y="revenue")


def test_show_returns_self(chart):
    result = chart.show()
    assert result is chart


def test_save_creates_html_file(chart):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.html")
        chart.save(path)
        assert os.path.exists(path)


def test_save_adds_html_extension(chart):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_no_ext")
        chart.save(path)
        assert os.path.exists(path + ".html")


def test_save_returns_self(chart):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = chart.save(os.path.join(tmpdir, "out.html"))
        assert result is chart


def test_to_html_returns_string(chart):
    html = chart.to_html()
    assert isinstance(html, str)
    assert "plotly" in html.lower()


def test_to_fig_returns_figure(chart):
    fig = chart.to_fig()
    assert isinstance(fig, go.Figure)


def test_update_returns_self(chart):
    result = chart.update(title="Updated")
    assert result is chart


def test_update_changes_layout(chart):
    chart.update(title="My Title")
    assert chart.to_fig().layout.title.text == "My Title"


def test_repr(chart):
    r = repr(chart)
    assert "Chart" in r
    assert "dark" in r
