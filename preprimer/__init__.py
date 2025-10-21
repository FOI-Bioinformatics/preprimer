"""
PrePrimer - Convert and analyze tiled primer schemes.

A modern, extensible tool for converting between different primer scheme formats
used in tiled amplicon sequencing.
"""

__version__ = "0.2.0"

# Import parsers, writers, and alignment providers to trigger auto-registration
import preprimer.alignment  # noqa: F401
import preprimer.parsers  # noqa: F401
import preprimer.writers  # noqa: F401

from .core.converter import PrimerConverter

# Import configuration
from .core.enhanced_config import EnhancedConfig
from .core.exceptions import OutputError, ParserError, PrePrimerError, ValidationError

# Import core components
from .core.interfaces import AmpliconData, OutputWriter, PrimerData, PrimerParser

# Import registries for advanced users
from .core.registry import parser_registry, writer_registry


# Convenience function for simple usage
def convert_primers(
    input_file,
    output_dir,
    input_format=None,
    output_formats=None,
    prefix="primers",
    reference_file=None,
    config=None,
    **kwargs,
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
        config: Configuration object (EnhancedConfig). If None, uses default.
        **kwargs: Additional configuration options

    Returns:
        Dictionary mapping format names to output file paths
    """
    # Use provided config or create default
    if config is None:
        config = EnhancedConfig()
    elif not isinstance(config, EnhancedConfig):
        raise TypeError(f"config must be EnhancedConfig, got {type(config)}")

    # Update config with kwargs if needed
    # Note: EnhancedConfig uses nested structure, so direct attribute setting is limited
    # Users should create proper EnhancedConfig instances instead

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
        **kwargs,
    )


__all__ = [
    "__version__",
    # Core components
    "PrimerParser",
    "OutputWriter",
    "PrimerData",
    "AmpliconData",
    # Configuration
    "EnhancedConfig",
    # Converter
    "PrimerConverter",
    # Exceptions
    "PrePrimerError",
    "ParserError",
    "ValidationError",
    "OutputError",
    # Registries
    "parser_registry",
    "writer_registry",
    # Convenience functions
    "convert_primers",
]
