"""
Output format writers for different primer schemes.
"""

# Auto-register all writers
from ..core.registry import writer_registry
from .artic_writer import ARTICWriter
from .fasta_writer import FASTAWriter
from .gff3_writer import GFF3Writer
from .olivar_writer import OlivarWriter
from .sts_writer import STSWriter
from .varvamp_writer import VarVAMPWriter


def register_all_writers():
    """Register all available writers."""
    writer_registry.register(ARTICWriter)
    writer_registry.register(FASTAWriter)
    writer_registry.register(STSWriter)
    writer_registry.register(VarVAMPWriter)
    writer_registry.register(OlivarWriter)
    writer_registry.register(GFF3Writer)


# Auto-register on import
register_all_writers()

__all__ = [
    "ARTICWriter",
    "FASTAWriter",
    "STSWriter",
    "VarVAMPWriter",
    "OlivarWriter",
    "GFF3Writer",
    "register_all_writers",
]
