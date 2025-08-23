"""
Core conversion logic for preprimer.
"""

from pathlib import Path
from typing import List, Union, Optional, Dict, Any
import logging

from .interfaces import AmpliconData
from .config import PrePrimerConfig
from .registry import parser_registry, writer_registry
from .exceptions import ParserError, OutputError, ValidationError

logger = logging.getLogger(__name__)


class PrimerConverter:
    """Main converter class for primer format conversion."""
    
    def __init__(self, config: Optional[PrePrimerConfig] = None):
        self.config = config or PrePrimerConfig()
    
    def convert(self,
                input_file: Union[str, Path],
                output_dir: Union[str, Path], 
                input_format: Optional[str] = None,
                output_formats: Optional[List[str]] = None,
                prefix: str = "primers",
                reference_file: Optional[Union[str, Path]] = None,
                **kwargs) -> Dict[str, Path]:
        """
        Convert primer file from one format to others.
        
        Args:
            input_file: Path to input primer file
            output_dir: Directory for output files
            input_format: Input format (auto-detected if None)
            output_formats: List of output formats (from config if None)
            prefix: Prefix for output files
            reference_file: Reference genome file
            **kwargs: Additional arguments
        
        Returns:
            Dictionary mapping format names to output file paths
        """
        input_file = Path(input_file)
        output_dir = Path(output_dir)
        
        # Validate input
        if not input_file.exists():
            raise ParserError(f"Input file not found: {input_file}")
        
        # Auto-detect format if not specified
        if input_format is None:
            input_format = parser_registry.detect_format(input_file)
            if input_format is None:
                available_formats = parser_registry.list_formats()
                raise ParserError(f"Could not detect input format. Available formats: {available_formats}")
        
        logger.info(f"Detected input format: {input_format}")
        
        # Parse input file
        parser = parser_registry.get_parser(input_format)
        amplicons = parser.parse(input_file, prefix)
        
        logger.info(f"Parsed {len(amplicons)} amplicons")
        
        # Validate amplicons
        self._validate_amplicons(amplicons)
        
        # Get reference file if not provided
        if reference_file is None:
            reference_file = parser.get_reference_file(input_file)
            if reference_file:
                logger.info(f"Found associated reference file: {reference_file}")
        
        # Use output formats from config if not specified
        if output_formats is None:
            output_formats = self.config.output_formats
        
        # Convert to output formats
        output_files = {}
        
        for output_format in output_formats:
            try:
                output_file = self._write_format(
                    amplicons, 
                    output_format, 
                    output_dir, 
                    prefix,
                    reference_file,
                    **kwargs
                )
                output_files[output_format] = output_file
                logger.info(f"Successfully created {output_format} format: {output_file}")
                
            except Exception as e:
                logger.error(f"Failed to create {output_format} format: {e}")
                if not kwargs.get('continue_on_error', False):
                    raise
        
        return output_files
    
    def _write_format(self,
                     amplicons: List[AmpliconData],
                     output_format: str,
                     output_dir: Path,
                     prefix: str,
                     reference_file: Optional[Path],
                     **kwargs) -> Path:
        """Write amplicons in specified output format."""
        
        writer = writer_registry.get_writer(output_format)
        
        # Create format-specific output path
        if output_format == "artic":
            # ARTIC needs special directory structure
            output_path = output_dir / "artic" / prefix / "V1" / f"{prefix}.scheme.bed"
        else:
            extension = writer.file_extension
            output_path = output_dir / output_format / f"{prefix}{extension}"
        
        # Check if file exists and force flag
        if output_path.exists() and not self.config.force_overwrite:
            if not kwargs.get('force', False):
                raise OutputError(f"Output file exists: {output_path}. Use --force to overwrite.")
        
        # Write the format
        writer.write(
            amplicons=amplicons,
            output_path=output_path,
            reference_path=reference_file,
            prefix=prefix,
            **kwargs
        )
        
        return output_path
    
    def _validate_amplicons(self, amplicons: List[AmpliconData]) -> None:
        """Validate parsed amplicon data."""
        if not amplicons:
            raise ValidationError("No amplicons found in input file")
        
        issues = []
        
        for amplicon in amplicons:
            if not amplicon.primers:
                issues.append(f"Amplicon {amplicon.amplicon_id} has no primers")
                continue
            
            # Check for forward and reverse primers
            forward_count = len(amplicon.forward_primers)
            reverse_count = len(amplicon.reverse_primers)
            
            if forward_count == 0:
                issues.append(f"Amplicon {amplicon.amplicon_id} has no forward primers")
            if reverse_count == 0:
                issues.append(f"Amplicon {amplicon.amplicon_id} has no reverse primers")
            
            # Validate primer sequences if enabled
            if self.config.validate_sequences:
                for primer in amplicon.primers:
                    if not primer.sequence:
                        issues.append(f"Primer {primer.name} has empty sequence")
                        continue
                    
                    # Check sequence length
                    if len(primer.sequence) < self.config.min_primer_length:
                        issues.append(f"Primer {primer.name} is too short ({len(primer.sequence)} bp)")
                    if len(primer.sequence) > self.config.max_primer_length:
                        issues.append(f"Primer {primer.name} is too long ({len(primer.sequence)} bp)")
                    
                    # Check for valid nucleotides (allow IUPAC codes)
                    valid_chars = set('ATCGRYSWKMBDHVNatcgryswkmbdhvn')
                    invalid_chars = set(primer.sequence) - valid_chars
                    if invalid_chars:
                        issues.append(f"Primer {primer.name} contains invalid characters: {invalid_chars}")
        
        if issues:
            if len(issues) > 10:
                # Show first 10 issues and count
                issue_summary = "\n".join(issues[:10]) + f"\n... and {len(issues) - 10} more issues"
            else:
                issue_summary = "\n".join(issues)
            
            raise ValidationError(f"Validation failed:\n{issue_summary}")
        
        logger.info(f"Validation passed for {len(amplicons)} amplicons")