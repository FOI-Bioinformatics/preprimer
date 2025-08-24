"""
Test Olivar parser with real example data from Olivar repository.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from preprimer import convert_primers
from preprimer.parsers.olivar_parser import OlivarParser

# Add the preprimer package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import everything needed to ensure registration

# Ensure all parsers and writers are registered


class TestOlivarParserWithRealData:
    """Test Olivar parser using real example data from Olivar repository."""

    @pytest.fixture
    def olivar_csv_file(self):
        """Path to the Olivar design CSV file."""
        return (
            Path(__file__).parent
            / "test_data"
            / "olivar_examples"
            / "olivar-design.csv"
        )

    @pytest.fixture
    def olivar_bed_file(self):
        """Path to the Olivar design BED file."""
        return (
            Path(__file__).parent
            / "test_data"
            / "olivar_examples"
            / "olivar-design.primer.bed"
        )

    @pytest.fixture
    def reference_file(self):
        """Path to the reference FASTA file."""
        return (
            Path(__file__).parent
            / "test_data"
            / "olivar_examples"
            / "EPI_ISL_402124_ref.fasta"
        )

    def test_olivar_csv_validation(self, olivar_csv_file):
        """Test that Olivar CSV file is properly validated."""
        parser = OlivarParser()

        assert olivar_csv_file.exists(), f"Test file not found: {olivar_csv_file}"
        assert parser.validate_file(olivar_csv_file), "Olivar CSV file should be valid"

    def test_olivar_csv_parsing(self, olivar_csv_file):
        """Test parsing of Olivar CSV file."""
        parser = OlivarParser()
        amplicons = parser.parse(olivar_csv_file, "EPI_ISL_402124")

        # Verify basic parsing results
        assert (
            len(amplicons) == 5
        ), f"Expected 5 amplicons, got {
            len(amplicons)}"

        # Check first amplicon
        amp1 = amplicons[0]
        assert amp1.amplicon_id == "EPI_ISL_402124_1"
        assert (
            len(amp1.primers) == 2
        ), "Each amplicon should have 2 primers (forward and reverse)"
        assert len(amp1.forward_primers) == 1
        assert len(amp1.reverse_primers) == 1

        # Verify primer sequences
        fwd_primer = amp1.forward_primers[0]
        rev_primer = amp1.reverse_primers[0]

        assert fwd_primer.sequence == "cggctgcatgcttagtgc"
        assert rev_primer.sequence == "gacctcctccacggagtct"
        assert fwd_primer.start == 100
        assert fwd_primer.stop == 118
        assert rev_primer.start == 360  # end - len(sequence) = 379 - 19 = 360
        assert rev_primer.stop == 379

    def test_olivar_primer_pools(self, olivar_csv_file):
        """Test that primer pools are correctly assigned."""
        parser = OlivarParser()
        amplicons = parser.parse(olivar_csv_file, "EPI_ISL_402124")

        # Check pool assignments match expected values
        expected_pools = [1, 2, 1, 2, 1]
        for i, amplicon in enumerate(amplicons):
            for primer in amplicon.primers:
                assert (
                    primer.pool == expected_pools[i]
                ), f"Amplicon {i + 1} should be in pool {expected_pools[i]}"

    def test_olivar_primer_naming(self, olivar_csv_file):
        """Test primer naming conventions."""
        parser = OlivarParser()
        amplicons = parser.parse(olivar_csv_file, "EPI_ISL_402124")

        # Check ARTIC naming for first amplicon
        amp1 = amplicons[0]
        fwd_primer = amp1.forward_primers[0]
        rev_primer = amp1.reverse_primers[0]

        assert fwd_primer.artic_name == "EPI_ISL_402124_1_LEFT_0"
        assert rev_primer.artic_name == "EPI_ISL_402124_1_RIGHT_0"

    def test_olivar_conversion_to_artic(self, olivar_csv_file, reference_file):
        """Test conversion of Olivar data to ARTIC format."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = convert_primers(
                input_file=olivar_csv_file,
                output_dir=temp_dir,
                output_formats=["artic"],
                prefix="EPI_ISL_402124",
                reference_file=reference_file,
            )

            # Check that ARTIC file was created
            assert "artic" in output_files
            artic_file = output_files["artic"]
            assert artic_file.exists()

            # Read and validate ARTIC content
            content = artic_file.read_text()
            lines = content.strip().split("\n")

            # Should have 10 lines (5 amplicons × 2 primers each)
            assert len(lines) == 10

            # Check first primer line
            first_line = lines[0].split("\t")
            assert (
                len(first_line) == 7
            )  # BED format: chrom, start, end, name, pool, strand, sequence
            assert first_line[0] == "EPI_ISL_402124"  # reference
            assert first_line[1] == "100"  # start
            assert first_line[2] == "118"  # end
            assert first_line[3] == "EPI_ISL_402124_1_LEFT_0"  # name
            assert first_line[4] == "1"  # pool
            assert first_line[5] == "+"  # strand
            assert first_line[6] == "cggctgcatgcttagtgc"  # sequence

    def test_olivar_conversion_to_fasta(self, olivar_csv_file):
        """Test conversion of Olivar data to FASTA format."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = convert_primers(
                input_file=olivar_csv_file,
                output_dir=temp_dir,
                output_formats=["fasta"],
                prefix="EPI_ISL_402124",
            )

            # Check that FASTA file was created
            assert "fasta" in output_files
            fasta_file = output_files["fasta"]
            assert fasta_file.exists()

            # Read and validate FASTA content
            content = fasta_file.read_text()

            # Should contain 10 primer sequences (5 amplicons × 2 primers each)
            assert content.count(">") == 10
            assert "EPI_ISL_402124_1_LEFT_0" in content
            assert "EPI_ISL_402124_1_RIGHT_0" in content
            assert "cggctgcatgcttagtgc" in content
            assert "gacctcctccacggagtct" in content

    def test_olivar_conversion_to_sts(self, olivar_csv_file):
        """Test conversion of Olivar data to STS format."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = convert_primers(
                input_file=olivar_csv_file,
                output_dir=temp_dir,
                output_formats=["sts"],
                prefix="EPI_ISL_402124",
            )

            # Check that STS file was created
            assert "sts" in output_files
            sts_file = output_files["sts"]
            assert sts_file.exists()

            # Read and validate STS content
            content = sts_file.read_text()
            lines = content.strip().split("\n")

            # Should have header + 5 amplicons
            assert len(lines) == 6
            assert lines[0] == "NAME\tFORWARD\tREVERSE"

            # Check first amplicon
            first_amplicon = lines[1].split("\t")
            assert first_amplicon[0] == "EPI_ISL_402124_1"
            assert first_amplicon[1] == "cggctgcatgcttagtgc"
            assert first_amplicon[2] == "gacctcctccacggagtct"

    def test_olivar_multi_format_conversion(self, olivar_csv_file, reference_file):
        """Test conversion to multiple formats simultaneously."""

        with tempfile.TemporaryDirectory() as temp_dir:
            output_files = convert_primers(
                input_file=olivar_csv_file,
                output_dir=temp_dir,
                output_formats=["artic", "fasta", "sts"],
                prefix="EPI_ISL_402124",
                reference_file=reference_file,
            )

            # Check all formats were created
            assert len(output_files) == 3
            assert "artic" in output_files
            assert "fasta" in output_files
            assert "sts" in output_files

            for format_name, file_path in output_files.items():
                assert file_path.exists(), f"Output file for {format_name} should exist"


