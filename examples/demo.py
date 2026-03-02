"""
watsonplots demo — run with:  uv run examples/demo.py
"""

import pandas as pd

import watsonplots as wp

binlog = pd.read_csv("examples/data/binlog.csv")
jetson = pd.read_csv("examples/data/jetson.csv")

# Align both logs to a common UTC time reference using cross-correlation on voltage
binlog, jetson = wp.sync(
    binlog,
    jetson,
    common_column=("BAT_Volt", "bus_voltage_v"),
    time1="timestamp_local",
    time2="jetson_timestamp_local",
)

height_chart = wp.line(
    binlog,
    x="timestamp_local",
    y="BARO_Alt",
    title="Drone Altitude over Time",
    xlabel="Time (UTC)",
    ylabel="Altitude (m)",
    theme="watson",
).add_threshold(50, label="Min cruise altitude")

# Align column names so both DataFrames can share x= and y=
b = binlog[["timestamp_local", "BAT_Volt"]].rename(
    columns={"timestamp_local": "time", "BAT_Volt": "voltage"}
)
j = jetson[["jetson_timestamp_local", "bus_voltage_v"]].rename(
    columns={"jetson_timestamp_local": "time", "bus_voltage_v": "voltage"}
)
voltage_chart = wp.line(
    [b, j],
    x="time",
    y="voltage",
    title="Voltage Comparison",
    xlabel="Time (UTC)",
    ylabel="Voltage (V)",
    theme="dark",
).add_threshold(11.1, label="Low battery")

util_chart = wp.area(
    jetson,
    x="jetson_timestamp_local",
    y=["cpu_util_pct", "gpu_util_pct"],
    title="Jetson CPU & GPU Utilization",
    xlabel="Time (UTC)",
    ylabel="Utilization (%)",
    theme="light",
)

# Gradient from blue → red shows the flight path progression over time
scatter_chart = wp.scatter(
    binlog,
    x="GPS_Lng",
    y="GPS_Lat",
    gradient_colors=("#58a6ff", "#f78166"),
    title="GPS Flight Path",
    xlabel="Longitude",
    ylabel="Latitude",
    theme="minimal",
)

all_charts = [height_chart, voltage_chart, util_chart, scatter_chart]
wp.save_pdf(all_charts, "examples/output/report.pdf", per_page=2, theme="light")
print("Saved report.pdf  (2 pages, 2 charts each, watson theme)")

wp.save_html(all_charts, "examples/output/report.html", title="Drone Flight Report", theme="watson")

print("\nAll done. Open examples/output/ to explore.")
