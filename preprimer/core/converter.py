"""
Core conversion logic for preprimer.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .enhanced_config import EnhancedConfig
from .exceptions import (
    ErrorContext,
    FileNotFoundError,
    InvalidFormatError,
    OutputError,
    ParserError,
    ValidationError,
)
from .interfaces import AmpliconData
from .registry import parser_registry, writer_registry

logger = logging.getLogger(__name__)


class PrimerConverter:
    """Main converter class for primer format conversion."""

    # Output formats that represent at most one forward + one reverse primer
    # per amplicon, so alternate primers are dropped on write.
    LOSSY_FORMATS = {"olivar", "sts"}

    def __init__(self, config: Optional[EnhancedConfig] = None):
        self.config = config or EnhancedConfig()
        # Populated by convert(); machine-readable summary of the last run.
        self.last_summary: Dict[str, Any] = {}

    def convert(
        self,
        input_file: Union[str, Path],
        output_dir: Union[str, Path],
        input_format: Optional[str] = None,
        output_formats: Optional[List[str]] = None,
        prefix: str = "primers",
        reference_file: Optional[Union[str, Path]] = None,
        lenient: bool = False,
        strict: bool = False,
        **kwargs,
    ) -> Dict[str, Path]:
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

        with ErrorContext("primer format conversion"):
            # Validate input file exists
            if not input_file.exists():
                raise FileNotFoundError(str(input_file))

            # Auto-detect format if not specified
            if input_format is None:
                input_format = parser_registry.detect_format(input_file)
                if input_format is None:
                    available_formats = parser_registry.list_formats()
                    error = InvalidFormatError(
                        str(input_file),
                        user_message=f"Could not detect the format of {input_file}. "
                        f"Available formats: {', '.join(available_formats)}",
                    )
                    error.add_suggestion("Try specifying the input format explicitly")
                    error.add_suggestion("Check that the file is in a supported format")
                    raise error

            logger.info(f"Detected input format: {input_format}")

            # Parse input file with error handling
            try:
                parser = parser_registry.get_parser(input_format)
                amplicons = parser.parse(input_file, prefix)
            except ParserError:
                # Re-raise parser errors as-is (they already have good context)
                raise
            except Exception as e:
                # Wrap unexpected parsing errors
                raise ParserError(
                    f"Unexpected error parsing {input_format} file: {e}",
                    file_path=str(input_file),
                    user_message=f"Failed to parse {input_file} as {input_format} format.",
                ).add_suggestion(
                    f"Verify that {input_file} is a valid {input_format} file"
                ) from e

            logger.info(f"Parsed {len(amplicons)} amplicons")

            # Collect warnings for the run summary (non-fatal data-quality notices).
            warnings: List[str] = []

            # Validate amplicons. In lenient mode, validation issues become
            # warnings instead of aborting the conversion.
            try:
                validation_warnings = self._validate_amplicons(
                    amplicons, lenient=lenient
                )
                warnings.extend(validation_warnings)
            except ValidationError:
                # Re-raise validation errors as-is
                raise
            except Exception as e:
                raise ValidationError(
                    f"Unexpected error during amplicon validation: {e}",
                    user_message="Error validating parsed amplicon data.",
                ).add_suggestion(
                    "Check that the input data is complete and valid"
                ) from e

            # Detect fabricated (synthetic) coordinates flagged by parsers.
            synthetic_primers = sum(
                1
                for amp in amplicons
                for p in amp.primers
                if p.metadata.get("synthetic_coordinates")
            )
            if synthetic_primers:
                msg = (
                    f"{synthetic_primers} primer(s) have synthetic coordinates "
                    f"(the source format lacked positions; coordinates were "
                    f"estimated and are not biologically accurate)"
                )
                if strict:
                    raise ValidationError(
                        msg,
                        user_message=(
                            "Conversion aborted in --strict mode: the input "
                            "lacks real primer coordinates."
                        ),
                    ).add_suggestion(
                        "Provide a coordinate-bearing input format, or drop "
                        "--strict to allow estimated coordinates"
                    )
                warnings.append(msg)
                logger.warning(msg)

        # Get reference file if not provided
        if reference_file is None:
            reference_file = parser.get_reference_file(input_file)
            if reference_file:
                logger.info(f"Found associated reference file: {reference_file}")

        # Use output formats from config if not specified
        if output_formats is None:
            output_formats = self.config.output.formats

        # Warn when the source carries no primer sequences (e.g. a 6-column
        # primer.bed) but the requested output relies on sequences.
        seqless_primers = sum(
            1 for amp in amplicons for p in amp.primers if not p.sequence
        )
        SEQUENCE_BEARING = {"fasta", "varvamp", "olivar", "sts"}
        if seqless_primers and SEQUENCE_BEARING.intersection(
            f.lower() for f in output_formats
        ):
            msg = (
                f"{seqless_primers} primer(s) have no sequence (the input is a "
                f"6-column primer.bed); sequence-bearing output formats will have "
                f"empty primer sequences"
            )
            warnings.append(msg)
            logger.warning(msg)

        # Convert to output formats
        output_files = {}

        for output_format in output_formats:
            # Warn when a lossy format will drop alternate primers.
            if output_format.lower() in self.LOSSY_FORMATS:
                dropped = self._count_dropped_primers(amplicons)
                if dropped:
                    msg = (
                        f"{output_format} format keeps one forward/reverse primer "
                        f"per amplicon; {dropped} alternate primer(s) will be dropped"
                    )
                    warnings.append(msg)
                    logger.warning(msg)

            try:
                output_file = self._write_format(
                    amplicons,
                    output_format,
                    output_dir,
                    prefix,
                    Path(reference_file) if reference_file else None,
                    **kwargs,
                )
                if output_file:
                    output_files[output_format] = output_file
                logger.info(
                    f"Successfully created {output_format} format: {output_file}"
                )

            except Exception as e:
                logger.error(f"Failed to create {output_format} format: {e}")
                if not kwargs.get("continue_on_error", False):
                    raise

        # Build a machine-readable summary of the run.
        self.last_summary = {
            "input_file": str(input_file),
            "input_format": input_format,
            "amplicons": len(amplicons),
            "primers": sum(len(a.primers) for a in amplicons),
            "synthetic_coordinate_primers": synthetic_primers,
            "output_files": {fmt: str(path) for fmt, path in output_files.items()},
            "warnings": warnings,
        }

        return output_files

    @staticmethod
    def _count_dropped_primers(amplicons: List[AmpliconData]) -> int:
        """Count alternate primers that a single-pair format would discard."""
        dropped = 0
        for amplicon in amplicons:
            fwd = len(amplicon.forward_primers)
            rev = len(amplicon.reverse_primers)
            dropped += max(0, fwd - 1) + max(0, rev - 1)
        return dropped

    def _write_format(
        self,
        amplicons: List[AmpliconData],
        output_format: str,
        output_dir: Path,
        prefix: str,
        reference_file: Optional[Path],
        **kwargs,
    ) -> Optional[Path]:
        """Write amplicons in specified output format."""

        writer = writer_registry.get_writer(output_format)

        # Create format-specific output path
        if output_format == "artic":
            # ARTIC needs special directory structure
            output_path = output_dir / "artic" / prefix / "V1" / f"{prefix}.scheme.bed"
        else:
            extension = writer.file_extension()
            output_path = output_dir / output_format / f"{prefix}{extension}"

        # Check if file exists and force flag
        if output_path.exists() and not self.config.output.force_overwrite:
            if not kwargs.get("force", False):
                raise OutputError(
                    f"Output file exists: {output_path}. Use --force to overwrite."
                )

        # Write the format
        result_path = writer.write(
            amplicons=amplicons,
            output_path=output_path,
            prefix=prefix,
            reference_path=reference_file,
            **kwargs,
        )

        return result_path or output_path

    def _validate_amplicons(
        self, amplicons: List[AmpliconData], lenient: bool = False
    ) -> List[str]:
        """Validate parsed amplicon data.

        Args:
            amplicons: Parsed amplicons to validate.
            lenient: When True, data-quality issues are returned as warnings
                instead of raising ``ValidationError``. An empty input is always
                a hard error regardless of this flag.

        Returns:
            List of warning strings (empty unless lenient mode downgraded issues).
        """
        if not amplicons:
            raise ValidationError("No amplicons found in input file")

        issues: List[str] = []

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
            if self.config.validation.enabled:
                for primer in amplicon.primers:
                    if not primer.sequence:
                        # An empty sequence is valid for a 6-column primer.bed,
                        # where sequences live in reference.fasta. Other parsers
                        # reject empty sequences at parse time, so this only
                        # occurs for sequence-less BED input. Skip content checks
                        # (the converter emits a "no sequence" warning separately).
                        continue

                    # Check sequence length
                    if len(primer.sequence) < self.config.validation.min_length:
                        issues.append(
                            f"Primer {primer.name} is too short "
                            f"({len(primer.sequence)} bp)"
                        )
                    if len(primer.sequence) > self.config.validation.max_length:
                        issues.append(
                            f"Primer {primer.name} is too long "
                            f"({len(primer.sequence)} bp)"
                        )

                    # Check for valid nucleotides (allow IUPAC codes)
                    valid_chars = set("ATCGRYSWKMBDHVNatcgryswkmbdhvn")
                    invalid_chars = set(primer.sequence) - valid_chars
                    if invalid_chars:
                        issues.append(
                            f"Primer {primer.name} contains invalid "
                            f"characters: {invalid_chars}"
                        )

        if issues:
            if len(issues) > 10:
                # Show first 10 issues and count
                issue_summary = (
                    "\n".join(issues[:10]) + f"\n... and {len(issues) - 10} more issues"
                )
            else:
                issue_summary = "\n".join(issues)

            if lenient:
                # Downgrade to warnings so the conversion can proceed.
                logger.warning(
                    f"Validation issues (continuing in lenient mode):\n{issue_summary}"
                )
                return issues

            raise ValidationError(f"Validation failed:\n{issue_summary}")

        logger.info(f"Validation passed for {len(amplicons)} amplicons")
        return []
