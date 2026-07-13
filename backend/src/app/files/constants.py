from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Allowed file processing states."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ScanStatus(StrEnum):
    """Allowed file scan states."""

    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    FAILED = "failed"


class AlertLevel(StrEnum):
    """Allowed alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
