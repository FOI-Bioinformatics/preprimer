"""
Olivar primer format parser.

Official Olivar tool: https://github.com/treangenlab/Olivar
Uses SADDLE algorithm for variant-aware primer design with degenerate primers.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.exceptions import (
    ParserError, SecurityError, InvalidFormatError, CorruptedDataError,
    InsufficientDataError, ErrorContext, handle_common_exceptions
)
from ..core.interfaces import AmpliconData, PrimerData
from ..core.standardized_parser import StandardizedParser

logger = logging.getLogger(__name__)


class OlivarParser(StandardizedParser):
    """
    Parser for official Olivar primer design format.
    
    Official specification from https://github.com/treangenlab/Olivar:
    - Required columns: amplicon_id, fP (forward primer), rP (reverse primer), pool
    - Optional columns: chrom, start, end (1-based coordinates)
    - Supports IUPAC degenerate nucleotide codes
    - Row-based format: one amplicon per row with both primers
    """

    @classmethod
    def format_name(cls) -> str:
        return "olivar"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".csv", "olivar-design.csv"]

    @handle_common_exceptions("Olivar file validation")
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in official Olivar format."""
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        # Official Olivar output file naming pattern
        if "olivar-design" in file_path.name.lower():
            return True

        try:
            with open(file_path, "r", encoding='utf-8') as f:
                # Check header for official Olivar columns
                header_line = f.readline().strip()
                if not header_line:
                    logger.debug(f"Empty file or no header: {file_path}")
                    return False
                    
                header = [col.strip().strip('"') for col in header_line.split(",")]
                header_lower = [col.lower() for col in header]

                # Official Olivar required columns per GitHub specification
                required_columns = ["amplicon_id", "fP", "rP", "pool"]
                optional_columns = ["chrom", "start", "end"]

                # Check for required columns
                required_matches = sum(1 for col in required_columns if col.lower() in header_lower)
                
                # Must have all 4 required columns for official Olivar format
                if required_matches >= 4:
                    logger.debug(f"Valid Olivar format detected: {required_matches}/4 required columns found")
                    return True
                
                # Alternative: Check if we have the essential forward/reverse primer columns
                has_forward = any(col in header_lower for col in ['fp', 'forward_primer', 'fwd_primer'])
                has_reverse = any(col in header_lower for col in ['rp', 'reverse_primer', 'rev_primer'])
                has_amplicon = any(col in header_lower for col in ['amplicon_id', 'amplicon', 'region_id'])
                
                return has_forward and has_reverse and has_amplicon

        except UnicodeDecodeError as e:
            logger.debug(f"File encoding issue for {file_path}: {e}")
            return False
        except Exception as e:
            logger.debug(f"Olivar validation failed for {file_path}: {e}")
            return False

    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        """
        Parse Olivar primer file content with comprehensive error handling.
        
        Official Olivar format: row-based CSV with amplicon_id, fP, rP, pool columns.
        Each row contains both forward and reverse primers for one amplicon.
        """
        amplicons = {}
        
        with ErrorContext(f"parsing Olivar file {file_path}"):
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    # Validate that we have field names
                    if not reader.fieldnames:
                        raise InvalidFormatError(
                            str(file_path),
                            expected_format="Olivar CSV",
                            user_message="The file appears to be empty or missing headers."
                        ).add_suggestion("Check that the file contains Olivar header columns")

                    processed_rows = 0
                    for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                        try:
                            # Skip completely empty rows
                            if not any(row.values()):
                                logger.debug(f"Skipping empty row {row_num}")
                                continue
                            
                            # Validate required fields using standardized method
                            required_fields = ["amplicon_id", "fP", "rP", "pool"]
                            self._validate_required_fields(row, required_fields, row_num)
                            
                            # Sanitize input data using standardized methods
                            amplicon_id = self._sanitize_string_field(row["amplicon_id"], "amplicon_id", row_num, 100)
                            fwd_seq = self._sanitize_string_field(row["fP"], "forward_primer", row_num, 100)
                            rev_seq = self._sanitize_string_field(row["rP"], "reverse_primer", row_num, 100)
                            
                            # Validate primer sequences (Olivar supports IUPAC degenerate codes)
                            self.input_validator.validate_primer_sequence(fwd_seq)
                            self.input_validator.validate_primer_sequence(rev_seq)
                            
                            # Pool number validation
                            pool_num = self._validate_numeric_field(row["pool"], "pool", row_num, int, min_value=1)
                            
                            # Optional coordinate fields (1-based in Olivar)
                            reference_id = row.get("chrom", prefix or "olivar_target")
                            start_pos = None
                            end_pos = None
                            
                            if row.get("start") and row.get("end"):
                                start_pos = self._validate_numeric_field(row["start"], "start", row_num, int, min_value=1)
                                end_pos = self._validate_numeric_field(row["end"], "end", row_num, int, min_value=1)
                                
                                # Note: Don't validate start < end here for Olivar format
                                # Olivar files may contain coordinates that appear to wrap,
                                # but this will be validated later with topology information
                            else:
                                # Estimate positions from sequence length (common when no coordinates provided)
                                start_pos = 1  # Default start
                                end_pos = len(fwd_seq) + len(rev_seq) + 100  # Estimate with gap
                            
                            # Create forward primer using standardized method
                            fwd_primer = self._create_primer_data(
                                name=f"{amplicon_id}_F",
                                sequence=fwd_seq,
                                start=start_pos,
                                stop=start_pos + len(fwd_seq),
                                strand="+",
                                direction="forward",
                                pool=pool_num,
                                amplicon_id=amplicon_id,
                                reference_id=reference_id,
                                metadata={
                                    "olivar_format": True,
                                    "degenerate_bases": any(base in fwd_seq for base in "RYSWKMBDHVN"),
                                    "source_row": row_num,
                                    "original_data": {k: v for k, v in row.items() if v}
                                }
                            )
                            
                            # Create reverse primer using standardized method  
                            rev_primer = self._create_primer_data(
                                name=f"{amplicon_id}_R",
                                sequence=rev_seq,
                                start=end_pos - len(rev_seq),
                                stop=end_pos,
                                strand="-",
                                direction="reverse",
                                pool=pool_num,
                                amplicon_id=amplicon_id,
                                reference_id=reference_id,
                                metadata={
                                    "olivar_format": True,
                                    "degenerate_bases": any(base in rev_seq for base in "RYSWKMBDHVN"),
                                    "source_row": row_num,
                                    "original_data": {k: v for k, v in row.items() if v}
                                }
                            )

                            # Group primers by amplicon
                            if amplicon_id not in amplicons:
                                amplicons[amplicon_id] = AmpliconData(
                                    amplicon_id=amplicon_id,
                                    primers=[],
                                    length=end_pos - start_pos if start_pos and end_pos else None,
                                    reference_id=reference_id,
                                )

                            amplicons[amplicon_id].primers.extend([fwd_primer, rev_primer])
                            processed_rows += 1
                            
                        except (ParserError, SecurityError, InvalidFormatError, CorruptedDataError):
                            # Re-raise our specific errors
                            raise
                        except Exception as e:
                            # Wrap unexpected errors
                            raise CorruptedDataError(
                                str(file_path),
                                details=f"Unexpected error processing row {row_num}: {e}",
                                user_message=f"Error processing data in row {row_num}. The row may be malformed."
                            ).add_suggestion("Check the data format in the problematic row") from e

                    # Validate that we processed some data
                    if processed_rows == 0:
                        raise InsufficientDataError(
                            "No valid primer data found in Olivar file",
                            user_message=f"No valid primer data found in {file_path}. The file may be empty or contain only invalid rows."
                        ).add_suggestion("Verify that the file contains properly formatted Olivar data")

            except UnicodeDecodeError as e:
                raise InvalidFormatError(
                    str(file_path),
                    expected_format="UTF-8 encoded Olivar CSV",
                    user_message=f"File encoding error: {file_path}. The file may not be UTF-8 encoded."
                ).add_suggestion("Try re-saving the file with UTF-8 encoding") from e
                
            except FileNotFoundError as e:
                raise ParserError(
                    f"Olivar file not found: {file_path}",
                    file_path=str(file_path),
                    user_message=f"File not found: {file_path}"
                ) from e
            
            except PermissionError as e:
                raise ParserError(
                    f"Permission denied reading Olivar file: {file_path}",
                    file_path=str(file_path),
                    user_message=f"Permission denied: Cannot read {file_path}"
                ).add_suggestion("Check file permissions and try again") from e

        return amplicons

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        Get associated reference file with security validation.
        
        Olivar typically generates reference files alongside the design CSV.
        """
        try:
            validated_path = self.path_validator.sanitize_path(file_path)
            base_name = validated_path.stem.replace("-design", "").replace("olivar-", "")

            # Try common Olivar reference file patterns
            possible_refs = [
                validated_path.parent / f"{base_name}_ref.fasta",
                validated_path.parent / f"{base_name}.reference.fasta", 
                validated_path.parent / "reference.fasta",
            ]

            for ref_file in possible_refs:
                if ref_file.exists():
                    # Validate the reference file path as well
                    validated_ref = self.path_validator.sanitize_path(ref_file)
                    return validated_ref
            
            return None
            
        except SecurityError as e:
            logger.warning(f"Security error accessing reference file for {file_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error finding reference file for {file_path}: {e}")
            return None
