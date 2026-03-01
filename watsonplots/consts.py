import pandas as pd

DataFormats = pd.DataFrame | dict | list

DEFAULT_THEME = "dark"

A4_W = 595
A4_H = 842

SKIP_AXIS_KEYS = frozenset({"domain", "anchor", "matches", "scaleanchor", "scaleratio"})
