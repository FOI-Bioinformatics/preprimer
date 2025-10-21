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

        elif output_format == "me-pcr":
            # Run in silico PCR using me-PCR
            mepcr_output_dir = output_dir / "alignment" / "mepcr"
            mepcr_output_dir.mkdir(parents=True, exist_ok=True)

            # Get me-PCR provider
            mepcr_provider = alignment_registry.get_provider("me-pcr")

            if not mepcr_provider.is_available():
                raise RuntimeError(
                    "me-PCR is not available on this system. "
                    "Please install me-PCR and ensure it's in your PATH."
                )

            logger.info("Running me-PCR in silico PCR...")
            output_file = mepcr_output_dir / f"{prefix}.mepcr.aln"

            output_path = mepcr_provider.run_mepcr(
                primer_file=sts_file,
                reference=reference_file,
                output_file=output_file,
                max_product_size=1000,
            )

            output_paths["me-pcr"] = output_path
            logger.info(f"me-PCR results: {output_path}")

        elif output_format == "merpcr":
            # Run in silico PCR using merPCR
            merpcr_output_dir = output_dir / "alignment" / "merpcr"
            merpcr_output_dir.mkdir(parents=True, exist_ok=True)

            # Get merPCR provider
            merpcr_provider = alignment_registry.get_provider("merpcr")

            if not merpcr_provider.is_available():
                raise RuntimeError(
                    "merPCR is not available on this system. "
                    "Please install merPCR and ensure it's in your PATH."
                )

            logger.info("Running merPCR in silico PCR...")
            output_file = merpcr_output_dir / f"{prefix}.merpcr.aln"

            output_path = merpcr_provider.run_merpcr(
                primer_file=sts_file,
                reference=reference_file,
                output_file=output_file,
                max_product_size=1000,
            )

            output_paths["merpcr"] = output_path
            logger.info(f"merPCR results: {output_path}")

        else:
            raise ValueError(
                f"Invalid output format '{output_format}'. "
                f"Must be 'primers', 'me-pcr', or 'merpcr'"
            )

    return output_paths


def list_available_aligners() -> List[str]:
    """
    List alignment tools available on the system.

    Returns:
        List of available aligner names
    """
    return alignment_registry.list_available_providers()
