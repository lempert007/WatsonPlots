"""
watsonplots demo — run with:  uv run examples/demo.py
"""

import pandas as pd

import watsonplots as wp

binlog = pd.read_csv("examples/data/binlog.csv")
jetson = pd.read_csv("examples/data/jetson.csv")

# Align both logs to a common UTC time reference via cross-correlation on voltage
binlog, jetson = wp.sync(
    binlog,
    jetson,
    common_columns=("BAT_Volt", "bus_voltage_v"),
    time1="timestamp_local",
    time2="jetson_timestamp_local",
)

# 1. Altitude — background bands show each flight phase, threshold marks cruise floor
altitude_chart = wp.line(
    binlog,
    x="timestamp_local",
    y="BARO_Alt",
    segment_color="flight_mode",
    title="Drone Altitude — Flight Phases",
    xlabel="Time (s)",
    ylabel="Altitude (m)",
    theme="watson",
).add_threshold(60, label="Cruise floor")

# 2. Battery voltage from both sources (post-sync, multi-DataFrame)
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
    labels=["Binlog", "Jetson"],
    title="Battery Voltage — Binlog vs Jetson (post-sync)",
    xlabel="Time (s)",
    ylabel="Voltage (V)",
    theme="dark",
).add_threshold(11.1, label="Low battery")

# 3. Roll & Pitch — multiple y columns with spline smoothing
attitude_chart = wp.line(
    binlog,
    x="timestamp_local",
    y=["ATT_Roll", "ATT_Pitch"],
    title="Attitude — Roll & Pitch",
    xlabel="Time (s)",
    ylabel="Degrees",
    theme="dark",
    smooth=True,
)

# 4. CPU & GPU — stacked filled area
util_chart = wp.area(
    jetson,
    x="jetson_timestamp_local",
    y=["cpu_util_pct", "gpu_util_pct"],
    title="Jetson CPU & GPU Utilization (stacked)",
    xlabel="Time (s)",
    ylabel="Utilization (%)",
    theme="light",
    stacked=True,
)

# 5. Power draw — filled area coloured by flight phase
power_chart = wp.area(
    jetson,
    x="jetson_timestamp_local",
    y="power_w",
    segment_color="flight_mode",
    title="Jetson Power Draw by Flight Phase",
    xlabel="Time (s)",
    ylabel="Power (W)",
    theme="watson",
)

# 6. GPS flight path — colour gradient shows temporal progression (blue → red)
path_chart = wp.scatter(
    binlog,
    x="GPS_Lng",
    y="GPS_Lat",
    gradient_colors=("#58a6ff", "#f78166"),
    title="GPS Flight Path (blue → red = time)",
    xlabel="Longitude",
    ylabel="Latitude",
    theme="minimal",
)

# 7. Speed vs altitude bubble — marker size encodes battery power draw
bubble_chart = wp.scatter(
    binlog.iloc[::20],  # downsample for readability
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
    path_chart,
    bubble_chart,
]

wp.save_pdf(all_charts, "examples/output/report.pdf", per_page=2, theme="light")
print("Saved report.pdf  (4 pages, 2 charts each)")

wp.save_html(all_charts, "examples/output/report.html", title="Drone Flight Report", theme="watson")
print("Saved report.html")

print("\nAll done. Open examples/output/ to explore.")
