"""
Alignment providers for PrePrimer.

Provides integration with external alignment tools:
- BLAST: Basic Local Alignment Search Tool
- Exonerate: Generic pairwise sequence alignment
- me-PCR: In silico PCR simulation (legacy)
- merPCR: Modern Electronic PCR (Python reimplementation)
"""

# Auto-register all alignment providers
from ..core.registry import alignment_registry
from .blast_provider import BlastProvider
from .exonerate_provider import ExonerateProvider
from .mepcr_provider import MePCRProvider
from .merpcr_provider import MerPCRProvider


def register_all_providers():
    """Register all available alignment providers."""
    alignment_registry.register(BlastProvider)
    alignment_registry.register(ExonerateProvider)
    alignment_registry.register(MePCRProvider)
    alignment_registry.register(MerPCRProvider)


# Auto-register on import
register_all_providers()

__all__ = [
    "BlastProvider",
    "ExonerateProvider",
    "MePCRProvider",
    "MerPCRProvider",
    "register_all_providers",
]
