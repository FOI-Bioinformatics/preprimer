"""
Performance-optimized VarVAMP primer format parser.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..core.exceptions import (
    ParserError, SecurityError, InvalidFormatError, CorruptedDataError,
    InsufficientDataError, ErrorContext, handle_common_exceptions
)
from ..core.interfaces import AmpliconData, PrimerData
from ..core.optimized_parser import OptimizedParser

logger = logging.getLogger(__name__)


class VarVAMPParserOptimized(OptimizedParser):
    """Performance-optimized parser for VarVAMP primer format."""

    @classmethod
    def format_name(cls) -> str:
        return "varvamp_optimized"

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
            with open(file_path, "r", encoding='utf-8') as f:
                # Check header
                header_line = f.readline().strip()
                if not header_line:
                    logger.debug(f"Empty file or no header: {file_path}")
                    return False
                    
                header = header_line.split("\t")
                expected_cols = [
                    "amplicon_name", "amplicon_length", "primer_name", "pool",
                    "start", "stop", "seq", "size", "gc_best", "temp_best",
                    "mean_gc", "mean_temp", "score"
                ]

                # Handle common typos in VarVAMP files (cached)
                cache_key = f"header_validation:{hash(header_line)}"
                if cache_key in self._validation_cache:
                    return self._validation_cache[cache_key]

                header_normalized = []
                for col in header:
                    col_clean = col.strip()
                    # Fix common typo: amlicon -> amplicon
                    if col_clean == "amlicon_name":
                        col_clean = "amplicon_name"
                    header_normalized.append(col_clean)

                # Check if all expected columns are present
                missing_cols = [col for col in expected_cols if col not in header_normalized]
                result = len(missing_cols) == 0
                
                # Cache validation result
                if len(self._validation_cache) < 1000:
                    self._validation_cache[cache_key] = result
                
                if missing_cols:
                    logger.debug(f"Missing VarVAMP columns in {file_path}: {missing_cols}")
                
                return result

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
        Performance-optimized VarVAMP file parsing.
        
        Key optimizations:
        1. Batch processing for numeric validation
        2. Cached string sanitization
        3. Efficient primer grouping
        4. Reduced object creation overhead
        """
        primer_data_list = []
        
        with ErrorContext(f"parsing VarVAMP file {file_path}"):
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter="\t")

                    # Validate fieldnames once
                    if not reader.fieldnames:
                        raise InvalidFormatError(
                            str(file_path),
                            expected_format="VarVAMP TSV",
                            user_message="The file appears to be empty or missing headers."
                        ).add_suggestion("Check that the file contains VarVAMP header columns")

                    # Fix header names if needed (common VarVAMP typo)
                    if "amlicon_name" in reader.fieldnames:
                        logger.info("Fixing common VarVAMP typo: 'amlicon_name' → 'amplicon_name'")
                        new_fieldnames = []
                        for field in reader.fieldnames:
                            if field == "amlicon_name":
                                new_fieldnames.append("amplicon_name")
                            else:
                                new_fieldnames.append(field)
                        reader.fieldnames = new_fieldnames

                    # Batch read all rows first
                    rows = list(reader)
                    
                    # Filter empty rows
                    non_empty_rows = []
                    for row_num, row in enumerate(rows, start=2):
                        if any(row.values()):
                            non_empty_rows.append((row_num, row))
                    
                    logger.info(f"Processing {len(non_empty_rows)} non-empty rows")
                    
                    # Batch validate numeric fields
                    numeric_fields = ["start", "stop", "pool", "amplicon_length", "gc_best", "temp_best", "score", "mean_gc", "mean_temp"]
                    row_data = [row for _, row in non_empty_rows]
                    numeric_results = self._validate_numeric_batch(row_data, numeric_fields)
                    
                    # Process each row with optimizations
                    for idx, (row_num, row) in enumerate(non_empty_rows):
                        try:
                            # Validate required fields (minimal check)
                            required_fields = ["amplicon_name", "primer_name", "seq", "start", "stop"]
                            missing = [f for f in required_fields if not row.get(f)]
                            if missing:
                                logger.warning(f"Missing required fields {missing} in row {row_num}")
                                continue
                            
                            # Optimized string sanitization with caching
                            amplicon_name = self._sanitize_string_field_optimized(
                                row["amplicon_name"], "amplicon_name", row_num, 100
                            )
                            primer_name = self._sanitize_string_field_optimized(
                                row["primer_name"], "primer_name", row_num, 100
                            )
                            sequence = self._sanitize_string_field_optimized(
                                row["seq"], "sequence", row_num, 1000
                            )

                            # Cached primer direction determination
                            try:
                                direction, strand = self._get_primer_direction_cached(primer_name)
                            except ValueError:
                                logger.warning(f"Invalid primer name format '{primer_name}' at row {row_num}")
                                continue

                            # Get pre-validated numeric values
                            numeric_data = numeric_results[idx]
                            start_pos = numeric_data.get('start')
                            stop_pos = numeric_data.get('stop')
                            
                            if start_pos is None or stop_pos is None:
                                logger.warning(f"Invalid coordinates in row {row_num}")
                                continue
                            
                            # Quick coordinate validation
                            if start_pos >= stop_pos:
                                logger.warning(f"Invalid coordinates: start >= stop in row {row_num}")
                                continue

                            # Collect primer data for batch creation
                            primer_data = {
                                'name': primer_name,
                                'sequence': sequence,
                                'start': start_pos,
                                'stop': stop_pos,
                                'strand': strand,
                                'direction': direction,
                                'pool': numeric_data.get('pool', 1),
                                'amplicon_id': amplicon_name,
                                'reference_id': prefix or "unknown",
                                'gc_content': numeric_data.get('gc_best'),
                                'tm': numeric_data.get('temp_best'),
                                'score': numeric_data.get('score')
                            }
                            primer_data_list.append(primer_data)
                            
                        except Exception as e:
                            logger.warning(f"Error processing row {row_num}: {e}")
                            continue

                    if not primer_data_list:
                        raise InsufficientDataError(
                            str(file_path),
                            details="No valid primer data found after parsing",
                            user_message="The file contains no valid primer data."
                        ).add_suggestion("Check that the file contains properly formatted VarVAMP data")

                    logger.info(f"Successfully processed {len(primer_data_list)} primers")
                    
                    # Batch create primers
                    primers = self._create_primer_batch(primer_data_list)
                    
                    # Efficiently group into amplicons
                    amplicons = self._group_primers_by_amplicon(primers)
                    
                    logger.info(f"Created {len(amplicons)} amplicons from {len(primers)} primers")
                    
                    return amplicons

            except FileNotFoundError:
                raise ParserError(f"VarVAMP file not found: {file_path}")
            except PermissionError:
                raise SecurityError(f"Permission denied reading file: {file_path}")
            except Exception as e:
                if isinstance(e, (ParserError, SecurityError, InvalidFormatError)):
                    raise
                raise ParserError(f"Unexpected error parsing VarVAMP file {file_path}: {e}")