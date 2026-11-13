"""Domain errors for Space Motion Studio.

Following Clean Architecture, domain errors belong to the innermost core
and have no dependencies on frameworks or outer circles.
"""


class DomainError(Exception):
    """Base class for all domain errors."""
    pass


class ValidationError(DomainError):
    """Raised when data contracts or domain invariants are violated."""

    def __init__(self, message: str, field_location: str | None = None) -> None:
        super().__init__(message)
        self.field_location = field_location


class RunConflictError(DomainError):
    """Raised when concurrent operations attempt to access a locked run."""
    pass


class ResourceNotFoundError(DomainError):
    """Raised when an asset or required resource is missing."""
    pass


class RenderError(DomainError):
    """Raised when video rendering fails."""
    pass


class PreflightError(DomainError):
    """Raised when preflight system dependency diagnostics fail."""
    pass
