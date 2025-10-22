"""
Olivar writer tests using BaseWriterTest framework.

Olivar format is a CSV format for primer schemes with support for
custom chromosome names and metadata.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.olivar_writer import OlivarWriter

from .test_base_writer import BaseWriterTest


class TestOlivarWriter(BaseWriterTest):
    """Olivar writer tests - inherits contract tests from BaseWriterTest."""

    # =========================================================================
    # Configuration - Required by BaseWriterTest
    # =========================================================================

    @property
    def writer_class(self):
        return OlivarWriter

    @property
    def expected_format_name(self):
        return "olivar"

    @property
    def expected_file_extension(self):
        return ".csv"

    def get_test_amplicons(self):
        """Return test amplicons for Olivar tests."""
        # Create realistic test data
        forward_primer = PrimerData(
            name="test_1_LEFT",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
        )

        reverse_primer = PrimerData(
            name="test_1_RIGHT",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amplicon_1",
        )

        amplicon = AmpliconData(
            amplicon_id="amplicon_1",
            primers=[forward_primer, reverse_primer],
            length=116,
            reference_id="test_ref",
        )

        # Create second amplicon for multi-amplicon tests
        forward_primer2 = PrimerData(
            name="test_2_LEFT",
            sequence="GGCCGGCCGGCCGGCC",
            start=300,
            stop=316,
            strand="+",
            direction="forward",
            pool=2,
            amplicon_id="amplicon_2",
        )

        reverse_primer2 = PrimerData(
            name="test_2_RIGHT",
            sequence="TTAATTAATTAATTAA",
            start=400,
            stop=416,
            strand="-",
            direction="reverse",
            pool=2,
            amplicon_id="amplicon_2",
        )

        amplicon2 = AmpliconData(
            amplicon_id="amplicon_2",
            primers=[forward_primer2, reverse_primer2],
            length=116,
            reference_id="test_ref",
        )

        return [amplicon, amplicon2]

    def verify_output_content(self, output_path: Path, amplicons: list):
        """Verify Olivar CSV output content."""
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Olivar writes one row per amplicon
        assert len(rows) == len(amplicons), f"Expected {len(amplicons)} rows, got {len(rows)}"

        # Check required columns exist
        required_columns = [
            "amplicon_id",
            "chrom",
            "pool",
            "start",
            "end",
            "fP",
            "rP",
        ]

        for row in rows:
            for col in required_columns:
                assert col in row, f"Missing required column: {col}"

    # =========================================================================
    # Olivar-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_prefix(self):
        """Olivar writer must handle prefix for amplicon IDs."""
        writer = OlivarWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path, prefix="test_scheme")

            # Verify prefix is applied
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["amplicon_id"] == "test_scheme_amplicon_1"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_custom_chrom_name(self):
        """Olivar writer must handle custom chromosome names."""
        writer = OlivarWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path, chrom_name="NC_012920.1")

            # Verify custom chrom name
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["chrom"] == "NC_012920.1"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_reference_name_kwarg(self):
        """Olivar writer must handle reference_name kwarg (alias for chrom_name)."""
        writer = OlivarWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path, reference_name="custom_ref")

            # Verify reference_name is used as chrom
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["chrom"] == "custom_ref"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_amplicon_missing_forward_primer(self):
        """Olivar writer must handle amplicons with missing forward primer."""
        writer = OlivarWriter()

        # Create amplicon with only reverse primer
        reverse_primer = self.create_test_primer(
            name="test_R",
            sequence="CGTAGCTA",
            start=200,
            stop=208,
            direction="reverse",
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp",
            primers=[reverse_primer],
            length=100,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Should handle gracefully (may log warning)
            writer.write([amplicon], output_path)

            # Verify file exists (even if incomplete)
            assert output_path.exists()

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_amplicon_missing_reverse_primer(self):
        """Olivar writer must handle amplicons with missing reverse primer."""
        writer = OlivarWriter()

        # Create amplicon with only forward primer
        forward_primer = self.create_test_primer(
            name="test_F",
            sequence="ATCGATCG",
            start=100,
            stop=108,
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp",
            primers=[forward_primer],
            length=100,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Should handle gracefully (may log warning)
            writer.write([amplicon], output_path)

            # Verify file exists (even if incomplete)
            assert output_path.exists()

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_primers_with_none_pool(self):
        """Olivar writer must handle primers with None pool (uses default)."""
        writer = OlivarWriter()

        # Create primers with None pool
        forward = PrimerData(
            name="test_F",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=None,  # No pool
            amplicon_id="test_amp",
        )

        reverse = PrimerData(
            name="test_R",
            sequence="CGTAGCTA",
            start=200,
            stop=208,
            strand="-",
            direction="reverse",
            pool=None,  # No pool
            amplicon_id="test_amp",
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp",
            primers=[forward, reverse],
            length=108,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            # Verify default pool is used
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                # Default pool should be set (typically 1 or 0)
                assert rows[0]["pool"] in ["0", "1"]

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_valid_file(self):
        """validate_output() must return True for valid Olivar file."""
        writer = OlivarWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create valid file
            writer.write(amplicons, output_path)

            # Validate it
            is_valid = writer.validate_output(output_path)
            assert is_valid is True

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_missing_file(self):
        """validate_output() must return False for non-existent file."""
        writer = OlivarWriter()
        non_existent_path = Path("/non/existent/file.csv")
        is_valid = writer.validate_output(non_existent_path)
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_missing_required_columns(self):
        """validate_output() must return False for files missing required columns."""
        writer = OlivarWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create CSV with missing required columns
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.DictWriter(csvfile, fieldnames=["amplicon_id", "pool"])
                csv_writer.writeheader()
                csv_writer.writerow({"amplicon_id": "amp1", "pool": "1"})

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_empty_file(self):
        """validate_output() must return False for empty files."""
        writer = OlivarWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create empty file
            with open(output_path, "w", encoding="utf-8") as f:
                pass  # Empty file

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_no_valid_primers(self):
        """validate_output() must return False for files with headers but no data."""
        writer = OlivarWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create CSV with all required headers but no data
            fieldnames = ["amplicon_id", "chrom", "pool", "start", "end", "fP", "rP"]
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                csv_writer.writeheader()
                # No data rows

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_malformed_csv(self):
        """validate_output() must return False for malformed CSV files."""
        writer = OlivarWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create malformed CSV
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("this is not a valid CSV file\nwith random content")

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_get_output_info(self):
        """get_output_info() must return comprehensive format information."""
        writer = OlivarWriter()
        info = writer.get_output_info()

        assert isinstance(info, dict)
        assert "format" in info
        assert "extension" in info
        assert "description" in info

        # Check specific content
        assert "Olivar" in info.get("use_case", "") or "olivar" in info.get("format", "")


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.writer
class TestOlivarWriterIntegration:
    """Olivar writer integration tests for complex scenarios."""

    def test_write_with_metadata(self):
        """Olivar writer must handle metadata correctly."""
        writer = OlivarWriter()

        # Create test amplicons
        forward = PrimerData(
            name="amp1_F",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amp1",
        )

        reverse = PrimerData(
            name="amp1_R",
            sequence="CGTAGCTA",
            start=200,
            stop=208,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amp1",
        )

        amplicon = AmpliconData(
            amplicon_id="amp1",
            primers=[forward, reverse],
            length=108,
            reference_id="test_ref",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.csv"

            # Write with metadata
            metadata = {"scheme_name": "test_scheme", "version": "1.0"}
            writer.write([amplicon], output_path, **metadata)

            # Verify main file exists
            assert output_path.exists()

            # Verify content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["amplicon_id"] == "amp1"

    def test_write_multiple_amplicons_different_pools(self):
        """Olivar writer must handle multiple amplicons with different pools."""
        writer = OlivarWriter()

        amplicons = []
        for i in range(3):
            forward = PrimerData(
                name=f"amp{i}_F",
                sequence=f"{'ATCG' * (4 + i)}",
                start=100 + i * 200,
                stop=116 + i * 200,
                strand="+",
                direction="forward",
                pool=(i % 2) + 1,
                amplicon_id=f"amp{i}",
            )

            reverse = PrimerData(
                name=f"amp{i}_R",
                sequence=f"{'CGTA' * (4 + i)}",
                start=200 + i * 200,
                stop=216 + i * 200,
                strand="-",
                direction="reverse",
                pool=(i % 2) + 1,
                amplicon_id=f"amp{i}",
            )

            amplicon = AmpliconData(
                amplicon_id=f"amp{i}",
                primers=[forward, reverse],
                length=116,
                reference_id="test_ref",
            )
            amplicons.append(amplicon)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            # Verify content
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 3

                # Check pools alternate
                assert rows[0]["pool"] == "1"
                assert rows[1]["pool"] == "2"
                assert rows[2]["pool"] == "1"

            # Validate output
            assert writer.validate_output(output_path) is True

        finally:
            if output_path.exists():
                output_path.unlink()
