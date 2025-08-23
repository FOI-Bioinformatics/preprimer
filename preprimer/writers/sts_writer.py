"""
STS format writer for me-pcr.
"""

from pathlib import Path
from typing import List, Union, Optional
import logging

from ..core.interfaces import OutputWriter, AmpliconData
from ..core.exceptions import OutputError

logger = logging.getLogger(__name__)


class STSWriter(OutputWriter):
    """Writer for STS format used by me-pcr."""

    @property
    def format_name(self) -> str:
        return "sts"

    @property
    def file_extension(self) -> str:
        return ".sts.tsv"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        reference_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> None:
        """Write amplicon data in STS format for me-pcr."""

        output_path = self.validate_output_path(output_path)

        logger.info(f"Writing STS format to: {output_path}")

        try:
            with open(output_path, "w") as f:
                # Write STS header
                f.write("NAME\tFORWARD\tREVERSE\n")

                amplicon_count = 0

                for amplicon in amplicons:
                    # Get primer pairs for this amplicon
                    forward_primers = amplicon.forward_primers
                    reverse_primers = amplicon.reverse_primers

                    if not forward_primers or not reverse_primers:
                        logger.warning(
                            f"Skipping amplicon {amplicon.amplicon_id}: missing forward or reverse primer"
                        )
                        continue

                    # For STS format, use the first primer of each direction
                    # (me-pcr expects one forward and one reverse per amplicon)
                    forward_primer = forward_primers[0]
                    reverse_primer = reverse_primers[0]

                    # Create STS name (amplicon identifier)
                    sts_name = f"{amplicon.amplicon_id}"
                    if hasattr(amplicon, "reference_id") and amplicon.reference_id:
                        sts_name = f"{amplicon.reference_id}_{amplicon.amplicon_id}"

                    # Write STS line: NAME FORWARD REVERSE
                    sts_line = f"{sts_name}\t{forward_primer.sequence}\t{reverse_primer.sequence}\n"
                    f.write(sts_line)

                    amplicon_count += 1

                    # If there are multiple primers per direction, log warning
                    if len(forward_primers) > 1 or len(reverse_primers) > 1:
                        logger.info(
                            f"Amplicon {amplicon.amplicon_id} has multiple primers per direction, using first of each"
                        )

            logger.info(f"Successfully wrote {amplicon_count} amplicons to STS format")

            # If reference was provided, log it for user info
            if reference_path:
                logger.info(
                    f"STS file ready for use with me-pcr against reference: {reference_path}"
                )
                logger.info(
                    f"Example command: me-pcr -f {reference_path} -s {output_path}"
                )

        except Exception as e:
            raise OutputError(f"Failed to write STS format: {e}")
