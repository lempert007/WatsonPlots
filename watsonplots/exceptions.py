class SyncError(ValueError):
    """Base class for all sync-related errors."""


class ColumnNotFoundError(SyncError):
    """A required column is missing from the DataFrame."""


class ConstantColumnError(SyncError):
    """A sync column has zero variance and cannot be used for correlation."""


class TimeParseError(SyncError):
    """A timestamp column could not be parsed."""


class NoTemporalOverlapError(SyncError):
    """The two log time ranges do not overlap."""
