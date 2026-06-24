"""
Alignment functionality for PrePrimer.

Provides primer and amplicon alignment using BLAST, Exonerate, me-PCR, and merPCR.
"""

import logging
from pathlib import Path
from typing import List, Union

from preprimer.core.registry import alignment_registry

logger = logging.getLogger(__name__)


def align_primers(
    sts_file: Union[str, Path],
    reference_file: Union[str, Path],
    output_dir: Union[str, Path],
    output_formats: List[str],
    aligner: str = "blast",
    prefix: str = "primers",
    force: bool = False,
) -> dict:
    """
    Align primers to a reference genome.

    Args:
        sts_file: Path to STS format primer file
        reference_file: Path to reference genome (FASTA)
        output_dir: Output directory for alignment results
        output_formats: List of output formats ('primers', 'me-pcr', 'merpcr')
        aligner: Alignment tool to use ('blast' or 'exonerate')
        prefix: Prefix for output files
        force: Force overwrite existing output

    Returns:
        Dictionary mapping output format to output path
    """
    sts_file = Path(sts_file)
    reference_file = Path(reference_file)
    output_dir = Path(output_dir)

    if not sts_file.exists():
        raise FileNotFoundError(f"STS file not found: {sts_file}")

    if not reference_file.exists():
        raise FileNotFoundError(f"Reference file not found: {reference_file}")

    output_paths = {}

    for output_format in output_formats:
        if output_format == "primers":
            # Align individual primers using BLAST or Exonerate
            primers_output_dir = output_dir / "alignment" / "primers"
            primers_output_dir.mkdir(parents=True, exist_ok=True)

            if aligner not in ["blast", "exonerate"]:
                raise ValueError(
                    f"Invalid aligner '{aligner}'. Must be 'blast' or 'exonerate'"
                )

            # Get alignment provider
            provider = alignment_registry.get_provider(aligner)

            if not provider.is_available():
                raise RuntimeError(
                    f"{aligner} is not available on this system. "
                    f"Please install {aligner} and ensure it's in your PATH."
                )

            logger.info(f"Running primer alignment with {aligner}...")
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=primers_output_dir,
            )

            output_paths["primers"] = output_path
            logger.info(f"Primer alignment results: {output_path}")

        else:
            # Any registered in-silico-PCR provider (me-pcr, merpcr, seqkit,
            # primersearch, mfeprimer, ...) runs uniformly via align_primers.
            if not alignment_registry.is_registered(output_format):
                raise ValueError(
                    f"Invalid output format '{output_format}'. Must be 'primers' "
                    f"or a registered in-silico-PCR tool: "
                    f"{', '.join(alignment_registry.list_providers())}"
                )

            tool_output_dir = output_dir / "alignment" / output_format
            tool_output_dir.mkdir(parents=True, exist_ok=True)

            provider = alignment_registry.get_provider(output_format)
            if not provider.is_available():
                raise RuntimeError(
                    f"{output_format} is not available on this system. "
                    f"Please install {output_format} and ensure it's in your PATH."
                )

            logger.info(f"Running {output_format} in silico PCR...")
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=tool_output_dir,
                prefix=prefix,
            )

            output_paths[output_format] = output_path
            logger.info(f"{output_format} results: {output_path}")

    return output_paths


def list_available_aligners() -> List[str]:
    """
    List alignment tools available on the system.

    Returns:
        List of available aligner names
    """
    return alignment_registry.list_available_providers()
