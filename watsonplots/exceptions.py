class WatsonPlotsError(Exception):
    """Base class for all watsonplots errors."""


class UnknownThemeError(WatsonPlotsError):
    """Raised when an unknown theme name is requested."""


class DataError(WatsonPlotsError):
    """Raised for invalid or inconsistent input data."""


class InvalidSliceRangeError(DataError):
    """start/end fractions are out of [0, 1] or start > end."""


class YColumnMismatchError(DataError):
    """Number of y columns does not match number of DataFrames."""


class MissingSeriesError(DataError):
    """A datetime x-axis requires at least one parsed series."""


class MissingDependencyError(WatsonPlotsError):
    """An optional dependency required for this feature is not installed."""


class SyncError(DataError):
    """Base class for sync-related errors."""


class ColumnNotFoundError(SyncError):
    """A required column is missing from the DataFrame."""


class ConstantColumnError(SyncError):
    """A sync column has zero variance and cannot be used for correlation."""


class TimeParseError(SyncError):
    """A timestamp column could not be parsed."""
