"""
BLAST alignment provider for PrePrimer.

Provides integration with NCBI BLAST for primer alignment.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Union

from preprimer.core.interfaces import AlignmentProvider


class BlastProvider(AlignmentProvider):
    """BLAST (Basic Local Alignment Search Tool) alignment provider."""

    @classmethod
    def tool_name(cls) -> str:
        """Return the name of the alignment tool."""
        return "blast"

    def is_available(self) -> bool:
        """Check if BLAST is available on the system."""
        return shutil.which("blastn") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        output_format: str = "6",
        **kwargs,
    ) -> Path:
        """
        Align primers to a reference genome using BLAST.

        Args:
            primer_file: Path to primer file (STS format)
            reference_file: Path to reference genome (FASTA)
            output_dir: Output directory for alignment results
            output_format: BLAST output format (default: "6" tabular, which is
                what parse_blast_output() consumes)
            **kwargs: Additional BLAST parameters

        Returns:
            Path to BLAST output directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        primer_file = Path(primer_file)
        reference_file = Path(reference_file)

        # Read STS file and align each primer
        with open(primer_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    amplicon_name = parts[0]
                    fw_seq = parts[1]
                    rw_seq = parts[2]

                    # Align forward primer
                    self._run_blast(
                        f"{amplicon_name}_fw",
                        output_dir,
                        fw_seq,
                        reference_file,
                        output_format,
                    )

                    # Align reverse primer
                    self._run_blast(
                        f"{amplicon_name}_rw",
                        output_dir,
                        rw_seq,
                        reference_file,
                        output_format,
                    )

        return output_dir

    def _run_blast(
        self,
        primer_id: str,
        output_dir: Path,
        sequence: str,
        reference: Path,
        output_format: str = "6",
    ) -> Path:
        """
        Run BLAST for a single primer sequence.

        Args:
            primer_id: Identifier for the primer
            output_dir: Output directory
            sequence: Primer sequence
            reference: Reference genome file
            output_format: BLAST output format

        Returns:
            Path to BLAST output file
        """
        # Create temporary FASTA file for the primer
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".fasta"
        ) as seq_file:
            seq_file.write(f">{primer_id}\n{sequence}\n")
            seq_file_path = Path(seq_file.name)

        try:
            # Define output file
            output_file = output_dir / f"{primer_id}.blast"

            # Build BLAST command
            blast_command = [
                "blastn",
                "-query",
                str(seq_file_path),
                "-subject",
                str(reference),
                "-outfmt",
                output_format,
                "-out",
                str(output_file),
                "-task",
                "blastn-short",  # Optimized for short sequences like primers
            ]

            # Run BLAST (timeout guards against a hung external process)
            subprocess.run(
                blast_command,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return output_file

        finally:
            # Clean up temporary file
            seq_file_path.unlink(missing_ok=True)

    def parse_blast_output(self, output_file: Path) -> List[Dict[str, Any]]:
        """
        Parse BLAST output in tabular format (outfmt 6).

        Args:
            output_file: Path to BLAST output file

        Returns:
            List of alignment dictionaries
        """
        alignments = []

        if not output_file.exists():
            return alignments

        with open(output_file, "r") as f:
            for line in f:
                if line.startswith("#"):
                    continue

                parts = line.strip().split("\t")
                if len(parts) >= 12:
                    alignment = {
                        "primer_name": parts[0],
                        "reference_id": parts[1],
                        "identity": float(parts[2]),
                        "length": int(parts[3]),
                        "query_start": int(parts[6]),
                        "query_end": int(parts[7]),
                        "start": int(parts[8]),
                        "stop": int(parts[9]),
                        "evalue": float(parts[10]),
                        "bitscore": float(parts[11]),
                        "strand": "+" if int(parts[8]) < int(parts[9]) else "-",
                    }
                    alignments.append(alignment)

        return alignments
