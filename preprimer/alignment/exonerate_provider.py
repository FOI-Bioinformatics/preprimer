"""
Exonerate alignment provider for PrePrimer.

Provides integration with Exonerate for primer alignment.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Union

from preprimer.core.interfaces import AlignmentProvider


class ExonerateProvider(AlignmentProvider):
    """Exonerate generic pairwise sequence alignment provider."""

    @classmethod
    def tool_name(cls) -> str:
        """Return the name of the alignment tool."""
        return "exonerate"

    def is_available(self) -> bool:
        """Check if Exonerate is available on the system."""
        return shutil.which("exonerate") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        **kwargs,
    ) -> Path:
        """
        Align primers to a reference genome using Exonerate.

        Args:
            primer_file: Path to primer file (STS format)
            reference_file: Path to reference genome (FASTA)
            output_dir: Output directory for alignment results
            **kwargs: Additional Exonerate parameters

        Returns:
            Path to Exonerate output directory
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
                    self._run_exonerate(
                        f"{amplicon_name}_fw",
                        output_dir,
                        fw_seq,
                        reference_file,
                    )

                    # Align reverse primer
                    self._run_exonerate(
                        f"{amplicon_name}_rw",
                        output_dir,
                        rw_seq,
                        reference_file,
                    )

        return output_dir

    def _run_exonerate(
        self,
        primer_id: str,
        output_dir: Path,
        sequence: str,
        reference: Path,
    ) -> Path:
        """
        Run Exonerate for a single primer sequence.

        Args:
            primer_id: Identifier for the primer
            output_dir: Output directory
            sequence: Primer sequence
            reference: Reference genome file

        Returns:
            Path to Exonerate output file
        """
        # Create temporary FASTA file for the primer
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".fasta"
        ) as seq_file:
            seq_file.write(f">{primer_id}\n{sequence}\n")
            seq_file_path = Path(seq_file.name)

        try:
            # Define output file
            output_file = output_dir / f"{primer_id}.aln"

            # Build Exonerate command
            exonerate_command = [
                "exonerate",
                "--model",
                "affine:local",
                "--query",
                str(seq_file_path),
                "--target",
                str(reference),
                "--showalignment",
                "TRUE",
                "--showvulgar",
                "FALSE",
                "--showcigar",
                "TRUE",
                "--ryo",
                "%qas",
                "--percent",
                "90",
                "--bestn",
                "1",
            ]

            # Run Exonerate
            with open(output_file, "w") as out_f:
                subprocess.run(
                    exonerate_command,
                    stdout=out_f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )

            return output_file

        finally:
            # Clean up temporary file
            seq_file_path.unlink(missing_ok=True)

    def parse_exonerate_output(self, output_file: Path) -> List[Dict[str, any]]:
        """
        Parse Exonerate output file.

        Args:
            output_file: Path to Exonerate output file

        Returns:
            List of alignment dictionaries
        """
        alignments = []

        if not output_file.exists():
            return alignments

        alignment = {}

        with open(output_file, "r") as f:
            for line in f:
                line = line.strip()

                if line.startswith("cigar:"):
                    # Process cigar line
                    parts = line.split()
                    if len(parts) >= 11:
                        alignment = {
                            "primer_name": parts[1],
                            "query_start": int(parts[2]),
                            "query_end": int(parts[3]),
                            "reference_id": parts[5],
                            "start": int(parts[6]),
                            "stop": int(parts[7]),
                            "strand": parts[8],
                            "score": float(parts[9]),
                            "cigar": (
                                f"{parts[10]}{parts[11]}"
                                if len(parts) > 11
                                else parts[10]
                            ),
                        }

                elif line.startswith(">"):
                    # Query sequence line
                    if alignment:
                        alignment["seq"] = line[1:]

                elif alignment and not line.startswith(("--", "C4", "Target", "Query")):
                    # Sequence data
                    if "seq" in alignment:
                        alignments.append(alignment)
                        alignment = {}

        # Add last alignment if exists
        if alignment:
            alignments.append(alignment)

        return alignments
