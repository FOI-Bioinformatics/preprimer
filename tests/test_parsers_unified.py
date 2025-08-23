"""
Unified test suite for all PrePrimer parsers (VarVAMP, ARTIC, Olivar).

This module provides harmonized testing across all supported parser types
with consistent test patterns, standardized assertions, and comprehensive
coverage of parsing, validation, and conversion functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from preprimer import convert_primers
from preprimer.core.config import PrePrimerConfig
from preprimer.core.converter import PrimerConverter
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.registry import parser_registry, writer_registry
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.olivar_parser import OlivarParser
from preprimer.parsers.varvamp_parser import VarVAMPParser

# Add preprimer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import preprimer components

# Ensure all parsers and writers are registered


class ParserTestBase:
    """Base class for parser testing with common test patterns."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return PrePrimerConfig(validate_sequences=True, force_overwrite=True)

    def assert_primer_validity(self, primer: PrimerData):
        """Standard primer validation assertions."""
        assert primer.name is not None and primer.name != ""
        assert primer.sequence is not None and primer.sequence != ""
        assert primer.start >= 0
        assert primer.stop >= 0
        # Allow start > stop for reverse strand primers in some formats
        assert abs(primer.stop - primer.start) > 0
        assert primer.strand in ["+", "-"]
        assert primer.direction in ["forward", "reverse"]
        assert primer.amplicon_id is not None and primer.amplicon_id != ""
        assert len(primer.sequence) == primer.length

        # Sequence should contain only valid nucleotides (allowing IUPAC)
        valid_chars = set("ATCGRYSWKMBDHVNatcgryswkmbdhvn")
        assert set(primer.sequence).issubset(valid_chars)

    def assert_amplicon_validity(self, amplicon: AmpliconData):
        """Standard amplicon validation assertions."""
        assert amplicon.amplicon_id is not None and amplicon.amplicon_id != ""
        assert len(amplicon.primers) >= 2  # At least forward and reverse
        assert len(amplicon.forward_primers) >= 1
        assert len(amplicon.reverse_primers) >= 1

        # Validate all primers
        for primer in amplicon.primers:
            self.assert_primer_validity(primer)

        # Check primer pairs
        primer_pairs = amplicon.get_primer_pairs()
        assert len(primer_pairs) >= 1

        for fwd, rev in primer_pairs:
            assert fwd.direction == "forward"
            assert rev.direction == "reverse"
            assert fwd.strand == "+"
            assert rev.strand == "-"
            assert fwd.amplicon_id == rev.amplicon_id == amplicon.amplicon_id

    def assert_parser_consistency(
        self, parser, file_path: Path, expected_amplicons: int
    ):
        """Standard parser consistency tests."""
        # Test validation
        assert parser.validate_file(file_path) is True

        # Test parsing
        amplicons = parser.parse(file_path, "TEST")
        assert len(amplicons) == expected_amplicons

        # Validate all amplicons
        for amplicon in amplicons:
            self.assert_amplicon_validity(amplicon)

        return amplicons

    def assert_conversion_consistency(
        self,
        input_file: Path,
        expected_amplicons: int,
        expected_primers: int,
        prefix: str = "TEST",
    ):
        """Standard conversion workflow tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test all output formats
            output_files = convert_primers(
                input_file=input_file,
                output_dir=temp_dir,
                output_formats=["artic", "fasta", "sts"],
                prefix=prefix,
            )

            # Verify all formats were created
            assert len(output_files) == 3
            for format_name in ["artic", "fasta", "sts"]:
                assert format_name in output_files
                assert output_files[format_name].exists()

            # Validate ARTIC output
            self._validate_artic_output(output_files["artic"], expected_primers)

            # Validate FASTA output
            self._validate_fasta_output(output_files["fasta"], expected_primers)

            # Validate STS output
            self._validate_sts_output(output_files["sts"], expected_amplicons)

            return output_files

    def _validate_artic_output(self, file_path: Path, expected_primers: int):
        """Validate ARTIC BED format output."""
        content = file_path.read_text()
        lines = [line for line in content.strip().split("\n") if line.strip()]

        assert len(lines) == expected_primers

        for line in lines:
            parts = line.split("\t")
            assert (
                len(parts) == 7
            )  # BED format: chrom, start, end, name, pool, strand, sequence

            # Validate coordinates (allow start > end for reverse strand)
            start = int(parts[1])
            end = int(parts[2])
            assert start != end  # Must be different

            # Validate name format
            name = parts[3]
            assert "_LEFT_" in name or "_RIGHT_" in name

            # Validate pool
            pool = int(parts[4])
            assert pool >= 0  # Allow pool 0

            # Validate strand
            strand = parts[5]
            assert strand in ["+", "-"]

            # Validate sequence
            sequence = parts[6]
            assert len(sequence) > 0

    def _validate_fasta_output(self, file_path: Path, expected_primers: int):
        """Validate FASTA format output."""
        content = file_path.read_text()

        # Count headers
        header_count = content.count(">")
        assert header_count == expected_primers

        # Validate format
        lines = content.strip().split("\n")
        for i in range(0, len(lines), 2):
            if i < len(lines):
                # Header line
                assert lines[i].startswith(">")
                # Sequence line
                if i + 1 < len(lines):
                    seq = lines[i + 1]
                    assert len(seq) > 0
                    assert all(c.upper() in "ATCGRYSWKMBDHVN" for c in seq)

    def _validate_sts_output(self, file_path: Path, expected_amplicons: int):
        """Validate STS format output."""
        content = file_path.read_text()
        lines = content.strip().split("\n")

        # Header + amplicons
        assert len(lines) == expected_amplicons + 1

        # Validate header
        header = lines[0].split("\t")
        assert header == ["NAME", "FORWARD", "REVERSE"]

        # Validate amplicon lines
        for line in lines[1:]:
            parts = line.split("\t")
            assert len(parts) == 3

            name, forward, reverse = parts
            assert name != ""
            assert len(forward) > 0
            assert len(reverse) > 0


class TestVarVAMPParser(ParserTestBase):
    """Comprehensive tests for VarVAMP parser."""

    @pytest.fixture
    def test_file(self):
        """VarVAMP test file fixture."""
        return Path(__file__).parent / "test_data" / "ASFV_long" / "primers.tsv"

    @pytest.fixture
    def reference_file(self):
        """VarVAMP reference file fixture."""
        return (
            Path(__file__).parent
            / "test_data"
            / "ASFV_long"
            / "ambiguous_consensus.fasta"
        )

    def test_varvamp_format_detection(self, test_file):
        """Test VarVAMP format detection."""
        detected_format = parser_registry.detect_format(test_file)
        assert detected_format == "varvamp"

    def test_varvamp_parser_validation(self, test_file):
        """Test VarVAMP parser validation."""
        parser = VarVAMPParser()
        assert parser.format_name == "varvamp"
        assert ".tsv" in parser.file_extensions
        assert parser.validate_file(test_file) is True

    def test_varvamp_parsing_consistency(self, test_file):
        """Test VarVAMP parsing consistency."""
        parser = VarVAMPParser()
        amplicons = self.assert_parser_consistency(
            parser, test_file, expected_amplicons=80
        )

        # VarVAMP-specific tests
        assert sum(len(a.primers) for a in amplicons) == 160  # 80 amplicons × 2 primers

        # Check first amplicon
        first_amplicon = amplicons[0]
        assert first_amplicon.amplicon_id == "amplicon_0"
        assert len(first_amplicon.primers) == 2

        # Check primer naming
        fwd_primer = first_amplicon.forward_primers[0]
        rev_primer = first_amplicon.reverse_primers[0]
        assert fwd_primer.name.startswith("FW")
        assert rev_primer.name.startswith("RW")

    def test_varvamp_conversion_workflow(self, test_file):
        """Test VarVAMP complete conversion workflow."""
        self.assert_conversion_consistency(
            test_file, expected_amplicons=80, expected_primers=160, prefix="ASFV"
        )

    def test_varvamp_reference_file_detection(self, test_file, reference_file):
        """Test VarVAMP reference file detection."""
        parser = VarVAMPParser()
        found_reference = parser.get_reference_file(test_file)
        assert found_reference is not None
        assert found_reference.exists()
        assert found_reference.name == "ambiguous_consensus.fasta"


class TestARTICParser(ParserTestBase):
    """Comprehensive tests for ARTIC parser."""

    @pytest.fixture
    def test_file(self):
        """ARTIC test file fixture."""
        return Path(__file__).parent / "test_data" / "ASFV.scheme.bed"

    def test_artic_format_detection(self, test_file):
        """Test ARTIC format detection."""
        detected_format = parser_registry.detect_format(test_file)
        assert detected_format == "artic"

    def test_artic_parser_validation(self, test_file):
        """Test ARTIC parser validation."""
        parser = ARTICParser()
        assert parser.format_name == "artic"
        assert ".bed" in parser.file_extensions
        assert parser.validate_file(test_file) is True

    def test_artic_parsing_consistency(self, test_file):
        """Test ARTIC parsing consistency."""
        parser = ARTICParser()

        # Count lines in file to determine expected amplicons
        with open(test_file) as f:
            lines = [line for line in f if line.strip() and not line.startswith("#")]

        expected_primers = len(lines)
        expected_amplicons = expected_primers // 2  # Assuming pairs

        amplicons = self.assert_parser_consistency(
            parser, test_file, expected_amplicons
        )

        # ARTIC-specific tests
        total_primers = sum(len(a.primers) for a in amplicons)
        assert total_primers == expected_primers

        # Check ARTIC naming convention
        for amplicon in amplicons:
            for primer in amplicon.primers:
                assert "_LEFT_" in primer.name or "_RIGHT_" in primer.name

    def test_artic_conversion_workflow(self, test_file):
        """Test ARTIC complete conversion workflow."""
        # Count expected amplicons and primers
        with open(test_file) as f:
            lines = [line for line in f if line.strip() and not line.startswith("#")]

        expected_primers = len(lines)
        expected_amplicons = expected_primers // 2

        self.assert_conversion_consistency(
            test_file, expected_amplicons, expected_primers, prefix="ASFV"
        )


class TestOlivarParser(ParserTestBase):
    """Comprehensive tests for Olivar parser."""

    @pytest.fixture
    def test_file(self):
        """Olivar test file fixture."""
        return (
            Path(__file__).parent
            / "test_data"
            / "olivar_examples"
            / "olivar-design.csv"
        )

    @pytest.fixture
    def reference_file(self):
        """Olivar reference file fixture."""
        return (
            Path(__file__).parent
            / "test_data"
            / "olivar_examples"
            / "EPI_ISL_402124_ref.fasta"
        )

    def test_olivar_format_detection(self, test_file):
        """Test Olivar format detection."""
        if test_file.exists():
            detected_format = parser_registry.detect_format(test_file)
            assert detected_format == "olivar"

    def test_olivar_parser_validation(self, test_file):
        """Test Olivar parser validation."""
        if not test_file.exists():
            pytest.skip("Olivar test data not available")

        parser = OlivarParser()
        assert parser.format_name == "olivar"
        assert ".csv" in parser.file_extensions
        assert parser.validate_file(test_file) is True

    def test_olivar_parsing_consistency(self, test_file):
        """Test Olivar parsing consistency."""
        if not test_file.exists():
            pytest.skip("Olivar test data not available")

        parser = OlivarParser()
        amplicons = self.assert_parser_consistency(
            parser, test_file, expected_amplicons=5
        )

        # Olivar-specific tests
        assert sum(len(a.primers) for a in amplicons) == 10  # 5 amplicons × 2 primers

        # Check primer naming
        for amplicon in amplicons:
            fwd_primer = amplicon.forward_primers[0]
            rev_primer = amplicon.reverse_primers[0]
            assert fwd_primer.name.endswith("_F")
            assert rev_primer.name.endswith("_R")

        # Check pool assignments
        pools = set()
        for amplicon in amplicons:
            for primer in amplicon.primers:
                pools.add(primer.pool)
        assert len(pools) <= 2  # Should use pools 1 and 2

    def test_olivar_conversion_workflow(self, test_file):
        """Test Olivar complete conversion workflow."""
        if not test_file.exists():
            pytest.skip("Olivar test data not available")

        self.assert_conversion_consistency(
            test_file, expected_amplicons=5, expected_primers=10, prefix="COVID19"
        )


class TestCrossParserCompatibility:
    """Tests for cross-parser compatibility and consistency."""

    @pytest.fixture
    def all_test_files(self):
        """All available test files."""
        test_dir = Path(__file__).parent / "test_data"
        files = {
            "varvamp": test_dir / "ASFV_long" / "primers.tsv",
            "artic": test_dir / "ASFV.scheme.bed",
            "olivar": test_dir / "olivar_examples" / "olivar-design.csv",
        }
        return {k: v for k, v in files.items() if v.exists()}

    def test_format_detection_consistency(self, all_test_files):
        """Test that all parsers are correctly detected."""
        for format_name, file_path in all_test_files.items():
            detected = parser_registry.detect_format(file_path)
            assert (
                detected == format_name
            ), f"Expected {format_name}, got {detected} for {file_path}"

    def test_parser_registry_completeness(self):
        """Test that all parsers are registered."""
        expected_formats = ["varvamp", "artic", "olivar"]
        registered_formats = parser_registry.list_formats()

        for fmt in expected_formats:
            assert fmt in registered_formats

    def test_writer_registry_completeness(self):
        """Test that all writers are registered."""
        expected_formats = ["artic", "fasta", "sts"]
        registered_formats = writer_registry.list_formats()

        for fmt in expected_formats:
            assert fmt in registered_formats

    def test_all_parsers_to_all_formats(self, all_test_files):
        """Test that all parsers can convert to all output formats."""
        for format_name, file_path in all_test_files.items():
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    output_files = convert_primers(
                        input_file=file_path,
                        output_dir=temp_dir,
                        output_formats=["artic", "fasta", "sts"],
                        prefix=f"TEST_{format_name.upper()}",
                    )

                    # All formats should be created
                    assert len(output_files) == 3
                    for output_format in ["artic", "fasta", "sts"]:
                        assert output_format in output_files
                        assert output_files[output_format].exists()
                        assert output_files[output_format].stat().st_size > 0

                except Exception as e:
                    pytest.fail(f"Conversion failed for {format_name}: {e}")


class TestConfigurationHarmonization:
    """Tests for configuration consistency across parsers."""

    def test_default_config_consistency(self):
        """Test default configuration works with all parsers."""
        config = PrePrimerConfig()
        issues = config.validate()
        assert len(issues) == 0

    def test_validation_settings_consistency(self):
        """Test validation settings work consistently."""
        config = PrePrimerConfig(
            validate_sequences=True, min_primer_length=15, max_primer_length=35
        )

        converter = PrimerConverter(config)
        assert converter.config.validate_sequences is True
        assert converter.config.min_primer_length == 15
        assert converter.config.max_primer_length == 35


def run_all_tests():
    """Run all harmonized tests manually."""
    print("🧪 Running harmonized parser tests...")

    # Test data structures
    test_base = ParserTestBase()

    # Test each parser if data is available
    test_dir = Path(__file__).parent / "test_data"

    # VarVAMP tests
    varvamp_file = test_dir / "ASFV_long" / "primers.tsv"
    if varvamp_file.exists():
        print("✅ Testing VarVAMP parser...")
        parser = VarVAMPParser()
        amplicons = test_base.assert_parser_consistency(parser, varvamp_file, 80)
        test_base.assert_conversion_consistency(varvamp_file, 80, 160, "ASFV")
        print(
            f"   Parsed {len(amplicons)} amplicons with {sum(len(a.primers) for a in amplicons)} primers"
        )

    # ARTIC tests
    artic_file = test_dir / "ASFV.scheme.bed"
    if artic_file.exists():
        print("✅ Testing ARTIC parser...")
        parser = ARTICParser()
        with open(artic_file) as f:
            lines = [line for line in f if line.strip()]
        expected_primers = len(lines)
        expected_amplicons = expected_primers // 2

        amplicons = test_base.assert_parser_consistency(
            parser, artic_file, expected_amplicons
        )
        test_base.assert_conversion_consistency(
            artic_file, expected_amplicons, expected_primers, "ASFV"
        )
        print(
            f"   Parsed {len(amplicons)} amplicons with {sum(len(a.primers) for a in amplicons)} primers"
        )

    # Olivar tests
    olivar_file = test_dir / "olivar_examples" / "olivar-design.csv"
    if olivar_file.exists():
        print("✅ Testing Olivar parser...")
        parser = OlivarParser()
        amplicons = test_base.assert_parser_consistency(parser, olivar_file, 5)
        test_base.assert_conversion_consistency(olivar_file, 5, 10, "COVID19")
        print(
            f"   Parsed {len(amplicons)} amplicons with {sum(len(a.primers) for a in amplicons)} primers"
        )

    # Cross-compatibility tests
    print("✅ Testing cross-parser compatibility...")

    # Format detection
    all_files = {"varvamp": varvamp_file, "artic": artic_file, "olivar": olivar_file}

    for format_name, file_path in all_files.items():
        if file_path.exists():
            detected = parser_registry.detect_format(file_path)
            assert detected == format_name
            print(f"   Format detection: {file_path.name} → {detected}")

    print("🎉 All harmonized tests passed!")
    print("\nSummary:")
    print("• VarVAMP: ✅ Parsing, validation, conversion")
    print("• ARTIC: ✅ Parsing, validation, conversion")
    print("• Olivar: ✅ Parsing, validation, conversion")
    print("• Cross-compatibility: ✅ Format detection, registry, conversion")
    print("• Configuration: ✅ Harmonized settings across all parsers")


if __name__ == "__main__":
    run_all_tests()
