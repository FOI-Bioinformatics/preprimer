"""
me-PCR alignment provider for PrePrimer.

Provides integration with me-PCR for in silico PCR simulation.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union

from preprimer.core.interfaces import AlignmentProvider


class MePCRProvider(AlignmentProvider):
    """me-PCR (in silico PCR simulation) provider."""

    @classmethod
    def tool_name(cls) -> str:
        """Return the name of the alignment tool."""
        return "me-pcr"

    def is_available(self) -> bool:
        """Check if me-PCR is available on the system."""
        return shutil.which("me-PCR") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "primers",
        max_product_size: int = 1000,
        **kwargs,
    ) -> Path:
        """
        Run in silico PCR using me-PCR.

        Args:
            primer_file: Path to primer file (STS format)
            reference_file: Path to reference genome (FASTA)
            output_dir: Output directory for me-PCR results
            prefix: Prefix for output filename
            max_product_size: Maximum PCR product size (default: 1000)
            **kwargs: Additional me-PCR parameters

        Returns:
            Path to me-PCR output file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        primer_file = Path(primer_file)
        reference_file = Path(reference_file)

        # Define output file
        output_file = output_dir / f"{prefix}.mepcr.aln"

        # Build me-PCR command
        # me-PCR format: me-PCR <primer_file> <reference> O=<output> M=<max_size>
        mepcr_command = [
            "me-PCR",
            str(primer_file),
            str(reference_file),
            f"O={output_file}",
            f"M={max_product_size}",
        ]

        # Run me-PCR (timeout guards against a hung external process)
        subprocess.run(
            mepcr_command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return output_file

    def run_mepcr(
        self,
        primer_file: Union[str, Path],
        reference: Union[str, Path],
        output_file: Union[str, Path],
        max_product_size: int = 1000,
    ) -> Path:
        """
        Run me-PCR directly with specified output file.

        Args:
            primer_file: Path to STS format primer file
            reference: Path to reference genome
            output_file: Path for output file
            max_product_size: Maximum amplicon size

        Returns:
            Path to output file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        mepcr_command = [
            "me-PCR",
            str(primer_file),
            str(reference),
            f"O={output_file}",
            f"M={max_product_size}",
        ]

        subprocess.run(
            mepcr_command,
            shell=False,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return output_file
