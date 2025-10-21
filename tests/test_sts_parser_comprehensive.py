"""
Comprehensive tests for STS parser implementation.

Tests cover format validation, parsing logic, error handling, and edge cases
to ensure robust STS format support for bidirectional conversion.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.exceptions import (
    CorruptedDataError,
    InsufficientDataError,
    InvalidFormatError,
    ParserError,
)
from preprimer.parsers.sts_parser import STSParser


class TestSTSParserBasics:
    """Test basic STS parser functionality."""

    def test_format_name(self):
        """Test format name identification."""
        parser = STSParser()
        assert parser.format_name() == "sts"

    def test_file_extensions(self):
        """Test supported file extensions."""
        parser = STSParser()
        extensions = parser.file_extensions()
        assert ".sts.tsv" in extensions
        assert ".sts" in extensions
        assert ".tsv" in extensions

    def test_parser_registration(self):
        """Test that STS parser is registered."""
        from preprimer.core.registry import parser_registry

        parser = parser_registry.get_parser("sts")
        assert parser is not None
        assert isinstance(parser, STSParser)


class TestSTSFormatValidation:
    """Test STS format validation logic."""

    def test_valid_sts_file(self, tmp_path):
        """Test validation of valid STS file."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amplicon1\tATCGATCGATCG\tCGATCGATCGAT\n"

        sts_file = tmp_path / "valid.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is True

    def test_empty_file(self, tmp_path):
        """Test validation of empty file."""
        sts_file = tmp_path / "empty.sts.tsv"
        sts_file.write_text("")

        parser = STSParser()
        assert parser.validate_file(sts_file) is False

    def test_missing_header(self, tmp_path):
        """Test validation of file without header."""
        content = "amplicon1\tATCGATCGATCG\tCGATCGATCGAT\n"

        sts_file = tmp_path / "no_header.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is False

    def test_invalid_header(self, tmp_path):
        """Test validation of file with invalid header."""
        content = "NAME\tSEQ1\tSEQ2\n"
        content += "amplicon1\tATCGATCGATCG\tCGATCGATCGAT\n"

        sts_file = tmp_path / "invalid_header.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is False

    def test_case_insensitive_header(self, tmp_path):
        """Test that header matching is case-insensitive."""
        content = "name\tforward\treverse\n"
        content += "amplicon1\tATCGATCGATCG\tCGATCGATCGAT\n"

        sts_file = tmp_path / "lowercase_header.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is True

    def test_header_only_file(self, tmp_path):
        """Test validation of file with only header."""
        content = "NAME\tFORWARD\tREVERSE\n"

        sts_file = tmp_path / "header_only.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is False

    def test_invalid_field_count(self, tmp_path):
        """Test validation of file with wrong number of fields."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amplicon1\tATCGATCGATCG\n"  # Missing REVERSE field

        sts_file = tmp_path / "missing_field.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        assert parser.validate_file(sts_file) is False

    def test_nonexistent_file(self, tmp_path):
        """Test validation of non-existent file."""
        sts_file = tmp_path / "nonexistent.sts.tsv"

        parser = STSParser()
        assert parser.validate_file(sts_file) is False


class TestSTSParsing:
    """Test STS file parsing functionality."""

    def test_parse_basic_file(self, tmp_path):
        """Test parsing of basic STS file."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amplicon1\tATCGATCGATCG\tCGATCGATCGAT\n"
        content += "amplicon2\tGCTAGCTAGCTA\tTAGCTAGCTAGC\n"

        sts_file = tmp_path / "basic.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "test")

        assert len(amplicons) == 2
        assert "amplicon1" in [amp.amplicon_id for amp in amplicons]
        assert "amplicon2" in [amp.amplicon_id for amp in amplicons]

    def test_parse_amplicon_structure(self, tmp_path):
        """Test that parsed amplicons have correct structure."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "test_amp\tATCGATCGATCGATCG\tCGATCGATCGATCGAT\n"

        sts_file = tmp_path / "structure.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "test_ref")

        amplicon = amplicons[0]
        assert amplicon.amplicon_id == "test_amp"
        assert len(amplicon.primers) == 2
        assert len(amplicon.forward_primers) == 1
        assert len(amplicon.reverse_primers) == 1
        assert amplicon.reference_id == "test_ref"

    def test_parse_primer_sequences(self, tmp_path):
        """Test that primer sequences are correctly parsed."""
        forward_seq = "ATCGATCGATCG"
        reverse_seq = "CGATCGATCGAT"

        content = "NAME\tFORWARD\tREVERSE\n"
        content += f"amp1\t{forward_seq}\t{reverse_seq}\n"

        sts_file = tmp_path / "sequences.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        amplicon = amplicons[0]
        fwd = amplicon.forward_primers[0]
        rev = amplicon.reverse_primers[0]

        assert fwd.sequence == forward_seq.upper()
        assert rev.sequence == reverse_seq.upper()

    def test_parse_primer_names(self, tmp_path):
        """Test that primer names are correctly generated."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "my_amplicon\tATCGATCG\tCGATCGAT\n"

        sts_file = tmp_path / "names.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        amplicon = amplicons[0]
        assert amplicon.forward_primers[0].name == "my_amplicon_LEFT"
        assert amplicon.reverse_primers[0].name == "my_amplicon_RIGHT"

    def test_parse_primer_directions(self, tmp_path):
        """Test that primer directions are correctly assigned."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp\tATCG\tCGAT\n"

        sts_file = tmp_path / "directions.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        amplicon = amplicons[0]
        assert amplicon.forward_primers[0].direction == "forward"
        assert amplicon.reverse_primers[0].direction == "reverse"
        assert amplicon.forward_primers[0].strand == "+"
        assert amplicon.reverse_primers[0].strand == "-"

    def test_parse_empty_rows_skipped(self, tmp_path):
        """Test that empty rows are skipped during parsing."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp1\tATCGATCG\tCGATCGAT\n"
        content += "\t\t\n"  # Empty row
        content += "amp2\tGCTAGCTA\tTAGCTAGC\n"

        sts_file = tmp_path / "empty_rows.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert len(amplicons) == 2  # Empty row should be skipped

    def test_parse_no_reference_file(self, tmp_path):
        """Test that STS parser returns None for reference file."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp\tATCG\tCGAT\n"

        sts_file = tmp_path / "no_ref.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        ref_file = parser.get_reference_file(sts_file)

        assert ref_file is None  # STS format doesn't have reference files


class TestSTSErrorHandling:
    """Test error handling in STS parser."""

    def test_empty_file_raises_error(self, tmp_path):
        """Test that empty file raises appropriate error."""
        sts_file = tmp_path / "empty.sts.tsv"
        sts_file.write_text("NAME\tFORWARD\tREVERSE\n")  # Header only

        parser = STSParser()
        with pytest.raises((InsufficientDataError, ParserError)):
            parser.parse(sts_file, "ref")

    def test_missing_required_field(self, tmp_path):
        """Test that missing required field raises error."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp1\tATCGATCG\t\n"  # Missing REVERSE

        sts_file = tmp_path / "missing_field.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        with pytest.raises((CorruptedDataError, ParserError)):
            parser.parse(sts_file, "ref")

    def test_empty_sequence(self, tmp_path):
        """Test that empty sequence raises error."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp1\t\tCGATCGAT\n"  # Empty FORWARD

        sts_file = tmp_path / "empty_seq.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        with pytest.raises((CorruptedDataError, ParserError)):
            parser.parse(sts_file, "ref")

    def test_invalid_characters_in_sequence(self, tmp_path):
        """Test that invalid characters in sequence raise error."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp1\tATCG123\tCGAT\n"  # Invalid characters

        sts_file = tmp_path / "invalid_chars.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        with pytest.raises((ParserError, CorruptedDataError)):
            parser.parse(sts_file, "ref")

    def test_nonexistent_file_raises_error(self, tmp_path):
        """Test that non-existent file raises error."""
        sts_file = tmp_path / "nonexistent.sts.tsv"

        parser = STSParser()
        with pytest.raises(ParserError):
            parser.parse(sts_file, "ref")


class TestSTSEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_sequences(self, tmp_path):
        """Test parsing of very long primer sequences."""
        long_seq = "A" * 500
        content = "NAME\tFORWARD\tREVERSE\n"
        content += f"amp\t{long_seq}\t{long_seq}\n"

        sts_file = tmp_path / "long_seq.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert len(amplicons[0].forward_primers[0].sequence) == 500

    def test_minimal_sequences(self, tmp_path):
        """Test parsing of minimal primer sequences."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp\tATCG\tCGAT\n"

        sts_file = tmp_path / "minimal.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert len(amplicons) == 1
        assert len(amplicons[0].forward_primers[0].sequence) == 4

    def test_many_amplicons(self, tmp_path):
        """Test parsing file with many amplicons."""
        content = "NAME\tFORWARD\tREVERSE\n"
        for i in range(100):
            content += f"amp{i}\tATCGATCG\tCGATCGAT\n"

        sts_file = tmp_path / "many_amps.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert len(amplicons) == 100

    def test_special_characters_in_name(self, tmp_path):
        """Test handling of special characters in amplicon names."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp-1_test.v2\tATCGATCG\tCGATCGAT\n"

        sts_file = tmp_path / "special_chars.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert amplicons[0].amplicon_id == "amp-1_test.v2"

    def test_lowercase_sequences(self, tmp_path):
        """Test that lowercase sequences are converted to uppercase."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp\tatcgatcg\tcgatcgat\n"

        sts_file = tmp_path / "lowercase.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert amplicons[0].forward_primers[0].sequence == "ATCGATCG"
        assert amplicons[0].reverse_primers[0].sequence == "CGATCGAT"

    def test_mixed_case_sequences(self, tmp_path):
        """Test handling of mixed case sequences."""
        content = "NAME\tFORWARD\tREVERSE\n"
        content += "amp\tAtCgAtCg\tcGaTcGaT\n"

        sts_file = tmp_path / "mixed_case.sts.tsv"
        sts_file.write_text(content)

        parser = STSParser()
        amplicons = parser.parse(sts_file, "ref")

        assert amplicons[0].forward_primers[0].sequence == "ATCGATCG"
        assert amplicons[0].reverse_primers[0].sequence == "CGATCGAT"


class TestSTSRoundTrip:
    """Test round-trip conversion between STS format and amplicon data."""

    def test_write_then_parse(self, tmp_path):
        """Test that data written can be parsed back correctly."""
        from preprimer.core.interfaces import AmpliconData, PrimerData
        from preprimer.writers.sts_writer import STSWriter

        # Create test data
        fwd_primer = PrimerData(
            name="amp1_LEFT",
            sequence="ATCGATCGATCG",
            start=0,
            stop=12,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amp1",
            reference_id="ref",
        )

        rev_primer = PrimerData(
            name="amp1_RIGHT",
            sequence="CGATCGATCGAT",
            start=300,
            stop=312,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amp1",
            reference_id="ref",
        )

        amplicon = AmpliconData(
            amplicon_id="amp1",
            primers=[fwd_primer, rev_primer],
            length=312,
            reference_id="ref",
        )

        # Write STS
        sts_file = tmp_path / "roundtrip.sts.tsv"
        writer = STSWriter()
        writer.write([amplicon], sts_file, prefix="ref")

        # Parse it back
        parser = STSParser()
        parsed_amplicons = parser.parse(sts_file, "ref")

        # Verify
        assert len(parsed_amplicons) == 1
        parsed_amp = parsed_amplicons[0]
        # Writer prefixes amplicon ID with reference_id
        assert parsed_amp.amplicon_id in ["amp1", "ref_amp1"]
        assert parsed_amp.forward_primers[0].sequence == "ATCGATCGATCG"
        assert parsed_amp.reverse_primers[0].sequence == "CGATCGATCGAT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
