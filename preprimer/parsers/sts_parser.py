"""
STS (Sequence Tagged Site) format parser for me-pcr.

The STS format is a simple TSV format with three columns:
- NAME: Amplicon identifier
- FORWARD: Forward primer sequence
- REVERSE: Reverse primer sequence
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.exceptions import (
    CorruptedDataError,
    ErrorContext,
    InsufficientDataError,
    InvalidFormatError,
    ParserError,
    SecurityError,
    handle_common_exceptions,
)
from ..core.interfaces import AmpliconData
from ..core.standardized_parser import StandardizedParser

logger = logging.getLogger(__name__)


class STSParser(StandardizedParser):
    """Parser for STS (Sequence Tagged Site) format used by me-pcr."""

    @classmethod
    def format_name(cls) -> str:
        return "sts"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".sts.tsv", ".sts", ".tsv"]

    @handle_common_exceptions("STS file validation")
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in STS format."""
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Check header
                header_line = f.readline().strip()
                if not header_line:
                    logger.debug(f"Empty file or no header: {file_path}")
                    return False

                # Split by tab and normalize
                header = [col.strip().upper() for col in header_line.split("\t")]

                # Check for required columns (case-insensitive)
                required_cols = ["NAME", "FORWARD", "REVERSE"]
                if header != required_cols:
                    logger.debug(
                        f"Invalid STS header in {file_path}. "
                        f"Expected {required_cols}, got {header}"
                    )
                    return False

                # Check if there's at least one data line
                data_line = f.readline().strip()
                if not data_line:
                    logger.debug(f"No data lines in {file_path}")
                    return False

                # Validate data line has 3 tab-separated fields
                fields = data_line.split("\t")
                if len(fields) != 3:
                    logger.debug(
                        f"Invalid STS data format: expected 3 fields, got {len(fields)}"
                    )
                    return False

                return True

        except UnicodeDecodeError as e:
            logger.debug(f"File encoding issue for {file_path}: {e}")
            return False
        except Exception as e:
            logger.debug(f"STS validation failed for {file_path}: {e}")
            return False

    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        """
        Parse STS format file content with comprehensive error handling.

        Args:
            file_path: Validated path to STS file
            prefix: Validated prefix for primer naming

        Returns:
            Dictionary of AmpliconData objects keyed by amplicon_id

        Raises:
            ParserError: If file format is invalid
            CorruptedDataError: If data appears corrupted
            InsufficientDataError: If insufficient data found
        """
        amplicons = {}

        with ErrorContext(f"parsing STS file {file_path}"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(
                        f, delimiter="\t", fieldnames=["NAME", "FORWARD", "REVERSE"]
                    )

                    # Skip header row
                    next(reader)

                    processed_rows = 0
                    for row_num, row in enumerate(
                        reader, start=2
                    ):  # Start at 2 for header
                        try:
                            # Skip completely empty rows
                            if not any(row.values()):
                                logger.debug(f"Skipping empty row {row_num}")
                                continue

                            # Validate required fields
                            required_fields = ["NAME", "FORWARD", "REVERSE"]
                            self._validate_required_fields(
                                row, required_fields, row_num
                            )

                            # Sanitize input data
                            amplicon_name = self._sanitize_string_field(
                                row["NAME"], "NAME", row_num, 100
                            )
                            forward_seq = self._sanitize_string_field(
                                row["FORWARD"], "FORWARD", row_num, 1000
                            )
                            reverse_seq = self._sanitize_string_field(
                                row["REVERSE"], "REVERSE", row_num, 1000
                            )

                            # Validate sequences
                            if not forward_seq or not reverse_seq:
                                raise CorruptedDataError(
                                    str(file_path),
                                    details=f"Empty sequence at row {row_num}",
                                    user_message=f"Row {row_num} contains empty primer sequence.",
                                ).add_suggestion(
                                    "Check that both FORWARD and REVERSE sequences are provided"
                                )

                            # Create primer names
                            forward_name = f"{amplicon_name}_LEFT"
                            reverse_name = f"{amplicon_name}_RIGHT"

                            # For STS format, we don't have coordinate information
                            # We'll use placeholder coordinates and let the user provide
                            # reference if they need actual positions
                            forward_start = 0
                            forward_stop = len(forward_seq)
                            reverse_start = forward_stop + 300  # Assume ~300bp amplicon
                            reverse_stop = reverse_start + len(reverse_seq)

                            # Create PrimerData objects
                            forward_primer = self._create_primer_data(
                                name=forward_name,
                                sequence=forward_seq.upper(),
                                start=forward_start,
                                stop=forward_stop,
                                strand="+",
                                direction="forward",
                                pool=1,  # STS doesn't specify pools
                                amplicon_id=amplicon_name,
                                reference_id=prefix or "unknown",
                                metadata={"source_row": row_num},
                            )

                            reverse_primer = self._create_primer_data(
                                name=reverse_name,
                                sequence=reverse_seq.upper(),
                                start=reverse_start,
                                stop=reverse_stop,
                                strand="-",
                                direction="reverse",
                                pool=1,
                                amplicon_id=amplicon_name,
                                reference_id=prefix or "unknown",
                                metadata={"source_row": row_num},
                            )

                            # Validate primer data
                            self._validate_primer_data(
                                forward_name,
                                forward_seq,
                                forward_start,
                                forward_stop,
                                row_num,
                            )
                            self._validate_primer_data(
                                reverse_name,
                                reverse_seq,
                                reverse_start,
                                reverse_stop,
                                row_num,
                            )

                            # Create or update amplicon
                            if amplicon_name not in amplicons:
                                amplicons[amplicon_name] = AmpliconData(
                                    amplicon_id=amplicon_name,
                                    primers=[],
                                    length=reverse_stop - forward_start,
                                    reference_id=prefix or "unknown",
                                )

                            amplicons[amplicon_name].primers.append(forward_primer)
                            amplicons[amplicon_name].primers.append(reverse_primer)
                            processed_rows += 1

                        except (
                            ParserError,
                            SecurityError,
                            InvalidFormatError,
                            CorruptedDataError,
                        ):
                            # Re-raise our specific errors
                            raise
                        except Exception as e:
                            # Wrap unexpected errors
                            raise CorruptedDataError(
                                str(file_path),
                                details=f"Unexpected error processing row {row_num}: {e}",
                                user_message=f"Error processing data in row {row_num}. The row may be malformed.",
                            ).add_suggestion(
                                "Check the data format in the problematic row"
                            ) from e

                    # Validate that we processed some data
                    if processed_rows == 0:
                        raise InsufficientDataError(
                            "No valid primer data found in STS file",
                            user_message=f"No valid primer data found in {file_path}. The file may be empty or contain only invalid rows.",
                        ).add_suggestion(
                            "Verify that the file contains properly formatted STS data"
                        )

                    logger.info(
                        f"Successfully parsed {processed_rows} amplicons from STS file"
                    )

            except UnicodeDecodeError as e:
                raise InvalidFormatError(
                    str(file_path),
                    expected_format="UTF-8 encoded STS TSV",
                    user_message=f"File encoding error: {file_path}. The file may not be UTF-8 encoded.",
                ).add_suggestion("Try re-saving the file with UTF-8 encoding") from e

            except FileNotFoundError as e:
                raise ParserError(
                    f"STS file not found: {file_path}",
                    file_path=str(file_path),
                    user_message=f"File not found: {file_path}",
                ) from e

            except PermissionError as e:
                raise ParserError(
                    f"Permission denied reading STS file: {file_path}",
                    file_path=str(file_path),
                    user_message=f"Permission denied: Cannot read {file_path}",
                ).add_suggestion("Check file permissions and try again") from e

        return amplicons

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        Get associated reference file.

        STS format doesn't typically have an associated reference file,
        so this returns None. Users should provide reference explicitly if needed.

        Args:
            file_path: Path to the STS file

        Returns:
            None (STS format doesn't have associated reference files)
        """
        # STS format is coordinate-free, no associated reference
        return None
