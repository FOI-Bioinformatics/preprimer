"""
Exception classes for preprimer.
"""


class PrePrimerError(Exception):
    """Base exception for all preprimer errors."""

    pass


class ParserError(PrePrimerError):
    """Raised when parsing fails."""

    pass


class ValidationError(PrePrimerError):
    """Raised when validation fails."""

    pass


class AlignmentError(PrePrimerError):
    """Raised when alignment operations fail."""

    pass


class OutputError(PrePrimerError):
    """Raised when output writing fails."""

    pass


class ConfigError(PrePrimerError):
    """Raised when configuration is invalid."""

    pass
