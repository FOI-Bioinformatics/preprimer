"""
STS format writer for me-pcr and merPCR.

Supports both 3-column and 4-column (extended) formats.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from ..core.exceptions import OutputError
from ..core.interfaces import AmpliconData, OutputWriter

logger = logging.getLogger(__name__)


class STSWriter(OutputWriter):
    """Writer for STS format used by me-pcr and merPCR."""

    @classmethod
    def format_name(cls) -> str:
        return "sts"

    @classmethod
    def file_extension(cls) -> str:
        return ".sts.tsv"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Optional[Path]:
        """
        Write amplicon data in STS format for me-pcr/merPCR.

        Args:
            amplicons: List of AmpliconData objects
            output_path: Output file path
            prefix: Prefix for naming (unused in STS)
            **kwargs: Additional options:
                - include_size: bool - Include SIZE column (default: auto-detect)
                - include_header: bool - Include header row (default: True)
                - reference_path: Path - Reference file path for logging

        Returns:
            Path to written file
        """
        output_path = self.validate_output_path(output_path)
        reference_path = kwargs.get("reference_path")

        # Determine if we should include SIZE column
        # Auto-detect: include if any amplicon has length information
        include_size = kwargs.get("include_size")
        if include_size is None:
            # Auto-detect: check if any amplicons have meaningful length info
            include_size = any(amp.length and amp.length > 0 for amp in amplicons)
            logger.info(
                f"Auto-detected STS format: "
                f"{'4-column (with SIZE)' if include_size else '3-column'}"
            )

        # Determine if we should include header
        include_header = kwargs.get("include_header", True)

        logger.info(f"Writing STS format to: {output_path}")

        try:
            with open(output_path, "w") as f:
                # Write STS header if requested
                if include_header:
                    if include_size:
                        f.write("NAME\tFORWARD\tREVERSE\tSIZE\n")
                    else:
                        f.write("NAME\tFORWARD\tREVERSE\n")

                amplicon_count = 0

                for amplicon in amplicons:
                    # Get primer pairs for this amplicon
                    forward_primers = amplicon.forward_primers
                    reverse_primers = amplicon.reverse_primers

                    if not forward_primers or not reverse_primers:
                        logger.warning(
                            f"Skipping amplicon {amplicon.amplicon_id}: "
                            "missing forward or reverse primer"
                        )
                        continue

                    # For STS format, use the first primer of each direction
                    # (me-pcr/merPCR expects one forward and one reverse per amplicon)
                    forward_primer = forward_primers[0]
                    reverse_primer = reverse_primers[0]

                    # Create STS name (amplicon identifier)
                    sts_name = amplicon.amplicon_id
                    if hasattr(amplicon, "reference_id") and amplicon.reference_id:
                        # Check if amplicon_id already contains reference_id to avoid duplication
                        if not amplicon.amplicon_id.startswith(amplicon.reference_id):
                            sts_name = f"{amplicon.reference_id}_{amplicon.amplicon_id}"

                    # Build STS line
                    sts_line = f"{sts_name}\t{forward_primer.sequence}\t{reverse_primer.sequence}"

                    # Add SIZE column if requested
                    if include_size:
                        # Use amplicon length if available, otherwise estimate
                        size = amplicon.length if amplicon.length else 300
                        sts_line += f"\t{size}"

                    sts_line += "\n"
                    f.write(sts_line)

                    amplicon_count += 1

                    # If there are multiple primers per direction, warn that
                    # alternate primers are being dropped.
                    if len(forward_primers) > 1 or len(reverse_primers) > 1:
                        logger.warning(
                            f"Amplicon {amplicon.amplicon_id} has multiple primers "
                            "per direction; keeping only the first of each "
                            "(alternates dropped)"
                        )

            format_desc = f"{'4-column' if include_size else '3-column'} STS format"
            logger.info(
                f"Successfully wrote {amplicon_count} amplicons to {format_desc}"
            )

            # If reference was provided, log usage examples
            if reference_path:
                logger.info(
                    f"STS file ready for use with me-pcr/merPCR against reference: "
                    f"{reference_path}"
                )
                if include_size:
                    logger.info(
                        f"Example command: merpcr {output_path} {reference_path}"
                    )
                else:
                    logger.info(
                        f"Example command: me-pcr -f {reference_path} -s {output_path}"
                    )

            return output_path

        except Exception as e:
            raise OutputError(f"Failed to write STS format: {e}")
