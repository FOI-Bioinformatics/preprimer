"""
VarVAMP writer tests using BaseWriterTest framework.

VarVAMP format is a 13-column TSV format with GC content and Tm calculations.
Supports degenerate primers and optional pool assignments.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.varvamp_writer import VarVAMPWriter

from .test_base_writer import BaseWriterTest


class TestVarVAMPWriter(BaseWriterTest):
    """VarVAMP writer tests - inherits contract tests from BaseWriterTest."""

    # =========================================================================
    # Configuration - Required by BaseWriterTest
    # =========================================================================

    @property
    def writer_class(self):
        return VarVAMPWriter

    @property
    def expected_format_name(self):
        return "varvamp"

    @property
    def expected_file_extension(self):
        return ".tsv"

    def get_test_amplicons(self):
        """Return test amplicons for VarVAMP tests."""
        # Create realistic test data
        forward_primer = PrimerData(
            name="test_1_LEFT",
            sequence="ATCGATCGATCGATCG",  # 50% GC content
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
            gc_content=0.5,
            tm=58.5,
            score=95.2,
        )

        reverse_primer = PrimerData(
            name="test_1_RIGHT",
            sequence="GGCCGGCCGGCCGGCC",  # 100% GC content
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amplicon_1",
            gc_content=1.0,
            tm=72.1,
            score=88.7,
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
        """Verify VarVAMP TSV output content."""
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows = list(reader)

        # Count expected primers
        expected_primers = sum(len(amp.primers) for amp in amplicons)
        assert (
            len(rows) == expected_primers
        ), f"Expected {expected_primers} primers, got {len(rows)}"

        # Check required columns exist
        required_columns = [
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

        for row in rows:
            for col in required_columns:
                assert col in row, f"Missing required column: {col}"
                assert row[col], f"Column {col} should not be empty"

    # =========================================================================
    # VarVAMP-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_amplicon_with_no_length(self):
        """VarVAMP writer must handle amplicons with None length (uses default 400)."""
        writer = VarVAMPWriter()

        # Create amplicon with no length
        forward_primer = self.create_test_primer(
            name="test_primer",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
        )

        reverse_primer = self.create_test_primer(
            name="test_primer_R",
            sequence="GGCCGGCCGGCCGGCC",
            start=200,
            stop=216,
            direction="reverse",
        )

        amplicon_no_length = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[forward_primer, reverse_primer],
            length=None,  # No length
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon_no_length], output_path)

            # Verify default amplicon length is used
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

                assert len(rows) == 2
                assert (
                    rows[0]["amplicon_length"] == "400"
                ), "Should use default length 400"
                assert (
                    rows[1]["amplicon_length"] == "400"
                ), "Should use default length 400"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_primers_with_no_pool(self):
        """VarVAMP writer must handle primers with None pool (uses default 1)."""
        writer = VarVAMPWriter()

        # Create primer with None pool
        primer_no_pool = PrimerData(
            name="test_no_pool",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=None,  # No pool
            amplicon_id="test_amplicon",
        )

        amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[primer_no_pool],
            length=116,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            # Verify default pool is used
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

                assert len(rows) == 1
                assert rows[0]["pool"] == "1", "Should use default pool 1"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_primers_with_missing_optional_attributes(self):
        """VarVAMP writer must handle primers lacking tm and score (uses defaults)."""
        writer = VarVAMPWriter()

        # Create primer without optional attributes
        basic_primer = PrimerData(
            name="basic_primer",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
            # No tm, no score
        )

        amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[basic_primer],
            length=116,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            # Verify default values are used
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]
                assert float(row["temp_best"]) == 60.0, "Should use default tm 60.0"
                assert float(row["mean_temp"]) == 60.0
                assert float(row["score"]) == 90.0, "Should use default score 90.0"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_calculate_gc_content_normal_sequence(self):
        """VarVAMP GC content calculation must work for normal sequences."""
        writer = VarVAMPWriter()

        # Test 50% GC content
        gc_content = writer._calculate_gc_content("ATCGATCGATCGATCG")
        assert gc_content == 0.5

        # Test 100% GC content
        gc_content = writer._calculate_gc_content("GGCCGGCCGGCCGGCC")
        assert gc_content == 1.0

        # Test 0% GC content
        gc_content = writer._calculate_gc_content("ATATATATATATATAT")
        assert gc_content == 0.0

        # Test mixed case
        gc_content = writer._calculate_gc_content("atcgATCG")
        assert gc_content == 0.5

    @pytest.mark.unit
    @pytest.mark.writer
    def test_calculate_gc_content_empty_sequence(self):
        """VarVAMP GC content calculation must handle empty sequences."""
        writer = VarVAMPWriter()
        gc_content = writer._calculate_gc_content("")
        assert gc_content == 0.0

    @pytest.mark.unit
    @pytest.mark.writer
    def test_calculate_gc_content_precision(self):
        """VarVAMP GC content must be rounded to 3 decimal places."""
        writer = VarVAMPWriter()

        # Test rounding to 3 decimal places
        gc_content = writer._calculate_gc_content("ATCGATCG")  # 4/8 = 0.5
        assert gc_content == 0.5

        # Test with longer sequence that needs rounding
        gc_content = writer._calculate_gc_content("ATCGATCGATC")  # 5/11 = 0.45454...
        assert gc_content == 0.455, "Should round to 3 decimal places"

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_valid_file(self):
        """validate_output() must return True for valid VarVAMP file."""
        writer = VarVAMPWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
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
        writer = VarVAMPWriter()
        non_existent_path = Path("/non/existent/file.tsv")
        is_valid = writer.validate_output(non_existent_path)
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_missing_required_columns(self):
        """validate_output() must return False for files missing required columns."""
        writer = VarVAMPWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create TSV with missing required columns
            with open(output_path, "w", newline="", encoding="utf-8") as tsvfile:
                csv_writer = csv.DictWriter(
                    tsvfile, fieldnames=["start", "stop"], delimiter="\t"
                )
                csv_writer.writeheader()
                csv_writer.writerow({"start": "100", "stop": "200"})

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_empty_file(self):
        """validate_output() must return False for empty files."""
        writer = VarVAMPWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
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
    def test_validate_output_no_data_rows(self):
        """validate_output() must return False for files with headers but no data."""
        writer = VarVAMPWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create TSV with all required headers but no data
            fieldnames = [
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
            with open(output_path, "w", newline="", encoding="utf-8") as tsvfile:
                csv_writer = csv.DictWriter(
                    tsvfile, fieldnames=fieldnames, delimiter="\t"
                )
                csv_writer.writeheader()
                # No data rows

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_malformed_tsv(self):
        """validate_output() must return False for malformed TSV files."""
        writer = VarVAMPWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Create malformed TSV
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("this is not a valid TSV file\nwith random content")

            is_valid = writer.validate_output(output_path)
            assert is_valid is False

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_get_output_info(self):
        """get_output_info() must return comprehensive format information."""
        writer = VarVAMPWriter()
        info = writer.get_output_info()

        assert isinstance(info, dict)
        assert "format" in info
        assert "extension" in info
        assert "description" in info
        assert "use_case" in info
        assert "columns" in info
        assert "separator" in info
        assert "coordinate_system" in info

        # Check specific content
        assert "VarVAMP" in info["use_case"]
        assert "tab" in info["separator"]
        assert "1-based" in info["coordinate_system"]
        assert "amplicon_name" in info["columns"]
        assert "seq" in info["columns"]


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.writer
class TestVarVAMPWriterIntegration:
    """VarVAMP writer integration tests for complex scenarios."""

    def test_write_multiple_amplicons_multiple_primers(self):
        """VarVAMP writer must handle multiple amplicons with multiple primers each."""
        writer = VarVAMPWriter()

        # Create complex test data
        amplicons = []

        for amp_i in range(2):
            primers = []

            # Create multiple primers per amplicon
            for primer_i in range(3):
                primer = PrimerData(
                    name=f"amp_{amp_i}_primer_{primer_i}",
                    sequence=f"{'ATCG' * (4 + primer_i)}",
                    start=100 + amp_i * 300 + primer_i * 50,
                    stop=116 + amp_i * 300 + primer_i * 50,
                    strand="+" if primer_i % 2 == 0 else "-",
                    direction="forward" if primer_i % 2 == 0 else "reverse",
                    pool=(amp_i % 2) + 1,
                    amplicon_id=f"amplicon_{amp_i}",
                    gc_content=0.5 + primer_i * 0.1,
                    tm=55.0 + primer_i * 2.5,
                    score=85.0 + primer_i * 3.0,
                )
                primers.append(primer)

            amplicon = AmpliconData(
                amplicon_id=f"amplicon_{amp_i}",
                primers=primers,
                length=250 + amp_i * 50,
                reference_id="test_genome",
            )
            amplicons.append(amplicon)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Write data
            result_path = writer.write(amplicons, output_path)

            # Verify comprehensive output
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

                # Should have 6 total primers (2 amplicons * 3 primers each)
                assert len(rows) == 6

                # Check amplicon grouping
                amp_0_rows = [r for r in rows if r["amplicon_name"] == "amplicon_0"]
                amp_1_rows = [r for r in rows if r["amplicon_name"] == "amplicon_1"]

                assert len(amp_0_rows) == 3
                assert len(amp_1_rows) == 3

                # Check specific values for first amplicon's first primer
                first_row = amp_0_rows[0]
                assert first_row["amplicon_length"] == "250"
                assert first_row["pool"] == "1"
                assert first_row["size"] == "16"  # 4 * 4 = 16 chars

                # Check GC content calculation
                # "ATCGATCGATCGATCG" = 8 GC out of 16 = 50%
                assert float(first_row["gc_best"]) == 50.0
                assert float(first_row["mean_gc"]) == 50.0

            # Validate output
            assert writer.validate_output(output_path) is True

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_round_trip_data_integrity(self):
        """VarVAMP writer must preserve all data correctly."""
        writer = VarVAMPWriter()

        # Create test data with specific values to verify
        primer_data = [
            {
                "name": "test_primer_1",
                "sequence": "GCGCGCGCGCGCGCGC",  # 100% GC
                "start": 1000,
                "stop": 1016,
                "pool": 3,
                "tm": 68.5,
                "score": 92.3,
            },
            {
                "name": "test_primer_2",
                "sequence": "ATATATATATATATATAT",  # 0% GC, 18 chars
                "start": 2000,
                "stop": 2018,
                "pool": 4,
                "tm": 45.2,
                "score": 78.9,
            },
        ]

        primers = []
        for data in primer_data:
            primer = PrimerData(
                name=data["name"],
                sequence=data["sequence"],
                start=data["start"],
                stop=data["stop"],
                strand="+",
                direction="forward",
                pool=data["pool"],
                amplicon_id="test_amplicon",
                tm=data["tm"],
                score=data["score"],
            )
            primers.append(primer)

        amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=primers,
            length=500,
            reference_id="test_ref",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Write data
            writer.write([amplicon], output_path)

            # Verify all values are preserved correctly
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                rows = list(reader)

                assert len(rows) == 2

                # Check first primer (100% GC)
                row1 = rows[0]
                assert row1["primer_name"] == "test_primer_1"
                assert row1["seq"] == "GCGCGCGCGCGCGCGC"
                assert row1["start"] == "1000"
                assert row1["stop"] == "1016"
                assert row1["size"] == "16"
                assert row1["pool"] == "3"
                assert float(row1["gc_best"]) == 100.0
                assert float(row1["temp_best"]) == 68.5
                assert float(row1["score"]) == 92.3

                # Check second primer (0% GC)
                row2 = rows[1]
                assert row2["primer_name"] == "test_primer_2"
                assert row2["seq"] == "ATATATATATATATATAT"
                assert row2["size"] == "18"
                assert row2["pool"] == "4"
                assert float(row2["gc_best"]) == 0.0
                assert float(row2["temp_best"]) == 45.2
                assert float(row2["score"]) == 78.9

        finally:
            if output_path.exists():
                output_path.unlink()
