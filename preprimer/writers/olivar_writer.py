"""
Olivar CSV format writer for PrePrimer.

Writes primer data to Olivar-compatible comma-separated format.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Union

from preprimer.core.interfaces import AmpliconData, OutputWriter


class OlivarWriter(OutputWriter):
    """Writer for Olivar CSV format."""

    @classmethod
    def format_name(cls) -> str:
        return "olivar"

    @classmethod
    def file_extension(cls) -> str:
        return ".csv"

    @property
    def description(self) -> str:
        return "Olivar comma-separated primer design format"

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Path:
        """
        Write amplicons to Olivar CSV format.

        Args:
            amplicons: List of amplicon data to write
            output_path: Output file path
            prefix: Prefix for amplicon names (optional)
            **kwargs: Additional options (reference_sequence, chrom_name, etc.)

        Returns:
            Path to the created file
        """
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get reference chromosome name from kwargs or use default
        chrom_name = kwargs.get("chrom_name", kwargs.get("reference_name", "ref"))

        # Prepare amplicon data for Olivar format
        amplicon_rows = []

        for amplicon in amplicons:
            # Get forward and reverse primers
            forward_primers = amplicon.forward_primers
            reverse_primers = amplicon.reverse_primers

            # Skip amplicons without both primer types
            if not forward_primers or not reverse_primers:
                continue

            # Use first primer of each type for Olivar format (one amplicon per
            # row)
            forward_primer = forward_primers[0]
            reverse_primer = reverse_primers[0]

            amplicon_id = (
                f"{prefix}_{amplicon.amplicon_id}" if prefix else amplicon.amplicon_id
            )

            # Calculate amplicon coordinates
            # Use primer coordinates to determine amplicon span
            start_coord = min(forward_primer.start, reverse_primer.start)
            end_coord = max(forward_primer.stop, reverse_primer.stop)

            # Get pool from primers (should be same for both)
            pool = forward_primer.pool or reverse_primer.pool or 1

            row = {
                "amplicon_id": amplicon_id,
                "chrom": chrom_name,
                "pool": pool,
                "start": start_coord,
                "end": end_coord,
                "fP": forward_primer.sequence,  # Forward primer
                "rP": reverse_primer.sequence,  # Reverse primer
            }
            amplicon_rows.append(row)

        # Write to CSV file
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if amplicon_rows:
                fieldnames = [
                    "amplicon_id",
                    "chrom",
                    "pool",
                    "start",
                    "end",
                    "fP",
                    "rP",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(amplicon_rows)

        return output_path

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
                reader = csv.DictReader(f)

                # Check required columns
                required_columns = {"amplicon_id", "fP", "rP"}

                if not required_columns.issubset(set(reader.fieldnames or [])):
                    return False

                # Check that we have at least one row with valid primers
                for row in reader:
                    if row.get("fP") and row.get("rP"):
                        return True

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
            "format": self.format_name(),
            "extension": self.file_extension(),
            "description": self.description,
            "use_case": "Olivar variant-aware primer design tool input",
            "columns": (
                "amplicon_id, chrom, pool, start, end, "
                "fP (forward primer), rP (reverse primer)"
            ),
            "separator": "comma",
            "coordinate_system": "variable (depends on input)",
            "layout": "One amplicon per row (forward/reverse primers in same row)",
        }

    def write_with_metadata(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        metadata: Optional[Dict] = None,
    ) -> Path:
        """
        Write amplicons with additional metadata fields.

        Args:
            amplicons: List of amplicon data to write
            output_path: Output file path
            prefix: Prefix for amplicon names (optional)
            metadata: Additional metadata to include

        Returns:
            Path to the created file
        """
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get reference chromosome name from metadata or use default
        chrom_name = "ref"
        if metadata:
            chrom_name = metadata.get(
                "chrom_name", metadata.get("reference_name", "ref")
            )

        # Prepare amplicon data for Olivar format with metadata
        amplicon_rows = []

        for amplicon in amplicons:
            # Get forward and reverse primers
            forward_primers = amplicon.forward_primers
            reverse_primers = amplicon.reverse_primers

            # Skip amplicons without both primer types
            if not forward_primers or not reverse_primers:
                continue

            # Use first primer of each type for Olivar format
            forward_primer = forward_primers[0]
            reverse_primer = reverse_primers[0]

            amplicon_id = (
                f"{prefix}_{amplicon.amplicon_id}" if prefix else amplicon.amplicon_id
            )

            # Calculate amplicon coordinates
            start_coord = min(forward_primer.start, reverse_primer.start)
            end_coord = max(forward_primer.stop, reverse_primer.stop)

            # Get pool from primers
            pool = forward_primer.pool or reverse_primer.pool or 1

            row = {
                "amplicon_id": amplicon_id,
                "chrom": chrom_name,
                "pool": pool,
                "start": start_coord,
                "end": end_coord,
                "fP": forward_primer.sequence,
                "rP": reverse_primer.sequence,
                "amplicon_length": end_coord - start_coord,
                "forward_primer_length": len(forward_primer.sequence),
                "reverse_primer_length": len(reverse_primer.sequence),
            }

            # Add metadata fields if available
            if metadata:
                row.update(
                    {k: v for k, v in metadata.items() if k not in row}
                )  # Don't overwrite existing fields

            amplicon_rows.append(row)

        # Write to CSV file
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if amplicon_rows:
                fieldnames = list(amplicon_rows[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(amplicon_rows)

        return output_path
