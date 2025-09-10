"""
Standardized parser interface for consistent validation, error handling, and logging.
"""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .exceptions import ParserError, SecurityError, InvalidFormatError
from .interfaces import AmpliconData, PrimerData, PrimerParser
from .security import InputValidator, PathValidator

logger = logging.getLogger(__name__)


class StandardizedParser(PrimerParser):
    """
    Standardized parser base class providing common validation patterns,
    standardized error messages, and consistent logging format.
    """
    
    def __init__(self):
        """Initialize standardized parser with security validators."""
        self.path_validator = PathValidator()
        self.input_validator = InputValidator()
    
    def parse(
        self, file_path: Union[str, Path], prefix: str = ""
    ) -> List[AmpliconData]:
        """
        Parse primer file with standardized validation and error handling.
        
        Args:
            file_path: Path to primer file
            prefix: Optional prefix for primer naming
            
        Returns:
            List of AmpliconData objects
            
        Raises:
            SecurityError: If file path or content is unsafe
            ParserError: If file format is invalid
        """
        # Step 1: Validate and sanitize inputs
        validated_path = self._validate_inputs(file_path, prefix)
        
        # Step 2: Validate file format
        if not self.validate_file(validated_path):
            raise InvalidFormatError(
                str(validated_path), 
                expected_format=self.__class__.format_name(),
                user_message=f"File {validated_path} is not in valid {self.__class__.format_name()} format."
            )
        
        # Step 3: Parse file with standardized error handling
        logger.info(f"Parsing {self.__class__.format_name()} file: {validated_path}")
        
        try:
            amplicons = self._parse_file_content(validated_path, prefix)
            
            # Step 4: Post-process results
            amplicon_list = self._finalize_amplicons(amplicons)
            
            # Step 5: Log results
            self._log_parse_results(amplicon_list)
            
            return amplicon_list
            
        except (ParserError, SecurityError):
            raise  # Re-raise parser and security errors
        except Exception as e:
            raise ParserError(
                f"Failed to parse {self.__class__.format_name()} file {validated_path}: {e}"
            ) from e
    
    def _validate_inputs(self, file_path: Union[str, Path], prefix: str) -> Path:
        """
        Validate and sanitize input parameters.
        
        Args:
            file_path: Path to primer file
            prefix: Optional prefix for primer naming
            
        Returns:
            Validated and sanitized file path
            
        Raises:
            SecurityError: If inputs are unsafe
        """
        # Validate and sanitize file path
        validated_path = self.path_validator.sanitize_path(file_path)
        
        # Validate prefix if provided
        if prefix:
            self.input_validator.validate_amplicon_name(prefix)
        
        return validated_path
    
    def _validate_required_fields(
        self, row: Dict[str, str], required_fields: List[str], row_num: int
    ) -> None:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            row: Data row dictionary
            required_fields: List of required field names
            row_num: Row number for error reporting
            
        Raises:
            ParserError: If required fields are missing or empty
        """
        for field in required_fields:
            if field not in row or not row[field]:
                raise ParserError(
                    f"Missing required field '{field}' in row {row_num} "
                    f"of {self.__class__.format_name()} file"
                )
    
    def _sanitize_string_field(
        self, value: str, field_name: str, row_num: int, max_length: int = 1000
    ) -> str:
        """
        Sanitize string field with validation.
        
        Args:
            value: String value to sanitize
            field_name: Name of field for error reporting
            row_num: Row number for error reporting
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string value
            
        Raises:
            SecurityError: If security validation fails
            ParserError: If other sanitization fails
        """
        try:
            return self.input_validator.sanitize_string(value, max_length=max_length)
        except SecurityError:
            raise  # Re-raise SecurityError unchanged for security tests
        except Exception as e:
            raise ParserError(
                f"Invalid {field_name} in row {row_num}: {e}"
            ) from e
    
    def _validate_numeric_field(
        self, 
        value: str, 
        field_name: str, 
        row_num: int,
        field_type: type = int,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Union[int, float]:
        """
        Validate and convert numeric field.
        
        Args:
            value: String value to convert
            field_name: Name of field for error reporting
            row_num: Row number for error reporting
            field_type: Target type (int or float)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Converted numeric value
            
        Raises:
            ParserError: If conversion or validation fails
        """
        try:
            numeric_value = field_type(value)
            
            if min_value is not None and numeric_value < min_value:
                raise ValueError(f"{field_name} cannot be less than {min_value}")
            
            if max_value is not None and numeric_value > max_value:
                raise ValueError(f"{field_name} cannot be greater than {max_value}")
            
            return numeric_value
            
        except ValueError as e:
            raise ParserError(
                f"Invalid {field_name} in row {row_num}: {e}"
            ) from e
    
    def _validate_primer_data(
        self, primer_name: str, sequence: str, start: int, stop: int, row_num: int
    ) -> None:
        """
        Validate primer data with comprehensive checks.
        
        Args:
            primer_name: Primer name
            sequence: Primer sequence
            start: Start position
            stop: Stop position
            row_num: Row number for error reporting
            
        Raises:
            ParserError: If validation fails
        """
        try:
            # Validate primer sequence
            self.input_validator.validate_primer_sequence(sequence)
            
            # Validate coordinates
            if start < 0 or stop < 0:
                raise ValueError("Negative coordinates not allowed")
            
            if start >= stop:
                raise ValueError("Start position must be less than stop position")
            
            # Validate sequence length matches coordinates
            expected_length = stop - start
            if len(sequence) != expected_length:
                logger.warning(
                    f"Sequence length ({len(sequence)}) does not match "
                    f"coordinates ({expected_length}) for primer {primer_name} "
                    f"in row {row_num}"
                )
                
        except Exception as e:
            raise ParserError(
                f"Invalid primer data for {primer_name} in row {row_num}: {e}"
            ) from e
    
    def _create_primer_data(
        self,
        name: str,
        sequence: str,
        start: int,
        stop: int,
        strand: str,
        direction: str,
        pool: int,
        amplicon_id: str,
        reference_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> PrimerData:
        """
        Create PrimerData object with standardized metadata.
        
        Args:
            name: Primer name
            sequence: Primer sequence
            start: Start position
            stop: Stop position
            strand: Strand (+ or -)
            direction: Direction (forward or reverse)
            pool: Pool number
            amplicon_id: Amplicon identifier
            reference_id: Reference identifier
            metadata: Additional metadata
            **kwargs: Additional PrimerData fields
            
        Returns:
            PrimerData object
        """
        if metadata is None:
            metadata = {}
        
        # Add standardized metadata
        metadata.update({
            "parser": self.__class__.format_name(),
            "validated": True,
        })
        
        return PrimerData(
            name=name,
            sequence=sequence,
            start=start,
            stop=stop,
            strand=strand,
            direction=direction,
            pool=pool,
            amplicon_id=amplicon_id,
            reference_id=reference_id,
            metadata=metadata,
            **kwargs
        )
    
    def _finalize_amplicons(self, amplicons: Dict[str, AmpliconData]) -> List[AmpliconData]:
        """
        Finalize amplicon data with length calculations and validation.
        
        Args:
            amplicons: Dictionary of amplicon data
            
        Returns:
            List of finalized AmpliconData objects
            
        Raises:
            ParserError: If amplicon data is invalid
        """
        if not amplicons:
            raise ParserError(f"No valid amplicons found in {self.__class__.format_name()} file")
        
        # Calculate amplicon lengths and validate
        for amplicon in amplicons.values():
            if amplicon.primers:
                starts = [p.start for p in amplicon.primers]
                stops = [p.stop for p in amplicon.primers]
                amplicon.length = max(stops) - min(starts)
                
                # Validate amplicon has both forward and reverse primers
                directions = {p.direction for p in amplicon.primers}
                if len(directions) < 2:
                    logger.warning(
                        f"Amplicon {amplicon.amplicon_id} only has "
                        f"{', '.join(directions)} primers"
                    )
        
        return list(amplicons.values())
    
    def _log_parse_results(self, amplicon_list: List[AmpliconData]) -> None:
        """
        Log parse results with standardized format.
        
        Args:
            amplicon_list: List of parsed amplicons
        """
        total_primers = sum(len(a.primers) for a in amplicon_list)
        logger.info(
            f"Successfully parsed {len(amplicon_list)} amplicons with "
            f"{total_primers} primers from {self.__class__.format_name()} file"
        )
        
        # Log additional statistics
        if amplicon_list:
            pools = set()
            for amplicon in amplicon_list:
                pools.update(p.pool for p in amplicon.primers if p.pool is not None)
            
            if pools:
                logger.info(f"Found {len(pools)} primer pools: {sorted(pools)}")
    
    @abstractmethod
    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        """
        Parse the actual file content - must be implemented by subclasses.
        
        Args:
            file_path: Validated file path
            prefix: Validated prefix
            
        Returns:
            Dictionary of amplicon data keyed by amplicon_id
            
        Raises:
            ParserError: If parsing fails
        """
        pass