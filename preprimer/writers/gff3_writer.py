"""
GFF3 writer.

Emits primer binding sites as GFF3 features for genome-browser visualization.
GFF3 is 1-based, inclusive; PrimerData stores 0-based half-open coordinates, so
a primer at [start, stop) is written as start+1 .. stop.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import AmpliconData, OutputWriter

logger = logging.getLogger(__name__)


class GFF3Writer(OutputWriter):
    """Writer for GFF3 primer-feature annotations."""

    @classmethod
    def format_name(cls) -> str:
        return "gff3"

    @classmethod
    def file_extension(cls) -> str:
        return ".gff3"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Optional[Path]:
        """Write primers as GFF3 ``primer_binding_site`` features."""
        output_path = self.validate_output_path(output_path)

        try:
            with open(output_path, "w") as f:
                f.write("##gff-version 3\n")
                for amplicon in amplicons:
                    for primer in amplicon.primers:
                        # 0-based half-open -> 1-based inclusive.
                        gff_start = max(1, primer.start + 1)
                        gff_end = primer.stop
                        attributes = (
                            f"ID={primer.name};"
                            f"amplicon={amplicon.amplicon_id};"
                            f"pool={primer.pool or 1}"
                        )
                        if primer.sequence:
                            attributes += f";sequence={primer.sequence}"
                        fields = [
                            primer.reference_id or "unknown",
                            "PrePrimer",
                            "primer_binding_site",
                            str(gff_start),
                            str(gff_end),
                            ".",
                            primer.strand,
                            ".",
                            attributes,
                        ]
                        f.write("\t".join(fields) + "\n")
            return output_path
        except Exception as e:
            raise OutputError(f"Failed to write GFF3 format: {e}")