def test_olivar_file_detection():
    """Test that Olivar files are properly detected."""
    from preprimer.core.registry import parser_registry

    olivar_file = (
        Path(__file__).parent / "test_data" / "olivar_examples" / "olivar-design.csv"
    )

    if olivar_file.exists():
        detected_format = parser_registry.detect_format(olivar_file)
        assert (
            detected_format == "olivar"
        ), f"Expected 'olivar', got '{detected_format}'"


if __name__ == "__main__":
    # Run basic tests manually
    test_dir = Path(__file__).parent / "test_data" / "olivar_examples"
    olivar_file = test_dir / "olivar-design.csv"

    if not olivar_file.exists():
        print("❌ Test data not found. Please run the test creation first.")
        exit(1)

    print("🧪 Testing Olivar parser with real data...")

    # Test validation
    parser = OlivarParser()
    if parser.validate_file(olivar_file):
        print("✅ Olivar file validation passed")
    else:
        print("❌ Olivar file validation failed")
        exit(1)

    # Test parsing
    amplicons = parser.parse(olivar_file, "EPI_ISL_402124")
    print(
        f"✅ Parsed {len(amplicons)} amplicons with {sum(len(a.primers) for a in amplicons)} primers"
    )

    # Test conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            output_files = convert_primers(
                input_file=olivar_file,
                output_dir=temp_dir,
                output_formats=["artic", "fasta", "sts"],
                prefix="TEST_OLIVAR",
            )
            print(f"✅ Successfully converted to {len(output_files)} formats")
            for format_name in output_files:
                print(f"   - {format_name}: {output_files[format_name]}")
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            exit(1)

    print("🎉 All Olivar tests passed!")
