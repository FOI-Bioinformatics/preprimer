"""
Parser implementations for different primer formats.
"""

# Auto-register all parsers
from ..core.registry import parser_registry
from .artic_parser import ARTICParser
from .olivar_parser import OlivarParser
from .sts_parser import STSParser
from .varvamp_parser import VarVAMPParser


def register_all_parsers():
    """Register all available parsers."""
    parser_registry.register(VarVAMPParser)
    parser_registry.register(ARTICParser)
    parser_registry.register(OlivarParser)
    parser_registry.register(STSParser)


# Auto-register on import
register_all_parsers()

__all__ = [
    "VarVAMPParser",
    "ARTICParser",
    "OlivarParser",
    "STSParser",
    "register_all_parsers",
]
