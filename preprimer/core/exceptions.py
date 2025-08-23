"""
Exception classes for preprimer.
"""


class PrePrimerError(Exception):
    """Base exception for all preprimer errors."""


class ParserError(PrePrimerError):
    """Raised when parsing fails."""


class ValidationError(PrePrimerError):
    """Raised when validation fails."""


class AlignmentError(PrePrimerError):
    """Raised when alignment operations fail."""


class OutputError(PrePrimerError):
    """Raised when output writing fails."""


class ConfigError(PrePrimerError):
    """Raised when configuration is invalid."""
