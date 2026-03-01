from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    paper_bgcolor: str
    plot_bgcolor: str
    font_color: str
    font_family: str
    font_size: int
    gridcolor: str
    gridwidth: float
    zerolinecolor: str
    linecolor: str
    show_grid: bool
    colorway: list[str]
    margin: dict
    legend_bgcolor: str
    legend_bordercolor: str
    legend_borderwidth: int


DARK = Theme(
    name="dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font_color="#e6edf3",
    font_family="Inter, system-ui, sans-serif",
    font_size=13,
    gridcolor="#30363d",
    gridwidth=0.5,
    zerolinecolor="#484f58",
    linecolor="#30363d",
    show_grid=True,
    colorway=["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657", "#79c0ff", "#56d364"],
    margin={"l": 60, "r": 30, "t": 60, "b": 60},
    legend_bgcolor="#161b22",
    legend_bordercolor="#30363d",
    legend_borderwidth=1,
)

LIGHT = Theme(
    name="light",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8f9fa",
    font_color="#212529",
    font_family="Inter, system-ui, sans-serif",
    font_size=13,
    gridcolor="#dee2e6",
    gridwidth=0.5,
    zerolinecolor="#adb5bd",
    linecolor="#dee2e6",
    show_grid=True,
    colorway=["#0d6efd", "#198754", "#dc3545", "#6f42c1", "#fd7e14", "#0dcaf0", "#ffc107"],
    margin={"l": 60, "r": 30, "t": 60, "b": 60},
    legend_bgcolor="#ffffff",
    legend_bordercolor="#dee2e6",
    legend_borderwidth=1,
)

MINIMAL = Theme(
    name="minimal",
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    font_color="#333333",
    font_family="Georgia, serif",
    font_size=13,
    gridcolor="#eeeeee",
    gridwidth=0.5,
    zerolinecolor="#cccccc",
    linecolor="#ffffff",
    show_grid=True,
    colorway=["#2c3e50", "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"],
    margin={"l": 60, "r": 30, "t": 60, "b": 60},
    legend_bgcolor="#ffffff",
    legend_bordercolor="#eeeeee",
    legend_borderwidth=1,
)

WATSON = Theme(
    name="watson",
    paper_bgcolor="#1a1a2e",
    plot_bgcolor="#16213e",
    font_color="#e2e8f0",
    font_family="'JetBrains Mono', 'Fira Code', monospace",
    font_size=12,
    gridcolor="#2d3748",
    gridwidth=0.5,
    zerolinecolor="#4a5568",
    linecolor="#2d3748",
    show_grid=True,
    colorway=["#63b3ed", "#68d391", "#fc8181", "#b794f4", "#f6ad55", "#76e4f7", "#f687b3"],
    margin={"l": 60, "r": 30, "t": 60, "b": 60},
    legend_bgcolor="#16213e",
    legend_bordercolor="#2d3748",
    legend_borderwidth=1,
)

_THEMES: dict[str, Theme] = {
    "dark": DARK,
    "light": LIGHT,
    "minimal": MINIMAL,
    "watson": WATSON,
}


def get_theme(theme: str | Theme) -> Theme:
    if isinstance(theme, Theme):
        return theme
    key = theme.lower().strip()
    if key not in _THEMES:
        raise ValueError(f"Unknown theme '{theme}'. Available: {list(_THEMES.keys())}")
    return _THEMES[key]
