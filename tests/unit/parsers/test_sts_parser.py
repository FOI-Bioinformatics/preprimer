"""
STS parser tests using BaseParserTest framework.

STS (Sequence Tagged Site) format is a simple TSV format with 3-4 columns.
Supports both headerless and header formats.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.exceptions import InvalidFormatError, ParserError
from preprimer.parsers.sts_parser import STSParser

from .test_base_parser import BaseParserTest


class TestSTSParser(BaseParserTest):
    """STS parser tests - inherits contract tests from BaseParserTest."""

    # =========================================================================
    # Configuration - Required by BaseParserTest
    # =========================================================================

    @property
    def parser_class(self):
        return STSParser

    @property
    def valid_test_file(self):
        return Path("tests/test_data/datasets/small/sts.tsv")

    @property
    def expected_amplicon_count(self):
        return 5  # Small STS file has 5 amplicons

    @property
    def expected_format_name(self):
        return "sts"

    @property
    def expected_extensions(self):
        return [".sts.tsv", ".sts", ".tsv"]

    def get_invalid_test_files(self):
        """Return invalid test files for validation tests."""
        return [
            Path("tests/test_data/datasets/small/varvamp.tsv"),  # Different TSV format
            Path("tests/test_data/datasets/small/artic.scheme.bed"),
        ]

    # =========================================================================
    # STS-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_tsv_format(self):
        """STS files must be valid TSV format (3 or 4 columns)."""
        parser = STSParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        assert len(amplicons) == 5, "Should parse all 5 amplicons from STS file"

        # STS format: amplicon_id, forward_seq, reverse_seq, [length]
        for amp in amplicons:
            assert amp.amplicon_id, "Amplicon must have ID from first column"
            assert len(amp.primers) == 2, "STS amplicons should have exactly 2 primers"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_primer_pairs(self):
        """STS format always has forward/reverse pairs."""
        parser = STSParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            forward_primers = [p for p in amp.primers if p.direction == "forward"]
            reverse_primers = [p for p in amp.primers if p.direction == "reverse"]

            assert len(forward_primers) == 1, f"STS amplicon must have 1 forward primer"
            assert len(reverse_primers) == 1, f"STS amplicon must have 1 reverse primer"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_sequence_format(self):
        """STS primers must have valid DNA sequences."""
        parser = STSParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            for primer in amp.primers:
                assert primer.sequence, f"Primer must have sequence"
                # Check only contains valid DNA bases (including IUPAC)
                assert all(
                    base.upper() in "ATCGNRYSWKMBDHV" for base in primer.sequence
                ), f"Invalid bases in primer sequence: {primer.sequence}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_amplicon_length(self):
        """STS amplicons should have reasonable length."""
        parser = STSParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            assert amp.length > 0, "Amplicon must have positive length"
            # STS typically has lengths provided or calculated
            assert amp.length < 10000, f"Amplicon length seems unusual: {amp.length}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_three_column_format(self):
        """STS parser must handle 3-column format (no length)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write 3-column STS format (id, forward, reverse)
            f.write("amp1\tATCGATCGATCGATCG\tGCTAGCTAGCTAGCTA\n")
            f.write("amp2\tCGCGCGCGCGCGCGCG\tTATATATATATATATA\n")
            three_col_file = Path(f.name)

        try:
            parser = STSParser()
            amplicons = parser.parse(three_col_file, prefix="test")

            assert len(amplicons) == 2, "Should parse 2 amplicons from 3-column format"
            for amp in amplicons:
                assert len(amp.primers) == 2, "Should have 2 primers per amplicon"
        finally:
            three_col_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_four_column_format(self):
        """STS parser must handle 4-column format (with length)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write 4-column STS format (id, forward, reverse, length)
            f.write("amp1\tATCGATCGATCGATCG\tGCTAGCTAGCTAGCTA\t200\n")
            f.write("amp2\tCGCGCGCGCGCGCGCG\tTATATATATATATATA\t150\n")
            four_col_file = Path(f.name)

        try:
            parser = STSParser()
            amplicons = parser.parse(four_col_file, prefix="test")

            assert len(amplicons) == 2, "Should parse 2 amplicons from 4-column format"
            for amp in amplicons:
                assert amp.length > 0, "Should have length from 4th column"
        finally:
            four_col_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_malformed_tsv_raises_error(self):
        """STS parser must reject malformed TSV files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write invalid STS (wrong number of columns)
            f.write("amp1\tATCG\n")  # Only 2 columns, need 3 or 4
            malformed_file = Path(f.name)

        try:
            parser = STSParser()
            # Should reject during validation or parsing
            result = parser.validate_file(malformed_file)
            if result:
                with pytest.raises((InvalidFormatError, ParserError)):
                    parser.parse(malformed_file, prefix="test")
        finally:
            malformed_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_sts_empty_file_raises_error(self):
        """STS parser must reject empty files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("")  # Completely empty
            empty_file = Path(f.name)

        try:
            parser = STSParser()
            with pytest.raises((InvalidFormatError, ParserError)):
                parser.parse(empty_file, prefix="test")
        finally:
            empty_file.unlink()


# =============================================================================
# Additional Test Classes for Edge Cases
# =============================================================================


@pytest.mark.unit
@pytest.mark.parser
class TestSTSParserEdgeCases:
    """STS parser edge case tests."""

    def test_sts_with_degenerate_bases(self):
        """STS parser should handle IUPAC degenerate bases."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write STS with degenerate bases (N, R, Y, etc.)
            f.write("amp1\tATCGNNNNATCG\tGCTARYWSKMBG\t200\n")
            degenerate_file = Path(f.name)

        try:
            parser = STSParser()
            amplicons = parser.parse(degenerate_file, prefix="test")

            assert len(amplicons) == 1, "Should parse amplicon with degenerate bases"
            for amp in amplicons:
                for primer in amp.primers:
                    # Sequence should be preserved
                    assert primer.sequence, "Primer must have sequence"
        finally:
            degenerate_file.unlink()
