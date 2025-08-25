"""
PrePrimer - Convert and analyze tiled primer schemes.

A modern, extensible tool for converting between different primer scheme formats
used in tiled amplicon sequencing.
"""

__version__ = "0.2.0"

from .core.config import DefaultConfig, PrePrimerConfig
from .core.converter import PrimerConverter
from .core.exceptions import OutputError, ParserError, PrePrimerError, ValidationError

# Import core components
from .core.interfaces import AmpliconData, OutputWriter, PrimerData, PrimerParser

# Import registries for advanced users
from .core.registry import parser_registry, writer_registry

# Import parsers and writers to trigger auto-registration
import preprimer.parsers  # noqa: F401
import preprimer.writers  # noqa: F401


# Convenience function for simple usage
def convert_primers(
    input_file,
    output_dir,
    input_format=None,
    output_formats=None,
    prefix="primers",
    reference_file=None,
    **kwargs
):
    """
    Convenience function for primer conversion.

    Args:
        input_file: Path to input primer file
        output_dir: Directory for output files
        input_format: Input format (auto-detected if None)
        output_formats: List of output formats (default: ['artic'])
        prefix: Prefix for output files
        reference_file: Reference genome file
        **kwargs: Additional configuration options

    Returns:
        Dictionary mapping format names to output file paths
    """
    config = PrePrimerConfig()

    # Update config with kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    if output_formats is None:
        output_formats = ["artic"]

    converter = PrimerConverter(config)

    return converter.convert(
        input_file=input_file,
        output_dir=output_dir,
        input_format=input_format,
        output_formats=output_formats,
        prefix=prefix,
        reference_file=reference_file,
        **kwargs
    )


__all__ = [
    "__version__",
    "PrimerParser",
    "OutputWriter",
    "PrimerData",
    "AmpliconData",
    "PrePrimerConfig",
    "DefaultConfig",
    "PrimerConverter",
    "PrePrimerError",
    "ParserError",
    "ValidationError",
    "OutputError",
    "parser_registry",
    "writer_registry",
    "convert_primers",
]
