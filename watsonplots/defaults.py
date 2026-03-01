from collections.abc import Callable
from enum import Enum

import pandas as pd

from .consts import DataFormats


class AxisType(str, Enum):
    DATE = "date"
    NUMERIC = "-"
    CATEGORY = "category"


class TickFormat(str, Enum):
    LARGE_NUMBER = ",.0f"


AXIS_TYPE_CHECKS: list[tuple[Callable, AxisType]] = [
    (pd.api.types.is_datetime64_any_dtype, AxisType.DATE),
    (pd.api.types.is_numeric_dtype, AxisType.NUMERIC),
]

TICK_FORMAT_CHECKS: list[tuple[Callable, TickFormat]] = [
    (
        lambda s: pd.api.types.is_numeric_dtype(s) and s.abs().max() >= 10_000,
        TickFormat.LARGE_NUMBER,
    ),
]


def infer_axis_type(series: pd.Series) -> AxisType:
    """Return the Plotly axis type for a series based on its dtype."""
    for check, axis_type in AXIS_TYPE_CHECKS:
        if check(series):
            return axis_type
    return AxisType.CATEGORY


def smart_title(x: str | None, y: str | None) -> str:
    """Generate a default chart title from column names."""
    if x and y:
        return f"{y} vs {x}"
    return ""


def tick_format_for(series: pd.Series) -> TickFormat | None:
    """Return a Plotly tickformat for the series, or None."""
    for check, fmt in TICK_FORMAT_CHECKS:
        if check(series):
            return fmt
    return None


def resolve_groups(
    data: DataFormats,
    color: str | list[str] | None,
) -> tuple[list[tuple[pd.DataFrame, str | None]], pd.DataFrame]:
    """
    Resolve any supported data input into ([(sub_df, label), ...], ref_df).

    label is None when there is no split — callers fall back to the column name.
    Works for: list of DataFrames, single DataFrame with color column, plain DataFrame.
    """
    if isinstance(data, list) and data and isinstance(data[0], pd.DataFrame):
        if isinstance(color, str):
            raise ValueError(
                "color must be a list of labels (not a column name) when data is a list of DataFrames"
            )
        labels = color if isinstance(color, list) else [str(i) for i in range(len(data))]
        if len(labels) != len(data):
            raise ValueError(
                f"color has {len(labels)} label(s) but data has {len(data)} DataFrames"
            )
        return list(zip(data, labels)), data[0]
    df = pd.DataFrame(data)
    if color is not None:
        return [(g, str(v)) for v, g in df.groupby(color, sort=False)], df
    return [(df, None)], df
