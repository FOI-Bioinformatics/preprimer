"""
merPCR alignment provider for PrePrimer.

Provides integration with merPCR, a modern Python reimplementation of me-PCR
for in silico PCR simulation with improved performance and documentation.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union

from preprimer.core.interfaces import AlignmentProvider


class MerPCRProvider(AlignmentProvider):
    """merPCR (Modern Electronic PCR) provider.

    merPCR is a 100% compatible Python reimplementation of me-PCR
    with improved performance (2.65x faster) and modern Python API.
    """

    @classmethod
    def tool_name(cls) -> str:
        """Return the name of the alignment tool."""
        return "merpcr"

    def is_available(self) -> bool:
        """Check if merPCR is available on the system."""
        return shutil.which("merpcr") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "primers",
        max_product_size: int = 1000,
        margin: int = 50,
        mismatches: int = 0,
        wordsize: int = 11,
        **kwargs,
    ) -> Path:
        """
        Run in silico PCR using merPCR.

        Args:
            primer_file: Path to primer file (STS format)
            reference_file: Path to reference genome (FASTA)
            output_dir: Output directory for merPCR results
            prefix: Prefix for output filename
            max_product_size: Maximum PCR product size (default: 1000)
            margin: Search margin in base pairs (default: 50)
            mismatches: Allowed mismatches (default: 0)
            wordsize: Hash word size (default: 11)
            **kwargs: Additional merPCR parameters

        Returns:
            Path to merPCR output file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        primer_file = Path(primer_file)
        reference_file = Path(reference_file)

        # Define output file
        output_file = output_dir / f"{prefix}.merpcr.aln"

        # Build merPCR command with modern flag syntax
        merpcr_command = [
            "merpcr",
            str(primer_file),
            str(reference_file),
            "-O",
            str(output_file),
            "-M",
            str(margin),
            "-N",
            str(mismatches),
            "-W",
            str(wordsize),
        ]

        # Add max product size if provided
        if max_product_size:
            merpcr_command.extend(["-Z", str(max_product_size)])

        # Run merPCR
        subprocess.run(
            merpcr_command,
            check=True,
            capture_output=True,
            text=True,
        )

        return output_file

    def run_merpcr(
        self,
        primer_file: Union[str, Path],
        reference: Union[str, Path],
        output_file: Union[str, Path],
        max_product_size: int = 1000,
        margin: int = 50,
        mismatches: int = 0,
        wordsize: int = 11,
    ) -> Path:
        """
        Run merPCR directly with specified output file.

        Args:
            primer_file: Path to STS format primer file
            reference: Path to reference genome
            output_file: Path for output file
            max_product_size: Maximum amplicon size (default: 1000)
            margin: Search margin in base pairs (default: 50)
            mismatches: Allowed mismatches (default: 0)
            wordsize: Hash word size (default: 11)

        Returns:
            Path to output file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        merpcr_command = [
            "merpcr",
            str(primer_file),
            str(reference),
            "-O",
            str(output_file),
            "-M",
            str(margin),
            "-N",
            str(mismatches),
            "-W",
            str(wordsize),
        ]

        if max_product_size:
            merpcr_command.extend(["-Z", str(max_product_size)])

        subprocess.run(merpcr_command, shell=False, check=True)

        return output_file
