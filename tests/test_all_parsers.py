"""
Harmonized pytest test suite for all PrePrimer parsers.

This module provides comprehensive, standardized testing for VarVAMP, ARTIC,
and Olivar parsers using pytest fixtures and parametrized tests.
"""

from pathlib import Path

import pytest

from preprimer import convert_primers
from preprimer.core.converter import PrimerConverter
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.registry import parser_registry, writer_registry


class TestParserValidation:
    """Test parser validation and format detection."""

    def test_format_detection(self, parser_test_data):
        """Test that format detection works correctly for all parsers."""
        file_path = parser_test_data["file"]
        expected_format = parser_test_data["format"]

        detected_format = parser_registry.detect_format(file_path)
        assert detected_format == expected_format

    def test_parser_properties(self, parser_test_data):
        """Test that parser properties are correctly set."""
        format_name = parser_test_data["format"]
        parser = parser_registry.get_parser(format_name)

        assert parser.format_name() == format_name
        assert len(parser.file_extensions()) >= 1

        # Test file validation
        file_path = parser_test_data["file"]
        assert parser.validate_file(file_path) is True


class TestParserConsistency:
    """Test parser consistency across all supported formats."""

    def test_parsing_results(self, parser_test_data):
        """Test that parsing produces expected results."""
        format_name = parser_test_data["format"]
        file_path = parser_test_data["file"]
        expected_amplicons = parser_test_data["expected_amplicons"]
        expected_primers = parser_test_data["expected_primers"]

        parser = parser_registry.get_parser(format_name)
        amplicons = parser.parse(file_path, "TEST")

        assert len(amplicons) == expected_amplicons
        total_primers = sum(len(a.primers) for a in amplicons)
        assert total_primers == expected_primers

    def test_primer_data_quality(self, parser_test_data):
        """Test that parsed primer data meets quality standards."""
        format_name = parser_test_data["format"]
        file_path = parser_test_data["file"]

        parser = parser_registry.get_parser(format_name)
        amplicons = parser.parse(file_path, "TEST")

        for amplicon in amplicons:
            self._validate_amplicon(amplicon)

    def _validate_amplicon(self, amplicon: AmpliconData):
        """Validate amplicon data quality."""
        assert amplicon.amplicon_id is not None
        assert len(amplicon.primers) >= 2
        assert len(amplicon.forward_primers) >= 1
        assert len(amplicon.reverse_primers) >= 1

        for primer in amplicon.primers:
            self._validate_primer(primer)

    def _validate_primer(self, primer: PrimerData):
        """Validate primer data quality."""
        assert primer.name is not None and primer.name != ""
        assert primer.sequence is not None and primer.sequence != ""
        assert primer.start >= 0
        assert primer.stop >= 0
        assert abs(primer.stop - primer.start) > 0
        assert primer.strand in ["+", "-"]
        assert primer.direction in ["forward", "reverse"]
        assert primer.amplicon_id is not None
        assert len(primer.sequence) == primer.length

        # Check valid nucleotides
        valid_chars = set("ATCGRYSWKMBDHVNatcgryswkmbdhvn")
        assert set(primer.sequence).issubset(valid_chars)

    def test_amplicon_structure(self, parser_test_data):
        """Test amplicon structure consistency."""
        format_name = parser_test_data["format"]
        file_path = parser_test_data["file"]

        parser = parser_registry.get_parser(format_name)
        amplicons = parser.parse(file_path, "TEST")

        for amplicon in amplicons:
            # Each amplicon should have primer pairs
            pairs = amplicon.get_primer_pairs()
            assert len(pairs) >= 1

            for fwd, rev in pairs:
                assert fwd.direction == "forward"
                assert rev.direction == "reverse"
                assert fwd.strand == "+"
                assert rev.strand == "-"


class TestOutputConsistency:
    """Test output format consistency across all parsers."""

    def test_all_output_formats(self, parser_test_data, temp_output_dir):
        """Test that all parsers can produce all output formats."""
        file_path = parser_test_data["file"]
        prefix = parser_test_data["prefix"]
        expected_amplicons = parser_test_data["expected_amplicons"]
        expected_primers = parser_test_data["expected_primers"]

        output_files = convert_primers(
            input_file=file_path,
            output_dir=temp_output_dir,
            output_formats=["artic", "fasta", "sts"],
            prefix=prefix,
        )

        # Verify all formats were created
        assert len(output_files) == 3
        for format_name in ["artic", "fasta", "sts"]:
            assert format_name in output_files
            assert output_files[format_name].exists()
            assert output_files[format_name].stat().st_size > 0

        # Validate specific formats
        self._validate_artic_output(output_files["artic"], expected_primers)
        self._validate_fasta_output(output_files["fasta"], expected_primers)
        self._validate_sts_output(output_files["sts"], expected_amplicons)

    def _validate_artic_output(self, file_path: Path, expected_primers: int):
        """Validate ARTIC BED format output."""
        content = file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line.strip()]

        assert len(lines) == expected_primers

        for line in lines:
            parts = line.split("\t")
            assert len(parts) == 7

            # Basic format validation
            assert parts[0]  # chromosome/reference
            start, end = int(parts[1]), int(parts[2])
            assert start != end
            assert "_LEFT_" in parts[3] or "_RIGHT_" in parts[3]  # name
            assert int(parts[4]) >= 0  # pool
            assert parts[5] in ["+", "-"]  # strand
            assert len(parts[6]) > 0  # sequence

    def _validate_fasta_output(self, file_path: Path, expected_primers: int):
        """Validate FASTA format output."""
        content = file_path.read_text()
        header_count = content.count(">")
        assert header_count == expected_primers

        lines = content.strip().split("\n")
        for i in range(0, len(lines), 2):
            if i < len(lines):
                assert lines[i].startswith(">")
                if i + 1 < len(lines):
                    seq = lines[i + 1]
                    assert len(seq) > 0
                    assert all(c.upper() in "ATCGRYSWKMBDHVN" for c in seq)

    def _validate_sts_output(self, file_path: Path, expected_amplicons: int):
        """Validate STS format output."""
        content = file_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == expected_amplicons + 1  # header + amplicons

        header = lines[0].split("\t")
        assert header == ["NAME", "FORWARD", "REVERSE"]

        for line in lines[1:]:
            parts = line.split("\t")
            assert len(parts) == 3
            assert all(part.strip() for part in parts)


