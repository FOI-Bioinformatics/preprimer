"""
Output validation framework for PrePrimer real data testing.

Validates format conversions, alignment outputs, and data integrity.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from preprimer.core.interfaces import AmpliconData


@dataclass
class ValidationResult:
    """Results from validation check."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, any] = field(default_factory=dict)

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_stat(self, key: str, value: any):
        """Add a statistic."""
        self.stats[key] = value


class OutputValidator:
    """Validator for PrePrimer outputs."""

    @staticmethod
    def validate_file_exists(file_path: Path) -> ValidationResult:
        """Validate that a file exists."""
        result = ValidationResult(valid=True)

        if not file_path.exists():
            result.add_error(f"File does not exist: {file_path}")
        elif not file_path.is_file():
            result.add_error(f"Path is not a file: {file_path}")
        else:
            result.add_stat("file_size", file_path.stat().st_size)
            result.add_stat("file_path", str(file_path))

        return result

    @staticmethod
    def calculate_md5(file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    @staticmethod
    def validate_primer_count(
        amplicons: List[AmpliconData], expected_min: int = 1
    ) -> ValidationResult:
        """Validate primer counts in amplicons."""
        result = ValidationResult(valid=True)

        total_primers = sum(len(amp.primers) for amp in amplicons)
        total_amplicons = len(amplicons)

        if total_amplicons < expected_min:
            result.add_error(
                f"Insufficient amplicons: {total_amplicons} < {expected_min}"
            )

        if total_primers < expected_min * 2:  # At least 2 primers per amplicon
            result.add_warning(f"Low primer count: {total_primers}")

        result.add_stat("total_amplicons", total_amplicons)
        result.add_stat("total_primers", total_primers)
        result.add_stat("avg_primers_per_amplicon", total_primers / max(total_amplicons, 1))

        return result

    @staticmethod
    def validate_sequence_integrity(amplicons: List[AmpliconData]) -> ValidationResult:
        """Validate primer sequences."""
        result = ValidationResult(valid=True)

        valid_bases = set("ATCGRYSWKMBDHVN")  # IUPAC codes
        sequences_checked = 0
        invalid_chars_found: Set[str] = set()

        for amplicon in amplicons:
            for primer in amplicon.primers:
                sequences_checked += 1

                if not primer.sequence:
                    result.add_error(
                        f"Empty sequence for primer: {primer.name}"
                    )
                    continue

                # Check for invalid characters
                invalid_chars = set(primer.sequence.upper()) - valid_bases
                if invalid_chars:
                    invalid_chars_found.update(invalid_chars)
                    result.add_error(
                        f"Invalid characters in {primer.name}: {invalid_chars}"
                    )

                # Check sequence length
                if primer.length and len(primer.sequence) != primer.length:
                    result.add_warning(
                        f"Length mismatch in {primer.name}: "
                        f"{len(primer.sequence)} != {primer.length}"
                    )

        result.add_stat("sequences_checked", sequences_checked)
        if invalid_chars_found:
            result.add_stat("invalid_characters", list(invalid_chars_found))

        return result


def validate_artic_output(output_dir: Path) -> ValidationResult:
    """Validate ARTIC format output structure."""
    result = ValidationResult(valid=True)

    # Handle if output_dir is actually a file path
    if output_dir.is_file():
        # If it's a BED file, validate it directly
        if output_dir.suffix == ".bed" or output_dir.name.endswith(".scheme.bed"):
            bed_files = [output_dir]
        else:
            result.add_error(f"Expected BED file, got: {output_dir}")
            return result
    else:
        # Check directory structure exists
        if not output_dir.exists():
            result.add_error(f"Output directory does not exist: {output_dir}")
            return result

        # Look for .scheme.bed or primer.bed file
        bed_files = list(output_dir.rglob("*.scheme.bed")) + list(output_dir.rglob("primer.bed"))
        if not bed_files:
            result.add_error("No BED file found in output (looking for *.scheme.bed or primer.bed)")
            return result

    # Add stats for found files
    result.add_stat("bed_files", [str(f) for f in bed_files])

    # Validate BED file format
    bed_file = bed_files[0]
    with open(bed_file) as f:
        lines = [line.strip() for line in f if line.strip()]

    result.add_stat("bed_line_count", len(lines))

    # Check BED format (at least 6 columns)
    for i, line in enumerate(lines[:5], 1):  # Check first 5 lines
        parts = line.split("\t")
        if len(parts) < 6:
            result.add_error(
                f"Line {i} has insufficient columns: {len(parts)} < 6"
            )

    # Look for reference FASTA (only if output_dir is a directory)
    if output_dir.is_dir():
        fasta_files = list(output_dir.rglob("*.reference.fasta")) + list(
            output_dir.rglob("*.fasta")
        )
    else:
        # If we have a file, look in parent directory
        fasta_files = list(output_dir.parent.rglob("*.reference.fasta")) + list(
            output_dir.parent.rglob("*.fasta")
        )
    if fasta_files:
        result.add_stat("fasta_files", [str(f) for f in fasta_files])

    return result


def validate_varvamp_output(output_file: Path) -> ValidationResult:
    """Validate VarVAMP format output."""
    result = ValidationResult(valid=True)

    if not output_file.exists():
        result.add_error(f"Output file does not exist: {output_file}")
        return result

    with open(output_file) as f:
        lines = [line.strip() for line in f if line.strip()]

    result.add_stat("line_count", len(lines))

    # VarVAMP format should have 13 tab-separated columns
    for i, line in enumerate(lines[:5], 1):
        parts = line.split("\t")
        if len(parts) != 13:
            result.add_error(
                f"Line {i} has incorrect column count: {len(parts)} != 13"
            )

    return result


def validate_olivar_output(output_file: Path) -> ValidationResult:
    """Validate Olivar format output."""
    result = ValidationResult(valid=True)

    if not output_file.exists():
        result.add_error(f"Output file does not exist: {output_file}")
        return result

    with open(output_file) as f:
        lines = [line.strip() for line in f if line.strip()]

    result.add_stat("line_count", len(lines))

    # Should be CSV format
    if len(lines) < 2:
        result.add_error("File has insufficient lines (need header + data)")
        return result

    # Check header
    header = lines[0]
    required_columns = ["fP", "rP"]
    for col in required_columns:
        if col not in header:
            result.add_error(f"Missing required column in header: {col}")

    return result


def validate_fasta_output(output_file: Path) -> ValidationResult:
    """Validate FASTA format output."""
    result = ValidationResult(valid=True)

    if not output_file.exists():
        result.add_error(f"Output file does not exist: {output_file}")
        return result

    with open(output_file) as f:
        content = f.read()

    # Count FASTA sequences (lines starting with >)
    sequence_count = content.count("\n>") + (1 if content.startswith(">") else 0)
    result.add_stat("sequence_count", sequence_count)

    if sequence_count == 0:
        result.add_error("No FASTA sequences found")

    # Basic format validation
    lines = content.strip().split("\n")
    for i, line in enumerate(lines):
        if line.startswith(">"):
            # Header line
            if len(line) < 2:
                result.add_error(f"Empty FASTA header at line {i+1}")
        elif line.strip():
            # Sequence line - check for valid characters
            valid_bases = set("ATCGRYSWKMBDHVN")
            invalid = set(line.upper()) - valid_bases
            if invalid:
                result.add_warning(
                    f"Invalid bases at line {i+1}: {invalid}"
                )

    return result


def validate_sts_output(output_file: Path) -> ValidationResult:
    """Validate STS format output (supports both 3 and 4-column formats)."""
    result = ValidationResult(valid=True)

    if not output_file.exists():
        result.add_error(f"Output file does not exist: {output_file}")
        return result

    with open(output_file) as f:
        lines = [line.strip() for line in f if line.strip()]

    result.add_stat("line_count", len(lines))

    if len(lines) < 1:
        result.add_error("File is empty")
        return result

    # Detect format (3 or 4 columns) from first data line
    # Skip header if present (check if first line looks like header)
    first_line = lines[0]
    first_parts = first_line.split("\t")

    # Check if first line is header
    is_header = any(
        keyword in first_line.upper()
        for keyword in ["NAME", "FORWARD", "REVERSE", "SIZE"]
    )

    # Get expected column count from first data line
    data_line_idx = 1 if is_header else 0
    if len(lines) > data_line_idx:
        expected_cols = len(lines[data_line_idx].split("\t"))
    else:
        expected_cols = len(first_parts)

    # STS format should have 3 or 4 tab-separated columns
    if expected_cols not in [3, 4]:
        result.add_error(
            f"Invalid STS format: expected 3 or 4 columns, got {expected_cols}"
        )
        return result

    result.add_stat("column_count", expected_cols)
    result.add_stat("has_header", is_header)
    result.add_stat("format_type", f"{'4-column (extended)' if expected_cols == 4 else '3-column (standard)'}")

    # Validate all lines have consistent column count
    for i, line in enumerate(lines, 1):
        parts = line.split("\t")
        # Allow header to have different count if it's the first line
        if i == 1 and is_header:
            continue
        if len(parts) != expected_cols:
            result.add_error(
                f"Line {i} has incorrect column count: {len(parts)} != {expected_cols}"
            )
            if len(result.errors) >= 10:  # Limit error reporting
                result.add_error("... (additional errors truncated)")
                break

    return result


def validate_conversion(
    input_format: str,
    output_format: str,
    input_file: Path,
    output_path: Path,
    amplicons: Optional[List[AmpliconData]] = None,
) -> ValidationResult:
    """
    Comprehensive validation of format conversion.

    Args:
        input_format: Input format name
        output_format: Output format name
        input_file: Path to input file
        output_path: Path to output file/directory
        amplicons: Optional parsed amplicons for additional validation

    Returns:
        ValidationResult with conversion validation results
    """
    result = ValidationResult(valid=True)

    # Validate input file exists
    if not input_file.exists():
        result.add_error(f"Input file does not exist: {input_file}")
        return result

    # Validate based on output format
    if output_format == "artic":
        format_result = validate_artic_output(output_path)
    elif output_format == "varvamp":
        format_result = validate_varvamp_output(output_path)
    elif output_format == "olivar":
        format_result = validate_olivar_output(output_path)
    elif output_format == "fasta":
        format_result = validate_fasta_output(output_path)
    elif output_format == "sts":
        format_result = validate_sts_output(output_path)
    else:
        result.add_error(f"Unknown output format: {output_format}")
        return result

    # Merge format-specific validation
    result.valid = result.valid and format_result.valid
    result.errors.extend(format_result.errors)
    result.warnings.extend(format_result.warnings)
    result.stats.update(format_result.stats)

    # Additional validation if amplicons provided
    if amplicons:
        primer_result = OutputValidator.validate_primer_count(amplicons)
        result.stats.update(primer_result.stats)
        result.warnings.extend(primer_result.warnings)
        result.errors.extend(primer_result.errors)
        result.valid = result.valid and primer_result.valid

        sequence_result = OutputValidator.validate_sequence_integrity(amplicons)
        result.stats.update(sequence_result.stats)
        result.warnings.extend(sequence_result.warnings)
        result.errors.extend(sequence_result.errors)
        result.valid = result.valid and sequence_result.valid

    # Add conversion metadata
    result.add_stat("conversion", f"{input_format} → {output_format}")
    result.add_stat("input_file", str(input_file))
    result.add_stat("output_path", str(output_path))

    return result
