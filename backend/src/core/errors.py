class ApplicationError(Exception):
    """Base class for application-level errors."""

    def __init__(self, message: str) -> None:
        """Store a user-facing error message."""
        super().__init__(message)
        self.message = message


class NotFoundError(ApplicationError):
    """Raised when an application resource is missing."""

    pass


class ValidationError(ApplicationError):
    """Raised when input validation fails."""

    pass


class StorageError(ApplicationError):
    """Raised when file storage operations fail."""

    pass