class TestCrossParserCompatibility:
    """Test compatibility and consistency across all parsers."""

    def test_registry_completeness(self):
        """Test that all expected parsers and writers are registered."""
        # Check parsers
        expected_parsers = ["varvamp", "artic", "olivar"]
        registered_parsers = parser_registry.list_formats()
        for parser in expected_parsers:
            assert parser in registered_parsers

        # Check writers
        expected_writers = ["artic", "fasta", "sts", "varvamp", "olivar"]
        registered_writers = writer_registry.list_formats()
        for writer in expected_writers:
            assert writer in registered_writers

    def test_consistent_conversion_workflow(self, temp_output_dir):
        """Test that conversion workflow is consistent across all parsers."""
        test_files = [
            (
                "varvamp",
                Path(__file__).parent / "test_data" / "legacy" / "ASFV_long" / "primers.tsv",
            ),
            ("artic", Path(__file__).parent / "test_data" / "legacy" / "ASFV.scheme.bed"),
            (
                "olivar",
                Path(__file__).parent
                / "test_data"
                / "legacy"
                / "olivar_examples"
                / "olivar-design.csv",
            ),
        ]

        successful_conversions = 0

        for format_name, file_path in test_files:
            if not file_path.exists():
                continue

            try:
                output_files = convert_primers(
                    input_file=file_path,
                    output_dir=temp_output_dir / format_name,
                    output_formats=[
                        "fasta"
                    ],  # Use simplest format for compatibility test
                    prefix=f"TEST_{format_name.upper()}",
                )

                assert "fasta" in output_files
                assert output_files["fasta"].exists()
                successful_conversions += 1

            except Exception as e:
                pytest.fail(f"Conversion failed for {format_name}: {e}")

        # At least one conversion should succeed
        assert successful_conversions >= 1

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across parsers."""
        # Test with non-existent file
        non_existent = Path("does_not_exist.txt")

        for format_name in ["varvamp", "artic", "olivar"]:
            parser = parser_registry.get_parser(format_name)
            assert parser.validate_file(non_existent) is False

    @pytest.mark.integration
    def test_end_to_end_workflow(self, parser_test_data, temp_output_dir, test_config):
        """Test complete end-to-end workflow."""
        file_path = parser_test_data["file"]
        parser_test_data["format"]
        prefix = parser_test_data["prefix"]

        # Create converter with test config
        converter = PrimerConverter(test_config)

        # Run conversion
        output_files = converter.convert(
            input_file=file_path,
            output_dir=temp_output_dir,
            output_formats=["artic", "fasta", "sts"],
            prefix=prefix,
        )

        # Verify results
        assert len(output_files) == 3
        for output_file in output_files.values():
            assert output_file.exists()
            assert output_file.stat().st_size > 0


class TestDataStructures:
    """Test core data structures."""

    def test_primer_data_creation(self, sample_primer_data):
        """Test PrimerData creation and properties."""
        primer = sample_primer_data[0]

        assert primer.name == "test_primer_F"
        assert primer.length == 20
        assert primer.artic_name == "test_ref_1_LEFT_0"

    def test_amplicon_data_creation(self, sample_amplicon_data):
        """Test AmpliconData creation and properties."""
        amplicon = sample_amplicon_data

        assert len(amplicon.primers) == 2
        assert len(amplicon.forward_primers) == 1
        assert len(amplicon.reverse_primers) == 1
        assert len(amplicon.get_primer_pairs()) == 1


class TestConfiguration:
    """Test configuration consistency."""

    def test_default_config(self, test_config):
        """Test that test configuration is valid."""
        issues = test_config.validate()
        assert len(issues) == 0

    def test_config_with_converter(self, test_config):
        """Test configuration integration with converter."""
        converter = PrimerConverter(test_config)
        assert converter.config.validate_sequences is True
        assert converter.config.force_overwrite is True


# Pytest collection hooks for better test organization
def pytest_generate_tests(metafunc):
    """Generate parametrized tests dynamically."""
    if "format_specific_test" in metafunc.fixturenames:
        formats = ["varvamp", "artic", "olivar"]
        metafunc.parametrize("format_specific_test", formats)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
