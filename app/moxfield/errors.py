"""Custom exceptions for the Moxfield client."""


class MoxfieldError(RuntimeError):
    """Base exception raised when a Moxfield request fails."""


class MoxfieldNotFoundError(MoxfieldError):
    """Raised when a requested entity cannot be found on Moxfield."""
