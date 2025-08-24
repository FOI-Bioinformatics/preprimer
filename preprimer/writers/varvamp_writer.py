"""
VarVAMP TSV format writer for PrePrimer.

Writes primer data to VarVAMP-compatible tab-separated format.
"""

import csv
from pathlib import Path
from typing import Dict, List, Union

from preprimer.core.interfaces import AmpliconData, OutputWriter


class VarVAMPWriter(OutputWriter):
    """Writer for VarVAMP TSV format."""

    @property
    def format_name(self) -> str:
        return "varvamp"

    @property
    def file_extension(self) -> str:
        return ".tsv"

    @property
    def description(self) -> str:
        return "VarVAMP tab-separated primer scheme format"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs
    ) -> Path:
        """
        Write amplicons to VarVAMP TSV format.

        Args:
            amplicons: List of amplicon data to write
            output_path: Output file path
            prefix: Prefix for primer names (optional)
            **kwargs: Additional options (reference_sequence, etc.)

        Returns:
            Path to the created file
        """
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare primer data for VarVAMP format
        primer_rows = []

        for amplicon in amplicons:
            amplicon_name = amplicon.amplicon_id

            # Add all primers from this amplicon
            for primer in amplicon.primers:
                row = {
                    "amplicon_name": amplicon_name,
                    "primer_name": primer.name,
                    "sequence": primer.sequence,
                    "start": primer.start,
                    "stop": primer.stop,
                    "length": len(primer.sequence),
                    "gc_content": self._calculate_gc_content(primer.sequence),
                    # Default Tm if not available
                    "tm": getattr(primer, "tm", 60.0),
                    # Use score as penalty
                    "penalty": getattr(primer, "score", 0.0),
                    "pool": primer.pool or 1,
                }
                primer_rows.append(row)

        # Write to TSV file
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if primer_rows:
                fieldnames = [
                    "amplicon_name",
                    "primer_name",
                    "sequence",
                    "start",
                    "stop",
                    "length",
                    "gc_content",
                    "tm",
                    "penalty",
                    "pool",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                writer.writerows(primer_rows)

        return output_path

    def _calculate_gc_content(self, sequence: str) -> float:
        """
        Calculate GC content of a DNA sequence.

        Args:
            sequence: DNA sequence string

        Returns:
            GC content as a ratio (0.0-1.0)
        """
        if not sequence:
            return 0.0

        sequence = sequence.upper()
        gc_count = sequence.count("G") + sequence.count("C")
        return round(gc_count / len(sequence), 3)

    def validate_output(self, output_path: Union[str, Path]) -> bool:
        """
        Validate that the output file was created correctly.

        Args:
            output_path: Path to the output file

        Returns:
            True if valid, False otherwise
        """
        output_path = Path(output_path)

        if not output_path.exists():
            return False

        try:
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")

                # Check required columns
                required_columns = {
                    "amplicon_name",
                    "primer_name",
                    "sequence",
                    "start",
                    "stop",
                    "pool",
                }

                if not required_columns.issubset(set(reader.fieldnames or [])):
                    return False

                # Check that we have at least one row
                try:
                    next(reader)
                    return True
                except StopIteration:
                    return False

        except Exception:
            return False

    def get_output_info(self) -> Dict[str, str]:
        """
        Get information about this output format.

        Returns:
            Dictionary with format information
        """
        return {
            "format": self.format_name,
            "extension": self.file_extension,
            "description": self.description,
            "use_case": "VarVAMP primer design tool input",
            "columns": (
                "amplicon_name, primer_name, sequence, start, stop, "
                "length, gc_content, tm, penalty, pool"
            ),
            "separator": "tab",
            "coordinate_system": "1-based",
        }
