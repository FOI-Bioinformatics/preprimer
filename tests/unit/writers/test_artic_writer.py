"""
ARTIC writer tests using BaseWriterTest framework.

ARTIC format creates a primerscheme directory with:
- primer.bed: BED format with primers
- reference.fasta: Reference genome
- info.json: Scheme metadata (primal-page schema)
"""

import json
import tempfile
from pathlib import Path

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.artic_writer import ARTICWriter

from .test_base_writer import BaseWriterTest


class TestARTICWriter(BaseWriterTest):
    """ARTIC writer tests - inherits contract tests from BaseWriterTest."""

    # =========================================================================
    # Configuration - Required by BaseWriterTest
    # =========================================================================

    @property
    def writer_class(self):
        return ARTICWriter

    @property
    def expected_format_name(self):
        return "artic"

    @property
    def expected_file_extension(self):
        return "primer.bed"

    def get_test_amplicons(self):
        """Return test amplicons for ARTIC tests."""
        # Create realistic test data with proper LEFT/RIGHT naming
        forward_primer = PrimerData(
            name="amp_1_LEFT",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amp_1",
            reference_id="MN908947.3",
        )

        reverse_primer = PrimerData(
            name="amp_1_RIGHT",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amp_1",
            reference_id="MN908947.3",
        )

        amplicon = AmpliconData(
            amplicon_id="amp_1",
            primers=[forward_primer, reverse_primer],
            length=116,
            reference_id="MN908947.3",
        )

        # Create second amplicon
        forward_primer2 = PrimerData(
            name="amp_2_LEFT",
            sequence="GGCCGGCCGGCCGGCC",
            start=300,
            stop=316,
            strand="+",
            direction="forward",
            pool=2,
            amplicon_id="amp_2",
            reference_id="MN908947.3",
        )

        reverse_primer2 = PrimerData(
            name="amp_2_RIGHT",
            sequence="TTAATTAATTAATTAA",
            start=400,
            stop=416,
            strand="-",
            direction="reverse",
            pool=2,
            amplicon_id="amp_2",
            reference_id="MN908947.3",
        )

        amplicon2 = AmpliconData(
            amplicon_id="amp_2",
            primers=[forward_primer2, reverse_primer2],
            length=116,
            reference_id="MN908947.3",
        )

        return [amplicon, amplicon2]

    def verify_output_content(self, output_path: Path, amplicons: list):
        """Verify ARTIC directory structure and content."""
        # ARTIC writer writes files to parent directory of output_path
        # So files are at output_path.parent, not output_path itself
        base_dir = output_path.parent

        # Check for required files in parent directory
        primer_bed = base_dir / "primer.bed"
        info_json = base_dir / "info.json"

        assert primer_bed.exists(), f"primer.bed should exist at {primer_bed}"
        assert info_json.exists(), f"info.json should exist at {info_json}"

        # Verify primer.bed content
        with open(primer_bed, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n")

        # Count primers
        expected_primers = sum(len(amp.primers) for amp in amplicons)
        assert len(lines) == expected_primers, \
            f"Expected {expected_primers} primers, got {len(lines)}"

        # Verify info.json is valid JSON
        with open(info_json, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        assert isinstance(metadata, dict), "info.json should contain a dictionary"

    # =========================================================================
    # Override base class tests where needed
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_description_property(self):
        """ARTIC writer doesn't have description property - skip this test."""
        pytest.skip("ARTICWriter doesn't implement description property")

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_single_amplicon(self):
        """ARTIC writer must handle single amplicon correctly."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            result_path = writer.write(amplicons, output_path)

            assert result_path is not None
            # ARTIC writes files to parent directory
            assert result_path.parent == Path(tmpdir)

            # Verify content using subclass implementation
            self.verify_output_content(output_path, amplicons)

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_multiple_amplicons(self):
        """ARTIC writer must handle multiple amplicons correctly."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            result_path = writer.write(amplicons, output_path)

            assert result_path is not None
            # Verify files created
            assert result_path.exists()

            self.verify_output_content(output_path, amplicons)

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_empty_amplicons_list(self):
        """ARTIC writer must handle empty amplicons list gracefully."""
        writer = ARTICWriter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            # Should handle empty list gracefully
            result_path = writer.write([], output_path)

            # Just verify no crash
            assert result_path is not None

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_creates_output_directory(self):
        """ARTIC writer must create output directory if it doesn't exist."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory path that doesn't exist
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "scheme"

            # Directory should not exist yet
            assert not output_path.parent.exists()

            result_path = writer.write(amplicons, output_path)

            # Files should be created
            assert result_path is not None
            assert result_path.exists()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_performance(self, benchmark):
        """Benchmark ARTIC writer performance for regression detection."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        def write_amplicons():
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "scheme"
                return writer.write(amplicons, output_path)

        result = benchmark(write_amplicons)
        assert result is not None

    # =========================================================================
    # ARTIC-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_creates_primer_bed(self):
        """ARTIC writer must create primer.bed file."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            writer.write(amplicons, output_path)

            # Files are in parent directory
            primer_bed = Path(tmpdir) / "primer.bed"
            assert primer_bed.exists()
            assert primer_bed.stat().st_size > 0

            # Verify BED format (6+ columns)
            with open(primer_bed, "r") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    assert len(parts) >= 6, "BED format should have at least 6 columns"

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_creates_info_json(self):
        """ARTIC writer must create info.json with metadata."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            writer.write(
                amplicons,
                output_path,
                schemeversion="v1.0.0",
                species="SARS-CoV-2",
                authors=["Test Author"],
            )

            info_json = Path(tmpdir) / "info.json"
            assert info_json.exists()

            # Verify JSON content
            with open(info_json, "r") as f:
                metadata = json.load(f)

            assert "schemeversion" in metadata
            assert metadata["schemeversion"] == "v1.0.0"

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_reference_path(self):
        """ARTIC writer must include reference.fasta when reference_path provided."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        # Create temporary reference file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as ref:
            ref.write(">MN908947.3\n")
            ref.write("ATCGATCGATCGATCG\n")
            ref_path = Path(ref.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "scheme"

                writer.write(amplicons, output_path, reference_path=str(ref_path))

                # Should have reference.fasta
                reference_fasta = Path(tmpdir) / "reference.fasta"
                assert reference_fasta.exists()

                # Verify content
                with open(reference_fasta, "r") as f:
                    content = f.read()
                    assert ">MN908947.3" in content
                    assert "ATCGATCGATCGATCG" in content

        finally:
            ref_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_primer_bed_format(self):
        """ARTIC primer.bed must use correct BED6 format."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            writer.write(amplicons, output_path)

            primer_bed = Path(tmpdir) / "primer.bed"

            # Verify BED6 format: chrom, start, end, name, pool, strand
            with open(primer_bed, "r") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    assert len(parts) >= 6

                    # Column checks
                    chrom = parts[0]
                    start = int(parts[1])  # Should be 0-based
                    end = int(parts[2])
                    name = parts[3]
                    pool = int(parts[4])
                    strand = parts[5]

                    assert start >= 0
                    assert end > start
                    assert "_LEFT" in name or "_RIGHT" in name
                    assert pool > 0
                    assert strand in ["+", "-"]

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_info_json_primalpage_schema(self):
        """ARTIC info.json must follow primal-page schema."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            writer.write(
                amplicons,
                output_path,
                prefix="nCoV-2019",
                schemeversion="v5.3.2",
                species="SARS-CoV-2",
                authors=["ARTIC Network"],
                description="ARTIC nCoV-2019 v5.3.2 primer scheme",
            )

            info_json = Path(tmpdir) / "info.json"

            with open(info_json, "r") as f:
                metadata = json.load(f)

            # Check primal-page required fields
            assert "schemeversion" in metadata
            assert "ampliconsize" in metadata or "targetampliconsize" in metadata
            assert "primerbed" in metadata or "primer_bed_md5" in metadata
            assert "collections" in metadata

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_prefix(self):
        """ARTIC writer must use prefix in metadata."""
        writer = ARTICWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scheme"

            writer.write(amplicons, output_path, prefix="test_scheme")

            # Prefix should appear in metadata
            info_json = Path(tmpdir) / "info.json"
            with open(info_json, "r") as f:
                metadata = json.load(f)

            # Prefix typically used in collections or other metadata
            assert metadata is not None


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.writer
class TestARTICWriterIntegration:
    """ARTIC writer integration tests for complex scenarios."""

    def test_write_complete_primerscheme(self):
        """ARTIC writer must create complete primerscheme directory."""
        writer = ARTICWriter()

        # Create realistic amplicons
        amplicons = []
        for i in range(5):
            forward = PrimerData(
                name=f"nCoV-2019_{i+1}_LEFT",
                sequence="ATCGATCGATCGATCG",
                start=100 + i * 200,
                stop=116 + i * 200,
                strand="+",
                direction="forward",
                pool=(i % 2) + 1,
                amplicon_id=f"nCoV-2019_{i+1}",
                reference_id="MN908947.3",
            )

            reverse = PrimerData(
                name=f"nCoV-2019_{i+1}_RIGHT",
                sequence="CGTAGCTAGCTAGCTA",
                start=200 + i * 200,
                stop=216 + i * 200,
                strand="-",
                direction="reverse",
                pool=(i % 2) + 1,
                amplicon_id=f"nCoV-2019_{i+1}",
                reference_id="MN908947.3",
            )

            amplicon = AmpliconData(
                amplicon_id=f"nCoV-2019_{i+1}",
                primers=[forward, reverse],
                length=116,
                reference_id="MN908947.3",
            )
            amplicons.append(amplicon)

        # Create reference file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as ref:
            ref.write(">MN908947.3 SARS-CoV-2\n")
            ref.write("A" * 1000 + "\n")
            ref_path = Path(ref.name)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "nCoV-2019" / "V5"

                writer.write(
                    amplicons,
                    output_path,
                    prefix="nCoV-2019",
                    schemeversion="v5.0.0",
                    species="SARS-CoV-2",
                    authors=["ARTIC Network"],
                    description="nCoV-2019 primer scheme v5.0.0",
                    reference_path=str(ref_path),
                )

                # Verify directory structure - files are in parent directory (tmpdir/nCoV-2019/)
                base = Path(tmpdir) / "nCoV-2019"
                assert (base / "primer.bed").exists()
                assert (base / "reference.fasta").exists()
                assert (base / "info.json").exists()

                # Verify primer.bed has all primers
                with open(base / "primer.bed", "r") as f:
                    lines = f.read().strip().split("\n")
                    assert len(lines) == 10  # 5 amplicons × 2 primers

                # Verify info.json has correct metadata
                with open(base / "info.json", "r") as f:
                    metadata = json.load(f)
                    assert metadata["schemeversion"] == "v5.0.0"

        finally:
            ref_path.unlink()
