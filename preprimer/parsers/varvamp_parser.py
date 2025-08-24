"""
VarVAMP primer format parser.
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Union

from ..core.exceptions import ParserError
from ..core.interfaces import AmpliconData, PrimerData, PrimerParser

logger = logging.getLogger(__name__)


class VarVAMPParser(PrimerParser):
    """Parser for VarVAMP primer format."""

    @property
    def format_name(self) -> str:
        return "varvamp"

    @property
    def file_extensions(self) -> List[str]:
        return [".tsv", ".txt"]

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in VarVAMP format."""
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        try:
            with open(file_path, "r") as f:
                # Check header
                header = f.readline().strip().split("\t")
                expected_cols = [
                    "amplicon_name",
                    "amplicon_length",
                    "primer_name",
                    "pool",
                    "start",
                    "stop",
                    "seq",
                    "size",
                    "gc_best",
                    "temp_best",
                    "mean_gc",
                    "mean_temp",
                    "score",
                ]

                # Handle common typos in VarVAMP files
                header_normalized = []
                for col in header:
                    col_clean = col.strip()
                    # Fix common typo: amlicon -> amplicon
                    if col_clean == "amlicon_name":
                        col_clean = "amplicon_name"
                    header_normalized.append(col_clean)

                # Check if all expected columns are present
                return all(col in header_normalized for col in expected_cols)

        except Exception as e:
            logger.debug(f"VarVAMP validation failed for {file_path}: {e}")
            return False

    def parse(
        self, file_path: Union[str, Path], prefix: str = ""
    ) -> List[AmpliconData]:
        """Parse VarVAMP primer file."""
        file_path = Path(file_path)

        if not self.validate_file(file_path):
            raise ParserError(f"File {file_path} is not a valid VarVAMP format")

        logger.info(f"Parsing VarVAMP file: {file_path}")

        amplicons = {}

        try:
            with open(file_path, "r") as f:
                reader = csv.DictReader(f, delimiter="\t")

                # Fix header names if needed
                if reader.fieldnames and "amlicon_name" in reader.fieldnames:
                    # Create a new fieldnames list with corrected names
                    new_fieldnames = []
                    for field in reader.fieldnames:
                        if field == "amlicon_name":
                            new_fieldnames.append("amplicon_name")
                        else:
                            new_fieldnames.append(field)
                    reader.fieldnames = new_fieldnames

                for row in reader:
                    amplicon_name = row["amplicon_name"]

                    # Determine primer direction and naming
                    primer_name = row["primer_name"]
                    if primer_name.startswith("FW"):
                        direction = "forward"
                        strand = "+"
                    elif primer_name.startswith("RW"):
                        direction = "reverse"
                        strand = "-"
                    else:
                        raise ParserError(
                            f"Unknown primer direction for: {primer_name}"
                        )

                    # Create PrimerData object
                    primer = PrimerData(
                        name=primer_name,
                        sequence=row["seq"],
                        start=int(row["start"]),
                        stop=int(row["stop"]),
                        strand=strand,
                        direction=direction,
                        pool=int(row["pool"]),
                        amplicon_id=amplicon_name,
                        reference_id=prefix or "ambiguous_consensus",
                        gc_content=float(row["gc_best"]),
                        tm=float(row["temp_best"]),
                        score=float(row["score"]),
                        metadata={
                            "mean_gc": float(row["mean_gc"]),
                            "mean_temp": float(row["mean_temp"]),
                            "amplicon_length": int(row["amplicon_length"]),
                        },
                    )

                    # Group primers by amplicon
                    if amplicon_name not in amplicons:
                        amplicons[amplicon_name] = AmpliconData(
                            amplicon_id=amplicon_name,
                            primers=[],
                            length=int(row["amplicon_length"]),
                            reference_id=prefix or "ambiguous_consensus",
                        )

                    amplicons[amplicon_name].primers.append(primer)

        except Exception as e:
            raise ParserError(f"Failed to parse VarVAMP file {file_path}: {e}")

        amplicon_list = list(amplicons.values())
        logger.info(
            f"Parsed {len(amplicon_list)} amplicons with "
            f"{sum(len(a.primers) for a in amplicon_list)} primers"
        )

        return amplicon_list

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """Get associated reference file (ambiguous_consensus.fasta)."""
        file_path = Path(file_path)
        ref_file = file_path.parent / "ambiguous_consensus.fasta"

        return ref_file if ref_file.exists() else None
