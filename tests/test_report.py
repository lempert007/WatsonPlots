import os
import tempfile

import watsonplots as wp


def test_save_html_creates_file(time_df, dist_df):
    charts = [
        wp.line(time_df, x="date", y="revenue", theme="watson"),
        wp.histogram(dist_df, x="value", color="group"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.html")
        wp.save_html(charts, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_save_html_adds_extension(time_df):
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report_no_ext")
        wp.save_html(charts, path)
        assert os.path.exists(path + ".html")


def test_save_html_contains_plotly(time_df):
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.html")
        wp.save_html(charts, path)
        content = open(path).read()
        assert "plotly" in content.lower()


def test_save_html_title(time_df):
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.html")
        wp.save_html(charts, path, title="My Dashboard")
        content = open(path).read()
        assert "My Dashboard" in content


def test_save_html_plotly_loaded_once(time_df, dist_df):
    charts = [
        wp.line(time_df, x="date", y="revenue"),
        wp.histogram(dist_df, x="value"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.html")
        wp.save_html(charts, path)
        content = open(path).read()
        # CDN script should appear exactly once
        assert content.count("cdn.plot.ly") == 1


def test_save_html_offline(time_df):
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "offline.html")
        wp.save_html(charts, path, offline=True)
        content = open(path).read()
        # No CDN <script> tag; bundled JS may internally reference cdn.plot.ly
        assert 'src="https://cdn.plot.ly' not in content
        assert "plotly" in content.lower()
