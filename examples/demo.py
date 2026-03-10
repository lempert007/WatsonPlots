"""
watsonplots demo — run with:  uv run examples/demo.py
"""

import pandas as pd

import watsonplots as wp

binlog = pd.read_csv("examples/data/binlog.csv")
jetson = pd.read_csv("examples/data/jetson.csv")
drone_route = pd.read_csv("examples/data/drone_route.csv")

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
        title="Drone Altitude — Flight Phases",
        xlabel="Time (s)",
        ylabel="Altitude (m)",
        theme="watson",
    )
    .add_y_threshold(60, label="above")
    .add_y_threshold(20, label="below")
)

voltage_chart = (
    wp.line(
        [synced_binlog, synced_jetson],
        x="time",
        y="voltage",
        labels=["Binlog", "Jetson"],
        title="Battery Voltage — Binlog vs Jetson (post-sync)",
        xlabel="Time (s)",
        ylabel="Voltage (V)",
        theme="dark",
    )
    .add_y_threshold(11.1, label="Low battery")
    .add_x_threshold(value=500, label="500s mark")
)

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
    title="Jetson CPU & GPU Utilization",
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

route_chart = wp.route(
    drone_route,
    x="easting",
    y="northing",
    title="Drone Route — No Map",
    xlabel="x (m)",
    ylabel="y (m)",
    utm_zone=36,
    utm_hemisphere="N",
    theme="dark",
)

route_map_chart = wp.route(
    drone_route,
    x="easting",
    y="northing",
    title="Drone Route — Satellite Map",
    xlabel="x (m)",
    ylabel="y (m)",
    map_background=True,
    utm_zone=36,
    utm_hemisphere="N",
    theme="dark",
    color="altitude_m",
)

scatter3d_chart = wp.scatter3d(
    drone_route,
    x="easting",
    y="northing",
    z="altitude_m",
    title="Drone Flight Path — 3D",
    xlabel="Easting (m)",
    ylabel="Northing (m)",
    zlabel="Altitude (m)",
    theme="watson",
)

line3d_chart = wp.line3d(
    drone_route,
    x="easting",
    y="northing",
    z="altitude_m",
    title="Drone Flight Path — 3D Line",
    xlabel="Easting (m)",
    ylabel="Northing (m)",
    zlabel="Altitude (m)",
    theme="dark",
)


# ── Export ────────────────────────────────────────────────────────────────────
all_charts: list[wp.Chart | wp.Text] = [
    wp.Text("Flight Telemetry"),
    wp.Text(
        "Altitude and voltage data captured during the test flight."
        " Thresholds mark safe operating limits.",
        variant="body",
    ),
    altitude_chart,
    voltage_chart,
    wp.Text("Attitude & Compute"),
    wp.Text(
        "Roll/pitch from the IMU alongside Jetson CPU/GPU utilization and power draw.",
        variant="body",
    ),
    attitude_chart,
    util_chart,
    power_chart,
    wp.Text("Route"),
    route_chart,
    route_map_chart,
    wp.Text("3D Flight Path"),
    wp.Text(
        "Full spatial trajectory of the drone plotted in three dimensions.",
        variant="body",
    ),
    scatter3d_chart,
    line3d_chart,
]

wp.save_pdf(all_charts, "examples/output/report.pdf", per_page=2, theme="light")
print("Saved report.pdf")

wp.save_html(all_charts, "examples/output/report.html", title="Drone Flight Report", theme="watson")
print("Saved report.html")

print("\nAll done. Open examples/output/ to explore.")
