"""
VarVAMP primer format parser.
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


class VarVAMPParser(StandardizedParser):
    """Parser for VarVAMP primer format."""

    @classmethod
    def format_name(cls) -> str:
        return "varvamp"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".tsv", ".txt"]

    @handle_common_exceptions("VarVAMP file validation")
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in VarVAMP format."""
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

                header = header_line.split("\t")
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
                missing_cols = [
                    col for col in expected_cols if col not in header_normalized
                ]
                if missing_cols:
                    logger.debug(
                        f"Missing VarVAMP columns in {file_path}: {missing_cols}"
                    )
                    return False

                return True

        except UnicodeDecodeError as e:
            logger.debug(f"File encoding issue for {file_path}: {e}")
            return False
        except Exception as e:
            logger.debug(f"VarVAMP validation failed for {file_path}: {e}")
            return False

    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        """
        Parse VarVAMP primer file content with comprehensive error handling.

        Args:
            file_path: Validated path to VarVAMP TSV file
            prefix: Validated prefix for primer naming

        Returns:
            Dictionary of AmpliconData objects keyed by amplicon_id

        Raises:
            ParserError: If file format is invalid
            CorruptedDataError: If data appears corrupted
            InsufficientDataError: If insufficient data found
        """
        amplicons = {}

        with ErrorContext(f"parsing VarVAMP file {file_path}"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f, delimiter="\t")

                    # Validate that we have field names
                    if not reader.fieldnames:
                        raise InvalidFormatError(
                            str(file_path),
                            expected_format="VarVAMP TSV",
                            user_message="The file appears to be empty or missing headers.",
                        ).add_suggestion(
                            "Check that the file contains VarVAMP header columns"
                        )

                    # Fix header names if needed (common VarVAMP typo)
                    if "amlicon_name" in reader.fieldnames:
                        logger.info(
                            "Fixing common VarVAMP typo: 'amlicon_name' → 'amplicon_name'"
                        )
                        new_fieldnames = []
                        for field in reader.fieldnames:
                            if field == "amlicon_name":
                                new_fieldnames.append("amplicon_name")
                            else:
                                new_fieldnames.append(field)
                        reader.fieldnames = new_fieldnames

                    processed_rows = 0
                    for row_num, row in enumerate(
                        reader, start=2
                    ):  # Start at 2 for header
                        try:
                            # Skip completely empty rows
                            if not any(row.values()):
                                logger.debug(f"Skipping empty row {row_num}")
                                continue

                            # Validate required fields using standardized method
                            required_fields = [
                                "amplicon_name",
                                "primer_name",
                                "seq",
                                "start",
                                "stop",
                            ]
                            self._validate_required_fields(
                                row, required_fields, row_num
                            )

                            # Sanitize input data using standardized methods
                            amplicon_name = self._sanitize_string_field(
                                row["amplicon_name"], "amplicon_name", row_num, 100
                            )
                            primer_name = self._sanitize_string_field(
                                row["primer_name"], "primer_name", row_num, 100
                            )
                            sequence = self._sanitize_string_field(
                                row["seq"], "sequence", row_num, 1000
                            )

                            # Determine primer direction with better error handling
                            if primer_name.startswith("FW"):
                                direction = "forward"
                                strand = "+"
                            elif primer_name.startswith("RW"):
                                direction = "reverse"
                                strand = "-"
                            else:
                                raise CorruptedDataError(
                                    str(file_path),
                                    details=f"Invalid primer name format '{primer_name}' at row {row_num}",
                                    user_message=f"Invalid primer name '{primer_name}' in row {row_num}. VarVAMP primers should start with 'FW' or 'RW'.",
                                ).add_suggestion(
                                    "Check that primer names follow VarVAMP conventions"
                                )

                            # Validate numeric fields using standardized methods
                            start_pos = self._validate_numeric_field(
                                row["start"], "start", row_num, int, min_value=0
                            )
                            stop_pos = self._validate_numeric_field(
                                row["stop"], "stop", row_num, int, min_value=0
                            )
                            pool_num = self._validate_numeric_field(
                                row.get("pool", "1"), "pool", row_num, int, min_value=0
                            )

                            # Additional coordinate validation
                            if start_pos >= stop_pos:
                                raise CorruptedDataError(
                                    str(file_path),
                                    details=f"Invalid coordinates: start ({start_pos}) >= stop ({stop_pos}) at row {row_num}",
                                    user_message=f"Invalid primer coordinates in row {row_num}: start position must be less than stop position.",
                                )

                            # Validate primer data using standardized method
                            self._validate_primer_data(
                                primer_name, sequence, start_pos, stop_pos, row_num
                            )

                            # Safely convert optional float fields
                            gc_content = self._safe_float_convert(
                                row.get("gc_best"), row_num, "gc_best"
                            )
                            tm = self._safe_float_convert(
                                row.get("temp_best"), row_num, "temp_best"
                            )
                            score = self._safe_float_convert(
                                row.get("score"), row_num, "score"
                            )
                            mean_gc = self._safe_float_convert(
                                row.get("mean_gc"), row_num, "mean_gc"
                            )
                            mean_temp = self._safe_float_convert(
                                row.get("mean_temp"), row_num, "mean_temp"
                            )
                            amplicon_length = self._safe_int_convert(
                                row.get("amplicon_length"), row_num, "amplicon_length"
                            )

                            # Create PrimerData object using standardized method
                            primer = self._create_primer_data(
                                name=primer_name,
                                sequence=sequence,
                                start=start_pos,
                                stop=stop_pos,
                                strand=strand,
                                direction=direction,
                                pool=pool_num,
                                amplicon_id=amplicon_name,
                                reference_id=prefix or "ambiguous_consensus",
                                gc_content=gc_content,
                                tm=tm,
                                score=score,
                                metadata={
                                    "mean_gc": mean_gc,
                                    "mean_temp": mean_temp,
                                    "amplicon_length": amplicon_length,
                                    "source_row": row_num,
                                },
                            )

                            # Group primers by amplicon
                            if amplicon_name not in amplicons:
                                amplicons[amplicon_name] = AmpliconData(
                                    amplicon_id=amplicon_name,
                                    primers=[],
                                    length=amplicon_length,
                                    reference_id=prefix or "ambiguous_consensus",
                                )

                            amplicons[amplicon_name].primers.append(primer)
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
                            "No valid primer data found in VarVAMP file",
                            user_message=f"No valid primer data found in {file_path}. The file may be empty or contain only invalid rows.",
                        ).add_suggestion(
                            "Verify that the file contains properly formatted VarVAMP data"
                        )

            except UnicodeDecodeError as e:
                raise InvalidFormatError(
                    str(file_path),
                    expected_format="UTF-8 encoded VarVAMP TSV",
                    user_message=f"File encoding error: {file_path}. The file may not be UTF-8 encoded.",
                ).add_suggestion("Try re-saving the file with UTF-8 encoding") from e

            except FileNotFoundError as e:
                raise ParserError(
                    f"VarVAMP file not found: {file_path}",
                    file_path=str(file_path),
                    user_message=f"File not found: {file_path}",
                ) from e

            except PermissionError as e:
                raise ParserError(
                    f"Permission denied reading VarVAMP file: {file_path}",
                    file_path=str(file_path),
                    user_message=f"Permission denied: Cannot read {file_path}",
                ).add_suggestion("Check file permissions and try again") from e

        return amplicons

    def _safe_float_convert(
        self, value: Optional[str], row_num: int, field_name: str
    ) -> Optional[float]:
        """Safely convert string to float with error handling."""
        if not value:
            return None
        try:
            return float(value)
        except ValueError as e:
            logger.warning(f"Invalid {field_name} in row {row_num}: {e}")
            return None

    def _safe_int_convert(
        self, value: Optional[str], row_num: int, field_name: str
    ) -> Optional[int]:
        """Safely convert string to int with error handling."""
        if not value:
            return None
        try:
            return int(value)
        except ValueError as e:
            logger.warning(f"Invalid {field_name} in row {row_num}: {e}")
            return None

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        Get associated reference file (ambiguous_consensus.fasta) with security validation.

        Args:
            file_path: Path to the VarVAMP file

        Returns:
            Path to reference file if it exists, None otherwise
        """
        try:
            validated_path = self.path_validator.sanitize_path(file_path)
            ref_file = validated_path.parent / "ambiguous_consensus.fasta"

            # Validate the reference file path as well
            if ref_file.exists():
                validated_ref = self.path_validator.sanitize_path(ref_file)
                return validated_ref

            return None

        except SecurityError as e:
            logger.warning(
                f"Security error accessing reference file for {file_path}: {e}"
            )
            return None
        except Exception as e:
            logger.warning(f"Error finding reference file for {file_path}: {e}")
            return None
