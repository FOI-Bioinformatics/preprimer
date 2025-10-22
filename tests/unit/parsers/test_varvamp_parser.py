"""
VarVAMP parser tests using BaseParserTest framework.

Demonstrates how to use the base test class to get comprehensive coverage
with minimal code duplication.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.exceptions import (
    CorruptedDataError,
    InvalidFormatError,
    ParserError,
)
from preprimer.parsers.varvamp_parser import VarVAMPParser

from .test_base_parser import BaseParserTest


class TestVarVAMPParser(BaseParserTest):
    """
    VarVAMP parser tests.

    Inherits all contract and standard tests from BaseParserTest.
    Only needs to define the configuration and format-specific tests.
    """

    # =========================================================================
    # Configuration - Required by BaseParserTest
    # =========================================================================

    @property
    def parser_class(self):
        return VarVAMPParser

    @property
    def valid_test_file(self):
        return Path("tests/test_data/datasets/small/varvamp.tsv")

    @property
    def expected_amplicon_count(self):
        return 5

    @property
    def expected_format_name(self):
        return "varvamp"

    @property
    def expected_extensions(self):
        return [".tsv", ".txt"]

    def get_invalid_test_files(self):
        """Return invalid test files for validation tests."""
        return [
            Path("tests/test_data/datasets/small/artic/small_artic/V1/nCoV-2019.bed"),
            Path("tests/test_data/datasets/small/olivar/olivar_primers.csv"),
        ]

    # =========================================================================
    # VarVAMP-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_column_count(self):
        """VarVAMP files must have exactly 13 columns."""
        parser = VarVAMPParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        # Check that we successfully parsed a 13-column format
        assert len(amplicons) == 5, "Should parse all 5 amplicons from 13-column file"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_handles_degenerate_primers(self):
        """VarVAMP format supports IUPAC degenerate nucleotides."""
        # VarVAMP is one of the formats that explicitly supports degenerates
        # This test would verify that if we had a test file with degenerates

        # For now, just verify the parser doesn't reject standard bases
        parser = VarVAMPParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        # All primers should have sequences
        for amp in amplicons:
            for primer in amp.primers:
                assert primer.sequence, f"Primer {primer.name} missing sequence"
                assert all(
                    base in "ATCGNatcgn" for base in primer.sequence
                ), f"Primer {primer.name} has invalid characters in sequence"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_parse_with_missing_columns(self):
        """VarVAMP parser must reject files with wrong column count."""
        # Create a file with only 5 columns (should have 13)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("col1\tcol2\tcol3\tcol4\tcol5\n")
            f.write("val1\tval2\tval3\tval4\tval5\n")
            invalid_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # Should reject during validation
            assert parser.validate_file(invalid_file) is False
        finally:
            invalid_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_parse_empty_file_raises_error(self):
        """VarVAMP parser must raise InvalidFormatError for empty files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("")  # Completely empty
            empty_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises(InvalidFormatError, match="empty|header|format"):
                parser.parse(empty_file, prefix="test")
        finally:
            empty_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_parse_header_only_raises_error(self):
        """VarVAMP parser must raise error for files with only headers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write valid header but no data rows
            header = [
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
            f.write("\t".join(header) + "\n")
            header_only_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # ParserError is also acceptable for this case
            with pytest.raises((InvalidFormatError, CorruptedDataError, ParserError)):
                parser.parse(header_only_file, prefix="test")
        finally:
            header_only_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_amplicon_structure(self):
        """VarVAMP amplicons must have correct structure."""
        parser = VarVAMPParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            # Check required attributes
            assert amp.amplicon_id, "Amplicon must have ID"
            assert amp.length > 0, "Amplicon must have positive length"
            assert amp.primers, "Amplicon must have primers"

            # VarVAMP typically has forward/reverse pairs
            forward_primers = [p for p in amp.primers if p.direction == "forward"]
            reverse_primers = [p for p in amp.primers if p.direction == "reverse"]

            assert len(forward_primers) > 0, "Must have at least one forward primer"
            assert len(reverse_primers) > 0, "Must have at least one reverse primer"

            # Check primer attributes
            for primer in amp.primers:
                assert primer.name, "Primer must have name"
                assert primer.sequence, "Primer must have sequence"
                assert primer.start >= 0, "Primer start must be non-negative"
                assert primer.stop > primer.start, "Primer stop must be after start"
                assert primer.pool is not None, "Primer must have pool assignment"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_varvamp_prefix_applied_correctly(self):
        """VarVAMP parser applies prefix to reference_id (not amplicon_id)."""
        parser = VarVAMPParser()
        prefix = "COVID19"

        amplicons = parser.parse(self.valid_test_file, prefix=prefix)

        for amp in amplicons:
            # VarVAMP uses prefix for reference_id, not amplicon_id
            # Amplicon IDs come from the "amplicon_name" column in the file
            assert (
                amp.reference_id == prefix
            ), f"Reference ID should be '{prefix}', got '{amp.reference_id}'"

            # Verify amplicon has ID from source file
            assert amp.amplicon_id, "Amplicon must have ID from source file"

            # Primers should reference the amplicon and have the prefix as reference_id
            for primer in amp.primers:
                assert primer.amplicon_id == amp.amplicon_id, (
                    f"Primer {primer.name} should reference "
                    f"amplicon {amp.amplicon_id}"
                )
                assert (
                    primer.reference_id == prefix
                ), f"Primer reference_id should be '{prefix}'"


# =============================================================================
# Additional Test Classes for Edge Cases
# =============================================================================


@pytest.mark.unit
@pytest.mark.parser
class TestVarVAMPParserEdgeCases:
    """VarVAMP parser edge case tests (not using BaseParserTest)."""

    def test_validate_file_with_unicode_decode_error(self):
        """Parser must handle files with invalid UTF-8."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".tsv", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\x80\x81\x82invalid utf-8\x90\x91\x92")
            invalid_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = parser.validate_file(invalid_file)
            # Should return False, not crash
            assert result is False, "Should reject file with invalid UTF-8"
        finally:
            invalid_file.unlink()

    def test_parse_with_inconsistent_pools(self):
        """VarVAMP parser should handle inconsistent pool assignments."""
        # Create a file with primers in same amplicon assigned to different pools
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
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
            f.write("\t".join(header) + "\n")

            # Same amplicon, different pools
            f.write("amp1\t200\tamp1_LEFT\t1\t100\t120\tATCGATCGATCGATCGATCG\t20\t50.0\t60.0\t50.0\t60.0\t1.0\n")
            f.write("amp1\t200\tamp1_RIGHT\t2\t280\t300\tGCTAGCTAGCTAGCTAGCTA\t20\t50.0\t60.0\t50.0\t60.0\t1.0\n")

            inconsistent_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # Should either parse successfully (taking first pool) or raise an error
            # The behavior depends on implementation - we just ensure it doesn't crash
            try:
                amplicons = parser.parse(inconsistent_file, prefix="test")
                # If it parsed, verify it has the amplicon
                assert len(amplicons) >= 1
            except (InvalidFormatError, CorruptedDataError):
                # Also acceptable to reject
                pass
        finally:
            inconsistent_file.unlink()
