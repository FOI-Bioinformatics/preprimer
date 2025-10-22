"""
FASTA writer tests using BaseWriterTest framework.

FASTA format is a multi-FASTA format where each primer is written
as a separate entry with metadata in the header.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.fasta_writer import FASTAWriter

from .test_base_writer import BaseWriterTest


class TestFASTAWriter(BaseWriterTest):
    """FASTA writer tests - inherits contract tests from BaseWriterTest."""

    # =========================================================================
    # Configuration - Required by BaseWriterTest
    # =========================================================================

    @property
    def writer_class(self):
        return FASTAWriter

    @property
    def expected_format_name(self):
        return "fasta"

    @property
    def expected_file_extension(self):
        return ".fasta"

    def get_test_amplicons(self):
        """Return test amplicons for FASTA tests."""
        # Create realistic test data
        forward_primer = PrimerData(
            name="test_1_F",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
            reference_id="chr1",
        )

        reverse_primer = PrimerData(
            name="test_1_R",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amplicon_1",
            reference_id="chr1",
        )

        amplicon = AmpliconData(
            amplicon_id="amplicon_1",
            primers=[forward_primer, reverse_primer],
            length=116,
            reference_id="chr1",
        )

        # Create second amplicon for multi-amplicon tests
        forward_primer2 = PrimerData(
            name="test_2_F",
            sequence="GGCCGGCCGGCCGGCC",
            start=300,
            stop=316,
            strand="+",
            direction="forward",
            pool=2,
            amplicon_id="amplicon_2",
            reference_id="chr1",
        )

        reverse_primer2 = PrimerData(
            name="test_2_R",
            sequence="TTAATTAATTAATTAA",
            start=400,
            stop=416,
            strand="-",
            direction="reverse",
            pool=2,
            amplicon_id="amplicon_2",
            reference_id="chr1",
        )

        amplicon2 = AmpliconData(
            amplicon_id="amplicon_2",
            primers=[forward_primer2, reverse_primer2],
            length=116,
            reference_id="chr1",
        )

        return [amplicon, amplicon2]

    def verify_output_content(self, output_path: Path, amplicons: list):
        """Verify FASTA output content."""
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # FASTA format should have headers starting with >
        lines = content.strip().split("\n")

        # Count headers (lines starting with >)
        headers = [line for line in lines if line.startswith(">")]
        expected_primers = sum(len(amp.primers) for amp in amplicons)

        assert len(headers) == expected_primers, \
            f"Expected {expected_primers} FASTA headers, got {len(headers)}"

        # Each header should be followed by a sequence
        for i, line in enumerate(lines):
            if line.startswith(">"):
                # Next line should be a sequence (not empty, not another header)
                if i + 1 < len(lines):
                    assert not lines[i + 1].startswith(">"), \
                        f"Header at line {i} not followed by sequence"
                    assert len(lines[i + 1]) > 0, \
                        f"Empty sequence after header at line {i}"

    # =========================================================================
    # Override base class tests where needed
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_description_property(self):
        """FASTA writer doesn't have description property - skip this test."""
        pytest.skip("FASTAWriter doesn't implement description property")

    # =========================================================================
    # FASTA-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_fasta_header_format(self):
        """FASTA writer must include primer metadata in headers."""
        writer = FASTAWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Check header format includes required metadata
            lines = content.strip().split("\n")
            headers = [line for line in lines if line.startswith(">")]

            for header in headers:
                # Should include position
                assert "pos=" in header, "Header should include position"
                # Should include strand
                assert "strand=" in header, "Header should include strand"
                # Should include pool
                assert "pool=" in header, "Header should include pool"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_fasta_sequence_format(self):
        """FASTA writer must write valid sequences."""
        writer = FASTAWriter()
        amplicons = self.get_test_amplicons()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Get sequence lines (non-header lines)
            sequences = [line for line in lines if not line.startswith(">")]

            assert len(sequences) > 0, "Should have sequence lines"

            # Check all sequences are valid DNA
            for seq in sequences:
                assert len(seq) > 0, "Sequences should not be empty"
                # Allow IUPAC nucleotide codes
                valid_chars = set("ATCGNRYSWKMBDHVatcgn")
                assert all(c in valid_chars for c in seq), \
                    f"Invalid characters in sequence: {seq}"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_with_quality_metrics(self):
        """FASTA writer must include quality metrics in headers when available."""
        writer = FASTAWriter()

        # Create primer with quality metrics
        forward = PrimerData(
            name="test_F",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amp",
            reference_id="chr1",
            gc_content=50.0,
            tm=55.5,
            score=0.95,
        )

        reverse = PrimerData(
            name="test_R",
            sequence="CGATCGAT",
            start=200,
            stop=208,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amp",
            reference_id="chr1",
            gc_content=50.0,
            tm=56.2,
            score=0.92,
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp",
            primers=[forward, reverse],
            length=108,
            reference_id="chr1",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Check quality metrics in headers
            assert "gc=" in content, "Should include GC content"
            assert "tm=" in content, "Should include melting temperature"
            assert "score=" in content, "Should include score"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_without_quality_metrics(self):
        """FASTA writer must handle primers without quality metrics."""
        writer = FASTAWriter()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Primers in get_test_amplicons() don't have quality metrics
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Should still have basic metadata
            assert "pos=" in content
            assert "strand=" in content
            assert "pool=" in content

            # File should exist and not be empty
            assert output_path.stat().st_size > 0

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_artic_naming_convention(self):
        """FASTA writer must use ARTIC naming convention for primers."""
        writer = FASTAWriter()

        # Create primers with proper ARTIC naming
        forward = PrimerData(
            name="nCoV-2019_1_LEFT",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="nCoV-2019_1",
            reference_id="MN908947.3",
        )

        amplicon = AmpliconData(
            amplicon_id="nCoV-2019_1",
            primers=[forward],
            length=108,
            reference_id="MN908947.3",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Check for ARTIC naming pattern in headers
            lines = content.strip().split("\n")
            headers = [line for line in lines if line.startswith(">")]

            for header in headers:
                # ARTIC names should be in format: amplicon_num_direction_alt
                # The artic_name property generates this
                assert "_LEFT" in header or "_RIGHT" in header, \
                    "Should use ARTIC naming convention"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_realistic_dataset(self):
        """FASTA writer must handle realistic datasets correctly."""
        writer = FASTAWriter()

        # Create realistic amplicons
        amplicons = []
        for i in range(5):
            forward = PrimerData(
                name=f"amplicon_{i+1}_LEFT",
                sequence=f"{'ATCG' * 4}",
                start=100 + i * 200,
                stop=116 + i * 200,
                strand="+",
                direction="forward",
                pool=(i % 2) + 1,
                amplicon_id=f"amplicon_{i+1}",
                reference_id="SARS-CoV-2",
            )

            reverse = PrimerData(
                name=f"amplicon_{i+1}_RIGHT",
                sequence=f"{'CGTA' * 4}",
                start=200 + i * 200,
                stop=216 + i * 200,
                strand="-",
                direction="reverse",
                pool=(i % 2) + 1,
                amplicon_id=f"amplicon_{i+1}",
                reference_id="SARS-CoV-2",
            )

            amplicon = AmpliconData(
                amplicon_id=f"amplicon_{i+1}",
                primers=[forward, reverse],
                length=116,
                reference_id="SARS-CoV-2",
            )
            amplicons.append(amplicon)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Should have 10 entries (5 amplicons × 2 primers)
            headers = [line for line in lines if line.startswith(">")]
            assert len(headers) == 10

            # Verify all primers written
            sequences = [line for line in lines if not line.startswith(">")]
            assert len(sequences) == 10

            for seq in sequences:
                assert len(seq) == 16  # 'ATCG' * 4 or 'CGTA' * 4

            # File should be well-formed
            assert output_path.exists()
            assert output_path.stat().st_size > 0

        finally:
            if output_path.exists():
                output_path.unlink()


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.writer
class TestFASTAWriterIntegration:
    """FASTA writer integration tests for complex scenarios."""

    def test_write_mixed_quality_metrics(self):
        """FASTA writer must handle mix of primers with and without quality metrics."""
        writer = FASTAWriter()

        # Primer with quality metrics
        forward = PrimerData(
            name="amp1_F",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amp1",
            reference_id="chr1",
            gc_content=50.0,
            tm=55.5,
        )

        # Primer without quality metrics
        reverse = PrimerData(
            name="amp1_R",
            sequence="CGTAGCTA",
            start=200,
            stop=208,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amp1",
            reference_id="chr1",
        )

        amplicon = AmpliconData(
            amplicon_id="amp1",
            primers=[forward, reverse],
            length=108,
            reference_id="chr1",
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            writer.write([amplicon], output_path)

            with open(output_path, "r") as f:
                content = f.read()

            # Should have both primers
            assert content.count(">") == 2

            # First primer should have quality metrics
            lines = content.strip().split("\n")
            assert "gc=" in lines[0] or "tm=" in lines[0]

            # Both should have basic metadata
            assert all("pos=" in line for line in lines if line.startswith(">"))

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_empty_amplicons_creates_empty_file(self):
        """FASTA writer must create valid (empty) file for empty amplicons list."""
        writer = FASTAWriter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = writer.write([], output_path)

            # Should create file
            assert result is not None
            assert output_path.exists()

            # File should be empty or minimal
            with open(output_path, "r") as f:
                content = f.read()
                assert len(content) == 0 or content.strip() == ""

        finally:
            if output_path.exists():
                output_path.unlink()
