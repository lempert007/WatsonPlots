"""
watsonplots demo — run with:  uv run examples/demo.py
"""

import pandas as pd

import watsonplots as wp

binlog = pd.read_csv("examples/data/binlog.csv")
jetson = pd.read_csv("examples/data/jetson.csv")

synced_binlog, synced_jetson = wp.sync(
    binlog,
    jetson,
    common_columns=("BAT_Volt", "bus_voltage_v"),
    time1="timestamp_local",
    time2="jetson_timestamp_local",
    new_column_name="voltage",
    new_time_name="time",
)

altitude_chart = (
    wp.line(
        synced_binlog,
        x="time",
        y="BARO_Alt",
        segment_color="flight_mode",
        title="Drone Altitude — Flight Phases",
        xlabel="Time (s)",
        ylabel="Altitude (m)",
        theme="watson",
    )
    .add_threshold(60, label="above")
    .add_threshold(20, label="below")
)


voltage_chart = wp.line(
    [synced_binlog, synced_jetson],
    x="time",
    y="voltage",
    labels=["Binlog", "Jetson"],
    title="Battery Voltage — Binlog vs Jetson (post-sync)",
    xlabel="Time (s)",
    ylabel="Voltage (V)",
    theme="dark",
).add_threshold(11.1, label="Low battery")

attitude_chart = wp.line(
    synced_binlog,
    x="time",
    y=["ATT_Roll", "ATT_Pitch"],
    title="Attitude — Roll & Pitch",
    xlabel="Time (s)",
    ylabel="Degrees",
    theme="dark",
    smooth=True,
)

util_chart = wp.area(
    synced_jetson,
    x="time",
    y=["cpu_util_pct", "gpu_util_pct"],
    title="Jetson CPU & GPU Utilization (stacked)",
    xlabel="Time (s)",
    ylabel="Utilization (%)",
    theme="light",
    stacked=True,
)

power_chart = wp.area(
    synced_jetson,
    x="time",
    y="power_w",
    segment_color="flight_mode",
    title="Jetson Power Draw by Flight Phase",
    xlabel="Time (s)",
    ylabel="Power (W)",
    theme="watson",
)

bubble_chart = wp.scatter(
    binlog,
    data_start=0.3,
    data_end=0.4,
    x="GPS_Spd",
    y="BARO_Alt",
    size="BAT_Power",
    title="Speed vs Altitude (bubble size = power draw)",
    xlabel="GPS Speed (m/s)",
    ylabel="Altitude (m)",
    theme="light",
    opacity=0.6,
)


# ── Export ────────────────────────────────────────────────────────────────────
all_charts = [
    altitude_chart,
    voltage_chart,
    attitude_chart,
    util_chart,
    power_chart,
    bubble_chart,
]

wp.save_pdf(all_charts, "examples/output/report.pdf", per_page=2, theme="light")
print("Saved report.pdf  (4 pages, 2 charts each)")

wp.save_html(all_charts, "examples/output/report.html", title="Drone Flight Report", theme="watson")
print("Saved report.html")

print("\nAll done. Open examples/output/ to explore.")
