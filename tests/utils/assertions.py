"""
Custom assertion helpers for PrePrimer tests.

Provides domain-specific assertions for clearer, more maintainable tests.
"""

from pathlib import Path
from typing import Dict, List, Optional

from preprimer.core.interfaces import AmpliconData, PrimerData


def assert_amplicons_equal(
    actual: Dict[str, AmpliconData],
    expected: Dict[str, AmpliconData],
    *,
    check_metadata: bool = True,
    tolerance: float = 0.01
) -> None:
    """
    Assert two amplicon dictionaries are equal.

    Args:
        actual: Actual amplicons
        expected: Expected amplicons
        check_metadata: Whether to check metadata fields
        tolerance: Tolerance for floating point comparisons
    """
    assert set(actual.keys()) == set(expected.keys()), \
        f"Amplicon IDs don't match. Actual: {set(actual.keys())}, Expected: {set(expected.keys())}"

    for amp_id in actual.keys():
        actual_amp = actual[amp_id]
        expected_amp = expected[amp_id]

        assert actual_amp.amplicon_id == expected_amp.amplicon_id
        assert len(actual_amp.primers) == len(expected_amp.primers), \
            f"Primer count mismatch for {amp_id}: {len(actual_amp.primers)} vs {len(expected_amp.primers)}"

        if actual_amp.length and expected_amp.length:
            assert abs(actual_amp.length - expected_amp.length) <= tolerance, \
                f"Length mismatch for {amp_id}: {actual_amp.length} vs {expected_amp.length}"


def assert_primer_valid(
    primer: PrimerData,
    *,
    min_length: int = 15,
    max_length: int = 35,
    check_gc: bool = True,
    min_gc: float = 0.3,
    max_gc: float = 0.7
) -> None:
    """
    Assert a primer meets validity constraints.

    Args:
        primer: Primer to validate
        min_length: Minimum primer length
        max_length: Maximum primer length
        check_gc: Whether to check GC content
        min_gc: Minimum GC content (if check_gc=True)
        max_gc: Maximum GC content (if check_gc=True)
    """
    # Check basic fields
    assert primer.name, "Primer must have a name"
    assert primer.sequence, "Primer must have a sequence"
    assert primer.direction in ("forward", "reverse"), \
        f"Invalid direction: {primer.direction}"

    # Check sequence length
    seq_len = len(primer.sequence)
    assert min_length <= seq_len <= max_length, \
        f"Primer length {seq_len} outside range [{min_length}, {max_length}]"

    # Check sequence validity (DNA only)
    valid_chars = set("ATCGRYSWKMBDHVN")  # Include IUPAC codes
    invalid_chars = set(primer.sequence.upper()) - valid_chars
    assert not invalid_chars, \
        f"Invalid characters in sequence: {invalid_chars}"

    # Check GC content if available and requested
    if check_gc and primer.gc_content is not None:
        assert min_gc <= primer.gc_content <= max_gc, \
            f"GC content {primer.gc_content} outside range [{min_gc}, {max_gc}]"


def assert_file_format_valid(
    file_path: Path,
    format_type: str,
    *,
    min_lines: Optional[int] = None,
    max_lines: Optional[int] = None,
    required_columns: Optional[List[str]] = None
) -> None:
    """
    Assert a file meets format specifications.

    Args:
        file_path: Path to file
        format_type: Expected format (varvamp, artic, etc.)
        min_lines: Minimum number of lines
        max_lines: Maximum number of lines
        required_columns: Required column names (for TSV/CSV)
    """
    assert file_path.exists(), f"File does not exist: {file_path}"
    assert file_path.is_file(), f"Not a file: {file_path}"

    with open(file_path) as f:
        lines = f.readlines()

    line_count = len(lines)

    if min_lines is not None:
        assert line_count >= min_lines, \
            f"File has {line_count} lines, expected at least {min_lines}"

    if max_lines is not None:
        assert line_count <= max_lines, \
            f"File has {line_count} lines, expected at most {max_lines}"

    # Check columns for TSV/CSV formats
    if required_columns and line_count > 0:
        if format_type in ("varvamp", "sts"):
            header = lines[0].strip().split("\t")
        elif format_type == "olivar":
            header = lines[0].strip().split(",")
        else:
            return  # Skip column check for other formats

        missing_cols = set(required_columns) - set(header)
        assert not missing_cols, \
            f"Missing required columns: {missing_cols}"


def assert_conversion_successful(
    result: Dict[str, Path],
    expected_formats: List[str]
) -> None:
    """
    Assert a conversion produced expected output formats.

    Args:
        result: Conversion result dictionary (format -> path)
        expected_formats: List of expected format names
    """
    assert set(result.keys()) == set(expected_formats), \
        f"Format mismatch. Got: {set(result.keys())}, Expected: {set(expected_formats)}"

    for format_name, output_path in result.items():
        assert output_path.exists(), \
            f"Output file for {format_name} does not exist: {output_path}"
        assert output_path.stat().st_size > 0, \
            f"Output file for {format_name} is empty: {output_path}"


def assert_amplicon_structure_valid(amplicon: AmpliconData) -> None:
    """
    Assert an amplicon has valid structure.

    Args:
        amplicon: Amplicon to validate
    """
    assert amplicon.amplicon_id, "Amplicon must have an ID"
    assert len(amplicon.primers) > 0, "Amplicon must have at least one primer"

    # Check for forward and reverse primers
    forward_primers = [p for p in amplicon.primers if p.direction == "forward"]
    reverse_primers = [p for p in amplicon.primers if p.direction == "reverse"]

    assert len(forward_primers) > 0, f"Amplicon {amplicon.amplicon_id} has no forward primers"
    assert len(reverse_primers) > 0, f"Amplicon {amplicon.amplicon_id} has no reverse primers"

    # Check primer pairs
    primer_pairs = amplicon.primer_pairs
    assert len(primer_pairs) > 0, f"Amplicon {amplicon.amplicon_id} has no valid primer pairs"


def assert_no_validation_errors(amplicons: Dict[str, AmpliconData]) -> None:
    """
    Assert amplicons have no validation errors.

    Args:
        amplicons: Dictionary of amplicons to validate
    """
    for amp_id, amplicon in amplicons.items():
        # Check all primers are valid
        for primer in amplicon.primers:
            assert_primer_valid(primer)

        # Check amplicon structure
        assert_amplicon_structure_valid(amplicon)
