import pandas as pd

DataFormats = pd.DataFrame | dict | list

DEFAULT_THEME = "dark"
TIME_LABEL = "Time (s)"

A4_WIDTH = 595
A4_HEIGHT = 842

SKIP_AXIS_KEYS = frozenset({"domain", "anchor", "matches", "scaleanchor", "scaleratio"})
