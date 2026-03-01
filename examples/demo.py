"""
watsonplots demo — run with:  uv run examples/demo.py
"""

import pandas as pd

import watsonplots as wp

f1 = pd.read_csv("examples/data/flight1.csv", parse_dates=["time"])
f2 = pd.read_csv("examples/data/flight2.csv", parse_dates=["time"])

height_chart = wp.line(
    [f1, f2],
    x="time",
    y="height",
    color=["Drone 1", "Drone 2"],
    title="Flight Height over Time",
    xlabel="Time (UTC)",
    ylabel="Height (m)",
    theme="watson",
)

voltage_chart = wp.line(
    [f1, f2],
    x="time",
    y="voltage",
    color=["Drone 1", "Drone 2"],
    title="Battery Voltage over Time",
    xlabel="Time (UTC)",
    ylabel="Voltage (V)",
    theme="dark",
)

current_chart = wp.area(
    f2,
    x="time",
    y="current",
    title="Drone 2 — Current Draw",
    xlabel="Time (UTC)",
    ylabel="Current (A)",
    theme="watson",
)

scatter_chart = wp.scatter(
    [f1, f2],
    x="voltage",
    y="height",
    color=["Drone 1", "Drone 2"],
    title="Height vs Battery Voltage",
    xlabel="Voltage (V)",
    ylabel="Height (m)",
    theme="minimal",
)

all_charts = [height_chart, voltage_chart, current_chart, scatter_chart]
wp.save_pdf(all_charts, "examples/output/report.pdf", per_page=2, theme="watson")
print("Saved report.pdf  (2 pages, 2 charts each, watson theme)")

wp.save_html(all_charts, "examples/output/report.html", title="Drone Flight Report")
print("Saved report.html")

fig = height_chart.to_fig()
peak_idx = f1["height"].idxmax()
peak_time = f1.loc[peak_idx, "time"]
peak_h = f1.loc[peak_idx, "height"]

fig.add_annotation(
    x=peak_time,
    y=peak_h,
    text=f"Peak {peak_h} m",
    showarrow=True,
    arrowhead=2,
    font={"color": "#f6ad55"},
    arrowcolor="#f6ad55",
)
fig.write_html("examples/output/05_annotated.html")
print("Saved 05_annotated.html")

print("\nAll done. Open examples/output/ to explore.")
