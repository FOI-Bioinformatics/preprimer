"""
Comprehensive tests for the OlivarWriter class.

Tests all functionality of the Olivar CSV format writer including
basic writing, validation, metadata handling, and edge cases.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.olivar_writer import OlivarWriter


class TestOlivarWriter:
    """Test the OlivarWriter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.writer = OlivarWriter()

        # Create realistic test data
        self.forward_primer = PrimerData(
            name="test_1_LEFT",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
        )

        self.reverse_primer = PrimerData(
            name="test_1_RIGHT",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amplicon_1",
        )

        self.amplicon = AmpliconData(
            amplicon_id="amplicon_1",
            primers=[self.forward_primer, self.reverse_primer],
            length=116,
            reference_id="test_ref",
        )

        # Create another amplicon for multi-amplicon tests
        self.forward_primer2 = PrimerData(
            name="test_2_LEFT",
            sequence="GGCCGGCCGGCCGGCC",
            start=300,
            stop=316,
            strand="+",
            direction="forward",
            pool=2,
            amplicon_id="amplicon_2",
        )

        self.reverse_primer2 = PrimerData(
            name="test_2_RIGHT",
            sequence="TTAATTAATTAATTAA",
            start=400,
            stop=416,
            strand="-",
            direction="reverse",
            pool=2,
            amplicon_id="amplicon_2",
        )

        self.amplicon2 = AmpliconData(
            amplicon_id="amplicon_2",
            primers=[self.forward_primer2, self.reverse_primer2],
            length=116,
            reference_id="test_ref",
        )

    def test_format_name(self):
        """Test format_name class method."""
        assert OlivarWriter.format_name() == "olivar"

    def test_file_extension(self):
        """Test file_extension class method."""
        assert OlivarWriter.file_extension() == ".csv"

    def test_description_property(self):
        """Test description property."""
        description = self.writer.description
        assert isinstance(description, str)
        assert "Olivar" in description
        assert "comma-separated" in description

    def test_write_single_amplicon(self):
        """Test writing a single amplicon to Olivar format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write([self.amplicon], output_path)

            assert result_path == output_path
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                assert row["amplicon_id"] == "amplicon_1"
                assert row["chrom"] == "ref"  # default
                assert row["pool"] == "1"
                assert row["start"] == "100"  # min of primer starts
                assert row["end"] == "216"  # max of primer stops
                assert row["fP"] == "ATCGATCGATCGATCG"
                assert row["rP"] == "CGTAGCTAGCTAGCTA"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_multiple_amplicons(self):
        """Test writing multiple amplicons to Olivar format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            amplicons = [self.amplicon, self.amplicon2]
            result_path = self.writer.write(amplicons, output_path)

            assert result_path == output_path
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2

                # Check first amplicon
                row1 = rows[0]
                assert row1["amplicon_id"] == "amplicon_1"
                assert row1["pool"] == "1"

                # Check second amplicon
                row2 = rows[1]
                assert row2["amplicon_id"] == "amplicon_2"
                assert row2["pool"] == "2"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_prefix(self):
        """Test writing with amplicon name prefix."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write(
                [self.amplicon], output_path, prefix="test_scheme"
            )

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["amplicon_id"] == "test_scheme_amplicon_1"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_custom_chrom_name(self):
        """Test writing with custom chromosome name."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write(
                [self.amplicon], output_path, chrom_name="NC_012920.1"
            )

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["chrom"] == "NC_012920.1"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_reference_name_kwarg(self):
        """Test writing with reference_name kwarg."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write(
                [self.amplicon], output_path, reference_name="test_reference"
            )

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["chrom"] == "test_reference"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_creates_output_directory(self):
        """Test that write creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.csv"

            # Directory shouldn't exist initially
            assert not output_path.parent.exists()

            result_path = self.writer.write([self.amplicon], output_path)

            # Directory should be created
            assert output_path.parent.exists()
            assert output_path.exists()

    def test_write_empty_amplicons_list(self):
        """Test writing empty amplicons list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write([], output_path)

            assert result_path == output_path
            assert output_path.exists()

            # File should exist but be empty (no header or rows)
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == ""

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_amplicon_missing_forward_primer(self):
        """Test writing amplicon with missing forward primer."""
        # Create amplicon with only reverse primer
        amplicon_no_forward = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[self.reverse_primer],
            length=100,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write([amplicon_no_forward], output_path)

            # Should create empty file since amplicon is skipped
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == ""

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_amplicon_missing_reverse_primer(self):
        """Test writing amplicon with missing reverse primer."""
        # Create amplicon with only forward primer
        amplicon_no_reverse = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[self.forward_primer],
            length=100,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write([amplicon_no_reverse], output_path)

            # Should create empty file since amplicon is skipped
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == ""

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_primers_with_none_pool(self):
        """Test writing primers where pools are None."""
        # Create primers with None pools
        forward_no_pool = PrimerData(
            name="test_LEFT",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=None,
            amplicon_id="test_amplicon",
        )

        reverse_no_pool = PrimerData(
            name="test_RIGHT",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=None,
            amplicon_id="test_amplicon",
        )

        amplicon_no_pool = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[forward_no_pool, reverse_no_pool],
            length=116,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write([amplicon_no_pool], output_path)

            # Verify default pool is used
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["pool"] == "1"  # default pool

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_valid_file(self):
        """Test validate_output with valid Olivar file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # First create a valid file
            self.writer.write([self.amplicon], output_path)

            # Then validate it
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is True

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_missing_file(self):
        """Test validate_output with non-existent file."""
        non_existent_path = Path("/non/existent/file.csv")
        is_valid = self.writer.validate_output(non_existent_path)
        assert is_valid is False

    def test_validate_output_missing_required_columns(self):
        """Test validate_output with missing required columns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create CSV with missing required columns
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["chrom", "start", "end"])
                writer.writeheader()
                writer.writerow({"chrom": "ref", "start": "100", "end": "200"})

            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_empty_file(self):
        """Test validate_output with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create empty file
            with open(output_path, "w", encoding="utf-8") as f:
                pass  # Empty file

            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_no_valid_primers(self):
        """Test validate_output with file that has headers but no valid primer rows."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create CSV with headers but no valid primer data
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["amplicon_id", "fP", "rP"])
                writer.writeheader()
                writer.writerow(
                    {"amplicon_id": "test", "fP": "", "rP": ""}
                )  # Empty primers

            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_malformed_csv(self):
        """Test validate_output with malformed CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create malformed CSV
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("this is not a valid CSV file\nwith random content")

            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_get_output_info(self):
        """Test get_output_info method."""
        info = self.writer.get_output_info()

        assert isinstance(info, dict)
        assert info["format"] == "olivar"
        assert info["extension"] == ".csv"
        assert "description" in info
        assert "use_case" in info
        assert "columns" in info
        assert "separator" in info
        assert "coordinate_system" in info
        assert "layout" in info

        # Check specific content
        assert "Olivar" in info["use_case"]
        assert "comma" in info["separator"]
        assert "amplicon_id" in info["columns"]
        assert "fP" in info["columns"]
        assert "rP" in info["columns"]

    def test_write_with_metadata_basic(self):
        """Test write_with_metadata method with basic functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            metadata = {"chrom_name": "custom_chrom"}
            result_path = self.writer.write_with_metadata(
                [self.amplicon], output_path, metadata=metadata
            )

            assert result_path == output_path
            assert output_path.exists()

            # Verify CSV content includes metadata
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                # Check basic fields
                assert row["amplicon_id"] == "amplicon_1"
                assert row["chrom"] == "custom_chrom"

                # Check metadata fields added
                assert "amplicon_length" in row
                assert "forward_primer_length" in row
                assert "reverse_primer_length" in row

                assert row["amplicon_length"] == "116"  # end - start = 216 - 100
                assert row["forward_primer_length"] == "16"
                assert row["reverse_primer_length"] == "16"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_metadata_no_metadata(self):
        """Test write_with_metadata with None metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write_with_metadata(
                [self.amplicon], output_path, metadata=None
            )

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                # Should still have basic amplicon_length fields
                assert row["chrom"] == "ref"  # default
                assert "amplicon_length" in row

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_metadata_additional_fields(self):
        """Test write_with_metadata with additional custom metadata."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            metadata = {
                "reference_name": "mt_genome",
                "scheme_version": "v1.0",
                "design_tool": "olivar",
                "amplicon_id": "should_not_overwrite",  # Should not overwrite existing field
            }

            result_path = self.writer.write_with_metadata(
                [self.amplicon], output_path, metadata=metadata
            )

            # Verify CSV content includes custom metadata
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                # Original field should not be overwritten
                assert row["amplicon_id"] == "amplicon_1"

                # Custom metadata should be added
                assert row["chrom"] == "mt_genome"  # reference_name used for chrom
                assert row["scheme_version"] == "v1.0"
                assert row["design_tool"] == "olivar"

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_metadata_creates_directory(self):
        """Test write_with_metadata creates output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.csv"

            # Directory shouldn't exist initially
            assert not output_path.parent.exists()

            result_path = self.writer.write_with_metadata([self.amplicon], output_path)

            # Directory should be created
            assert output_path.parent.exists()
            assert output_path.exists()

    def test_write_with_metadata_empty_amplicons(self):
        """Test write_with_metadata with empty amplicons list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write_with_metadata([], output_path)

            assert result_path == output_path
            assert output_path.exists()

            # File should exist but be empty
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == ""

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_with_metadata_skip_incomplete_amplicons(self):
        """Test write_with_metadata skips amplicons without both primer types."""
        # Create amplicon with only forward primer
        amplicon_incomplete = AmpliconData(
            amplicon_id="incomplete",
            primers=[self.forward_primer],
            length=100,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            result_path = self.writer.write_with_metadata(
                [amplicon_incomplete], output_path, metadata={"test": "value"}
            )

            # Should create empty file since amplicon is skipped
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert content == ""

        finally:
            if output_path.exists():
                output_path.unlink()


class TestOlivarWriterIntegration:
    """Integration tests for OlivarWriter with realistic data."""

    def test_round_trip_compatibility(self):
        """Test that output can be used as input to Olivar parser."""
        writer = OlivarWriter()

        # Create complex test data
        primers = []
        amplicons = []

        for i in range(3):
            forward = PrimerData(
                name=f"amp_{i}_LEFT",
                sequence=f"ATCG" * (4 + i),
                start=100 + i * 200,
                stop=116 + i * 200,
                strand="+",
                direction="forward",
                pool=(i % 2) + 1,
                amplicon_id=f"amplicon_{i}",
            )

            reverse = PrimerData(
                name=f"amp_{i}_RIGHT",
                sequence=f"CGTA" * (4 + i),
                start=200 + i * 200,
                stop=216 + i * 200,
                strand="-",
                direction="reverse",
                pool=(i % 2) + 1,
                amplicon_id=f"amplicon_{i}",
            )

            amplicon = AmpliconData(
                amplicon_id=f"amplicon_{i}",
                primers=[forward, reverse],
                length=116,
                reference_id="test_genome",
            )

            amplicons.append(amplicon)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Write data
            result_path = writer.write(amplicons, output_path, prefix="test_scheme")

            # Verify comprehensive output
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3

                for i, row in enumerate(rows):
                    assert row["amplicon_id"] == f"test_scheme_amplicon_{i}"
                    assert row["pool"] == str((i % 2) + 1)
                    assert len(row["fP"]) == 16 + i * 4  # Sequence length
                    assert len(row["rP"]) == 16 + i * 4
                    assert int(row["start"]) < int(row["end"])

            # Validate output
            assert writer.validate_output(output_path) is True

        finally:
            if output_path.exists():
                output_path.unlink()
