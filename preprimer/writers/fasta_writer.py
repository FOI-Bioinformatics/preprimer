"""
FASTA format writer.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import AmpliconData, OutputWriter

logger = logging.getLogger(__name__)


class FASTAWriter(OutputWriter):
    """Writer for FASTA primer format."""

    @property
    def format_name(self) -> str:
        return "fasta"

    @property
    def file_extension(self) -> str:
        return ".fasta"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Optional[Path]:
        """Write amplicon data in FASTA format."""

        output_path = self.validate_output_path(output_path)

        logger.info(f"Writing FASTA primers to: {output_path}")

        try:
            with open(output_path, "w") as f:
                total_primers = 0

                for amplicon in amplicons:
                    for primer in amplicon.primers:
                        # Create FASTA header with primer information
                        # Use ARTIC naming for consistency
                        artic_name = primer.artic_name

                        # Add additional information in header
                        header_parts = [
                            artic_name,
                            f"pos={primer.start}-{primer.stop}",
                            f"strand={primer.strand}",
                            f"pool={primer.pool or 1}",
                        ]

                        # Add quality metrics if available
                        if primer.gc_content is not None:
                            header_parts.append(f"gc={primer.gc_content:.1f}")
                        if primer.tm is not None:
                            header_parts.append(f"tm={primer.tm:.1f}")
                        if primer.score is not None:
                            header_parts.append(f"score={primer.score:.2f}")

                        header = f">{' '.join(header_parts)}\n"
                        sequence = f"{primer.sequence}\n"

                        f.write(header)
                        f.write(sequence)
                        total_primers += 1

            logger.info(f"Successfully wrote {total_primers} primers to FASTA format")

            return output_path

        except Exception as e:
            raise OutputError(f"Failed to write FASTA format: {e}")
