"""
Core preprimer modules with abstract base classes and interfaces.
"""

from .interfaces import (
    PrimerParser,
    PrimerData,
    AmpliconData, 
    OutputWriter,
    AlignmentProvider
)
from .exceptions import (
    PrePrimerError,
    ParserError,
    ValidationError,
    AlignmentError,
    OutputError
)
from .config import PrePrimerConfig, DefaultConfig

__all__ = [
    'PrimerParser',
    'PrimerData', 
    'AmpliconData',
    'OutputWriter',
    'AlignmentProvider',
    'PrePrimerError',
    'ParserError',
    'ValidationError',
    'AlignmentError', 
    'OutputError',
    'PrePrimerConfig',
    'DefaultConfig'
]