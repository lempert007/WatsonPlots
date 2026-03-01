import os
import tempfile

import pytest

import watsonplots as wp

kaleido = pytest.importorskip("kaleido", reason="kaleido not installed")
pypdf = pytest.importorskip("pypdf", reason="pypdf not installed")


def test_save_pdf_creates_file(time_df, dist_df, numeric_df):
    charts = [
        wp.line(time_df, x="date", y="revenue", theme="dark"),
        wp.histogram(dist_df, x="value", color="group"),
        wp.scatter(numeric_df, x="x", y="y", color="category"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report.pdf")
        wp.save_pdf(charts, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


def test_save_pdf_adds_extension(time_df):
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "report_no_ext")
        wp.save_pdf(charts, path)
        assert os.path.exists(path + ".pdf")


def test_save_pdf_page_count_one_per_page(time_df, dist_df):
    charts = [
        wp.line(time_df, x="date", y="revenue"),
        wp.histogram(dist_df, x="value"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "two_pages.pdf")
        wp.save_pdf(charts, path, per_page=1)
        assert len(pypdf.PdfReader(path).pages) == 2


def test_save_pdf_per_page_2(time_df, dist_df):
    charts = [
        wp.line(time_df, x="date", y="revenue"),
        wp.histogram(dist_df, x="value"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "one_page.pdf")
        wp.save_pdf(charts, path, per_page=2)
        assert len(pypdf.PdfReader(path).pages) == 1


def test_save_pdf_per_page_4_two_pages(time_df, dist_df, numeric_df):
    # 5 charts with per_page=4 → 2 pages (4 on first, 1 on second)
    charts = [wp.line(time_df, x="date", y="revenue")] * 5
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "two_pages.pdf")
        wp.save_pdf(charts, path, per_page=4)
        assert len(pypdf.PdfReader(path).pages) == 2


def test_save_pdf_missing_pypdf_raises(monkeypatch, time_df):
    import sys
    monkeypatch.setitem(sys.modules, "pypdf", None)
    charts = [wp.line(time_df, x="date", y="revenue")]
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ImportError, match="pypdf"):
            wp.save_pdf(charts, os.path.join(tmpdir, "out.pdf"))
