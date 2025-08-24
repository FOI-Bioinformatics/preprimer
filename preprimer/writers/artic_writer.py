"""
ARTIC format writer.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import AmpliconData, OutputWriter

logger = logging.getLogger(__name__)


class ARTICWriter(OutputWriter):
    """Writer for ARTIC primer scheme format."""

    @property
    def format_name(self) -> str:
        return "artic"

    @property
    def file_extension(self) -> str:
        return ".scheme.bed"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Optional[Path]:
        """Write amplicon data in ARTIC format."""

        output_path = self.validate_output_path(output_path)

        # ARTIC format requires a specific directory structure
        # output_path should be like: schemes/artic/PREFIX/V1/PREFIX.scheme.bed
        prefix = prefix or kwargs.get("prefix", "primers")
        reference_path = kwargs.get("reference_path")

        # Create ARTIC directory structure
        artic_dir = output_path.parent
        scheme_file = artic_dir / f"{prefix}.scheme.bed"
        reference_file = artic_dir / f"{prefix}.reference.fasta"

        logger.info(f"Writing ARTIC scheme to: {scheme_file}")

        try:
            # Write BED file
            with open(scheme_file, "w") as f:
                for amplicon in amplicons:
                    for primer in amplicon.primers:
                        # ARTIC BED format:
                        # chrom start end name pool strand sequence

                        # Use ARTIC naming convention
                        artic_name = primer.artic_name

                        bed_line = f"{
                            primer.reference_id}\t{
                            primer.start}\t{
                            primer.stop}\t{artic_name}\t{
                            primer.pool or 1}\t{
                            primer.strand}\t{
                            primer.sequence}\n"
                        f.write(bed_line)

            # Copy reference file if provided
            if reference_path:
                reference_path = Path(reference_path)
                if reference_path.exists():
                    logger.info(f"Copying reference to: {reference_file}")
                    shutil.copy2(reference_path, reference_file)
                else:
                    logger.warning(f"Reference file not found: {reference_path}")

            # Write summary info
            total_primers = sum(len(a.primers) for a in amplicons)
            logger.info(
                f"Successfully wrote ARTIC scheme with {len(amplicons)} "
                f"amplicons and {total_primers} primers"
            )

            return scheme_file

        except Exception as e:
            raise OutputError(f"Failed to write ARTIC format: {e}")

    def validate_output_path(self, output_path: Union[str, Path]) -> Path:
        """Validate and create ARTIC directory structure."""
        path = Path(output_path)

        # Create full directory structure
        path.parent.mkdir(parents=True, exist_ok=True)

        return path
