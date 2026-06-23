"""
STS (Sequence Tagged Site) format parser for me-pcr and merPCR.

The STS format is a simple TSV format with 3-4 columns:
- NAME: Amplicon identifier
- FORWARD: Forward primer sequence
- REVERSE: Reverse primer sequence
- SIZE: (Optional) Expected product size in bp

Supports both header and header-less formats for compatibility with
me-pcr and merPCR output files.
"""

import csv
import logging
import re
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
    """Parser for STS (Sequence Tagged Site) format used by me-pcr and merPCR."""

    @classmethod
    def format_name(cls) -> str:
        return "sts"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".sts.tsv", ".sts", ".tsv"]

    def _detect_header(self, first_line: str) -> bool:
        """
        Detect if first line is a header or data.

        Headers contain column names like NAME, FORWARD, REVERSE.
        Data lines contain actual sequences (DNA bases).

        Args:
            first_line: First line of the file

        Returns:
            True if first line appears to be a header, False if it's data
        """
        fields = first_line.strip().split("\t")

        if len(fields) < 3:
            return False

        # Check if first field looks like a header (NAME, AMPLICON, ID, etc.)
        first_field_upper = fields[0].strip().upper()
        header_keywords = ["NAME", "AMPLICON", "ID", "MARKER", "STS"]
        if any(keyword in first_field_upper for keyword in header_keywords):
            return True

        # Check if second/third fields look like headers (FORWARD, REVERSE, etc.)
        second_field_upper = fields[1].strip().upper()
        third_field_upper = fields[2].strip().upper()

        primer_keywords = [
            "FORWARD",
            "REVERSE",
            "FWD",
            "REV",
            "LEFT",
            "RIGHT",
            "PRIMER",
        ]
        if any(keyword in second_field_upper for keyword in primer_keywords):
            return True
        if any(keyword in third_field_upper for keyword in primer_keywords):
            return True

        # Check if fields look like DNA sequences (mostly ATCG)
        # If second field is mostly DNA bases, it's likely data not header
        dna_pattern = re.compile(r"^[ATCGNRYSWKMBDHVatcgn]+$")
        if dna_pattern.match(fields[1].strip()):
            return False  # Looks like sequence data

        # Default: assume header if we're unsure
        return True

    @handle_common_exceptions("STS file validation")
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in STS format (3 or 4 columns, with or without header)."""
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

                if len(lines) < 1:
                    logger.debug(f"Empty file: {file_path}")
                    return False

                # Check first line structure
                first_line = lines[0]
                fields = first_line.split("\t")

                # Must have 3 or 4 tab-separated fields
                if len(fields) not in [3, 4]:
                    logger.debug(
                        f"Invalid STS format: expected 3 or 4 fields, got {len(fields)} in {file_path}"
                    )
                    return False

                # Detect if we have a header
                has_header = self._detect_header(first_line)

                # If header detected, validate it has correct column names
                if has_header:
                    header_fields_upper = [f.strip().upper() for f in fields]

                    # First field should be a name/ID field
                    valid_name_fields = ["NAME", "AMPLICON", "ID", "MARKER", "STS"]
                    if not any(
                        keyword in header_fields_upper[0]
                        for keyword in valid_name_fields
                    ):
                        logger.debug(
                            f"Invalid header: first field '{fields[0]}' doesn't match expected name fields"
                        )
                        return False

                    # Second and third fields should be primer-related
                    primer_keywords = [
                        "FORWARD",
                        "REVERSE",
                        "FWD",
                        "REV",
                        "LEFT",
                        "RIGHT",
                        "PRIMER",
                    ]
                    has_primer_keyword = False
                    for field in header_fields_upper[1:3]:  # Check 2nd and 3rd fields
                        if any(keyword in field for keyword in primer_keywords):
                            has_primer_keyword = True
                            break

                    if not has_primer_keyword:
                        logger.debug(
                            f"Invalid header: no primer-related keywords in fields {fields[1:3]}"
                        )
                        return False

                # Get a data line (skip header if present)
                data_line_idx = 1 if has_header else 0
                if len(lines) <= data_line_idx:
                    logger.debug(f"No data lines in {file_path}")
                    return False

                data_fields = lines[data_line_idx].split("\t")
                if len(data_fields) not in [3, 4]:
                    logger.debug(
                        f"Invalid data line format: expected 3 or 4 fields, got {len(data_fields)}"
                    )
                    return False

                # Validate that second/third fields look like DNA sequences
                dna_pattern = re.compile(r"^[ATCGNRYSWKMBDHVatcgn]+$")
                if not dna_pattern.match(data_fields[1].strip()):
                    logger.debug(
                        f"Second field doesn't look like DNA sequence: {data_fields[1]}"
                    )
                    return False
                if not dna_pattern.match(data_fields[2].strip()):
                    logger.debug(
                        f"Third field doesn't look like DNA sequence: {data_fields[2]}"
                    )
                    return False

                # If 4 columns, validate fourth is numeric (product size)
                if len(data_fields) == 4:
                    try:
                        size = int(data_fields[3].strip())
                        if size <= 0:
                            logger.debug(
                                f"Invalid product size (must be positive): {size}"
                            )
                            return False
                    except ValueError:
                        logger.debug(f"Fourth field is not numeric: {data_fields[3]}")
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

        Supports:
        - 3-column format: NAME, FORWARD, REVERSE
        - 4-column format: NAME, FORWARD, REVERSE, SIZE
        - With or without header line

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
                    lines = [line.strip() for line in f if line.strip()]

                if not lines:
                    raise InsufficientDataError(
                        "Empty STS file",
                        user_message=f"STS file is empty: {file_path}",
                    )

                # Detect header and column count
                has_header = self._detect_header(lines[0])
                first_data_line = lines[1] if has_header else lines[0]
                num_columns = len(first_data_line.split("\t"))

                logger.info(
                    f"Parsing STS file: {num_columns} columns, "
                    f"{'with' if has_header else 'without'} header"
                )

                # Determine field names based on column count
                if num_columns == 3:
                    fieldnames = ["NAME", "FORWARD", "REVERSE"]
                elif num_columns == 4:
                    fieldnames = ["NAME", "FORWARD", "REVERSE", "SIZE"]
                else:
                    raise InvalidFormatError(
                        str(file_path),
                        expected_format="STS TSV (3 or 4 columns)",
                        user_message=f"Invalid STS format: expected 3 or 4 columns, got {num_columns}",
                    )

                # Parse data
                processed_rows = 0
                start_row = 1 if has_header else 0

                for row_num_offset, line in enumerate(lines[start_row:]):
                    row_num = (
                        row_num_offset + start_row + 1
                    )  # Human-readable row number

                    try:
                        fields = line.split("\t")

                        if len(fields) != num_columns:
                            raise CorruptedDataError(
                                str(file_path),
                                details=f"Row {row_num} has {len(fields)} fields, expected {num_columns}",
                                user_message=f"Row {row_num} has inconsistent number of columns.",
                            ).add_suggestion(
                                f"Check that all rows have {num_columns} tab-separated fields"
                            )

                        # Create row dictionary
                        row = dict(zip(fieldnames, fields))

                        # Skip completely empty rows
                        if not any(row.values()):
                            logger.debug(f"Skipping empty row {row_num}")
                            continue

                        # Validate required fields
                        required_fields = ["NAME", "FORWARD", "REVERSE"]
                        self._validate_required_fields(row, required_fields, row_num)

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

                        # Get product size if available
                        product_size = None
                        if "SIZE" in row and row["SIZE"]:
                            try:
                                product_size = int(row["SIZE"].strip())
                                if product_size <= 0:
                                    logger.warning(
                                        f"Row {row_num}: Invalid product size {product_size}, ignoring"
                                    )
                                    product_size = None
                            except ValueError:
                                logger.warning(
                                    f"Row {row_num}: Non-numeric product size '{row['SIZE']}', ignoring"
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
                        # Use product size if available, otherwise assume ~300bp
                        estimated_amplicon_length = product_size or 300

                        forward_start = 0
                        forward_stop = len(forward_seq)
                        reverse_start = (
                            forward_stop + estimated_amplicon_length - len(reverse_seq)
                        )
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
                            metadata={
                                "source_row": row_num,
                                "product_size": product_size,
                                # STS format carries no coordinates; positions
                                # here are estimated, not biologically accurate.
                                "synthetic_coordinates": True,
                            },
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
                            metadata={
                                "source_row": row_num,
                                "product_size": product_size,
                                # STS format carries no coordinates; positions
                                # here are estimated, not biologically accurate.
                                "synthetic_coordinates": True,
                            },
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
                                length=estimated_amplicon_length,
                                reference_id=prefix or "unknown",
                            )

                        # Update amplicon length if we have product size
                        if product_size:
                            amplicons[amplicon_name].length = product_size

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
                        user_message=f"No valid primer data found in {file_path}. The file may contain only invalid rows.",
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
