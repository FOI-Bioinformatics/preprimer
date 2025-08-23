"""
Output format writers for different primer schemes.
"""

from .artic_writer import ARTICWriter
from .fasta_writer import FASTAWriter 
from .sts_writer import STSWriter
from .varvamp_writer import VarVAMPWriter
from .olivar_writer import OlivarWriter

# Auto-register all writers
from ..core.registry import writer_registry

def register_all_writers():
    """Register all available writers."""
    writer_registry.register(ARTICWriter)
    writer_registry.register(FASTAWriter)
    writer_registry.register(STSWriter)
    writer_registry.register(VarVAMPWriter)
    writer_registry.register(OlivarWriter)

# Auto-register on import
register_all_writers()

__all__ = [
    'ARTICWriter',
    'FASTAWriter',
    'STSWriter',
    'VarVAMPWriter',
    'OlivarWriter',
    'register_all_writers'
]