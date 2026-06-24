"""
ARTIC parser tests using BaseParserTest framework.

ARTIC format uses BED files with specific naming conventions for primers.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.exceptions import InvalidFormatError, ParserError
from preprimer.parsers.artic_parser import ARTICParser

from .test_base_parser import BaseParserTest


class TestARTICParser(BaseParserTest):
    """ARTIC parser tests - inherits contract tests from BaseParserTest."""

    # =========================================================================
    # Configuration - Required by BaseParserTest
    # =========================================================================

    @property
    def parser_class(self):
        return ARTICParser

    @property
    def valid_test_file(self):
        return Path("tests/test_data/datasets/small/artic.scheme.bed")

    @property
    def expected_amplicon_count(self):
        return 5

    @property
    def expected_format_name(self):
        return "artic"

    @property
    def expected_extensions(self):
        return [".bed", ".scheme.bed"]

    def get_invalid_test_files(self):
        """Return invalid test files for validation tests."""
        return [
            Path("tests/test_data/datasets/small/varvamp.tsv"),
            Path("tests/test_data/datasets/small/olivar.csv"),
        ]

    # =========================================================================
    # ARTIC-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_bed_format(self):
        """ARTIC files must be valid BED format with primer naming."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        assert len(amplicons) == 5, "Should parse all 5 amplicons from BED file"

        # Check BED format compliance
        for amp in amplicons:
            for primer in amp.primers:
                # ARTIC primers contain _LEFT or _RIGHT (may have _1, _2 suffix for alternates)
                assert (
                    "_LEFT" in primer.name or "_RIGHT" in primer.name
                ), f"ARTIC primer name must contain _LEFT or _RIGHT: {primer.name}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_primer_pairing(self):
        """ARTIC primers must come in LEFT/RIGHT pairs."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            left_primers = [
                p
                for p in amp.primers
                if p.name.endswith("_LEFT") or p.direction == "forward"
            ]
            right_primers = [
                p
                for p in amp.primers
                if p.name.endswith("_RIGHT") or p.direction == "reverse"
            ]

            assert (
                len(left_primers) > 0
            ), f"Amplicon {amp.amplicon_id} must have LEFT primer"
            assert (
                len(right_primers) > 0
            ), f"Amplicon {amp.amplicon_id} must have RIGHT primer"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_pool_assignment(self):
        """ARTIC amplicons must have pool assignments."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            for primer in amp.primers:
                assert (
                    primer.pool is not None
                ), f"Primer {primer.name} must have pool assignment"
                assert primer.pool > 0, f"Pool must be positive: {primer.pool}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_coordinates(self):
        """ARTIC primers must have valid genomic coordinates."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            for primer in amp.primers:
                assert primer.start >= 0, f"Primer start must be non-negative"
                assert primer.stop > primer.start, f"Primer stop must be after start"
                assert (
                    primer.stop - primer.start < 50
                ), f"Primer length seems too long: {primer.stop - primer.start}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_amplicon_structure(self):
        """ARTIC amplicons must have correct structure."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        for amp in amplicons:
            # Check required attributes
            assert amp.amplicon_id, "Amplicon must have ID"
            assert amp.length > 0, "Amplicon must have positive length"
            assert amp.primers, "Amplicon must have primers"

            # ARTIC amplicons should have reasonable length (50-2000bp typically)
            assert (
                50 < amp.length < 5000
            ), f"Amplicon length seems unusual: {amp.length}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_alternate_primers(self):
        """ARTIC format supports alternate primers (alt1, alt2, etc.)."""
        parser = ARTICParser()
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        # Check if any amplicons have alternates
        # (The test file might not have alternates, so this just verifies structure)
        for amp in amplicons:
            for primer in amp.primers:
                # Primer names might have _alt1, _alt2, etc.
                # Just verify the name is well-formed
                assert primer.name, "Primer must have a name"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_malformed_bed_raises_error(self):
        """ARTIC parser must reject malformed BED files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bed", delete=False) as f:
            # Write invalid BED (wrong number of columns)
            f.write("chr1\t100\n")  # Only 2 columns, need at least 6
            malformed_file = Path(f.name)

        try:
            parser = ARTICParser()
            # Should reject during validation or parsing
            result = parser.validate_file(malformed_file)
            if result:
                # If validation passed, parsing should fail
                with pytest.raises((InvalidFormatError, ParserError)):
                    parser.parse(malformed_file, prefix="test")
        finally:
            malformed_file.unlink()

    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_with_prefix(self):
        """ARTIC parser gets reference from BED file, not from prefix parameter."""
        parser = ARTICParser()
        prefix = "TEST_PREFIX"

        amplicons = parser.parse(self.valid_test_file, prefix=prefix)

        # ARTIC parser uses reference_id from BED file's chromosome column
        # Prefix is not directly used in amplicon_id or reference_id
        for amp in amplicons:
            assert amp.reference_id, "Must have reference_id from BED file"
            assert amp.amplicon_id, "Must have amplicon_id"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_artic_reference_id_from_bed(self):
        """ARTIC parser uses reference_id from BED file (column 1)."""
        parser = ARTICParser()
        prefix = (
            "SARS-CoV-2"  # Prefix is used for generating IDs, not replacing reference
        )

        amplicons = parser.parse(self.valid_test_file, prefix=prefix)

        for amp in amplicons:
            # ARTIC gets reference_id from BED file's first column (chromosome)
            # The test file uses "EPI_ISL_402124" as the reference
            assert amp.reference_id, "Amplicon must have reference_id from BED file"
            # Amplicon IDs are generated (amplicon_1, amplicon_2, etc.)
            assert amp.amplicon_id, "Amplicon must have ID"


# =============================================================================
# Additional Test Classes for Edge Cases
# =============================================================================


@pytest.mark.unit
@pytest.mark.parser
class TestARTICParserEdgeCases:
    """ARTIC parser edge case tests."""

    def test_artic_empty_bed_raises_error(self):
        """ARTIC parser must reject empty BED files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bed", delete=False) as f:
            f.write("")  # Completely empty
            empty_file = Path(f.name)

        try:
            parser = ARTICParser()
            with pytest.raises((InvalidFormatError, ParserError)):
                parser.parse(empty_file, prefix="test")
        finally:
            empty_file.unlink()

    def test_artic_no_primer_pairs_raises_error(self):
        """ARTIC parser must reject files with incomplete primer pairs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bed", delete=False) as f:
            # Write only LEFT primer, no RIGHT primer
            f.write("MN908947.3\t100\t120\tamp1_LEFT\t1\t+\n")
            incomplete_file = Path(f.name)

        try:
            parser = ARTICParser()
            # Should either reject during validation or raise error during parsing
            result = parser.validate_file(incomplete_file)
            if result:
                with pytest.raises((InvalidFormatError, ParserError)):
                    parser.parse(incomplete_file, prefix="test")
        finally:
            incomplete_file.unlink()
