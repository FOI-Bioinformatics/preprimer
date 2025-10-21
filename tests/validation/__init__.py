"""
Validation framework for PrePrimer real data testing.

Provides comprehensive validation of:
- Format conversions
- Alignment outputs
- Data integrity
- Performance metrics
"""

from .validator import (
    OutputValidator,
    ValidationResult,
    validate_artic_output,
    validate_conversion,
    validate_fasta_output,
    validate_olivar_output,
    validate_sts_output,
    validate_varvamp_output,
)

__all__ = [
    "OutputValidator",
    "ValidationResult",
    "validate_conversion",
    "validate_artic_output",
    "validate_varvamp_output",
    "validate_olivar_output",
    "validate_fasta_output",
    "validate_sts_output",
]
