"""
Core preprimer modules with abstract base classes and interfaces.
"""

from .config import DefaultConfig, PrePrimerConfig
from .exceptions import (
    AlignmentError,
    OutputError,
    ParserError,
    PrePrimerError,
    ValidationError,
)
from .interfaces import (
    AlignmentProvider,
    AmpliconData,
    OutputWriter,
    PrimerData,
    PrimerParser,
)

__all__ = [
    "PrimerParser",
    "PrimerData",
    "AmpliconData",
    "OutputWriter",
    "AlignmentProvider",
    "PrePrimerError",
    "ParserError",
    "ValidationError",
    "AlignmentError",
    "OutputError",
    "PrePrimerConfig",
    "DefaultConfig",
]
