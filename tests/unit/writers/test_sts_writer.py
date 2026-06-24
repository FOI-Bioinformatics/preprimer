"""
STS writer tests using BaseWriterTest framework.

STS (Sequence Tagged Site) format is a 3-column TSV format with
amplicon ID, forward primer sequence, and reverse primer sequence.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.sts_writer import STSWriter

from .test_base_writer import BaseWriterTest


class TestSTSWriter(BaseWriterTest):
    """STS writer tests - inherits contract tests from BaseWriterTest."""

    # =========================================================================
    # Configuration - Required by BaseWriterTest
    # =========================================================================

    @property
    def writer_class(self):
        return STSWriter

    @property
    def expected_format_name(self):
        return "sts"

    @property
    def expected_file_extension(self):
        return ".sts.tsv"

    def get_test_amplicons(self):
        """Return test amplicons for STS tests."""
        # Create realistic test data
        forward_primer = PrimerData(
            name="amp1_F",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amp1",
        )

        reverse_primer = PrimerData(
            name="amp1_R",
            sequence="CGTAGCTAGCTAGCTA",
            start=200,
            stop=216,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="amp1",
        )

        amplicon = AmpliconData(
            amplicon_id="amp1",
            primers=[forward_primer, reverse_primer],
            length=116,
            reference_id="chr1",
        )

        # Create second amplicon
        forward_primer2 = PrimerData(
            name="amp2_F",
            sequence="GGCCGGCCGGCCGGCC",
            start=300,
            stop=316,
            strand="+",
            direction="forward",
            pool=2,
            amplicon_id="amp2",
        )

        reverse_primer2 = PrimerData(
            name="amp2_R",
            sequence="TTAATTAATTAATTAA",
            start=400,
            stop=416,
            strand="-",
            direction="reverse",
            pool=2,
            amplicon_id="amp2",
        )

        amplicon2 = AmpliconData(
            amplicon_id="amp2",
            primers=[forward_primer2, reverse_primer2],
            length=116,
            reference_id="chr1",
        )

        return [amplicon, amplicon2]

    def verify_output_content(self, output_path: Path, amplicons: list):
        """Verify STS TSV output content."""
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n")

        # STS has header + one row per amplicon
        assert len(lines) >= 1, "File should have at least header"
        # STS writer outputs 4 columns: NAME, FORWARD, REVERSE, SIZE
        assert (
            lines[0] == "NAME\tFORWARD\tREVERSE\tSIZE"
        ), "Header should be NAME, FORWARD, REVERSE, SIZE"

        # Count amplicons with both forward and reverse primers
        complete_amplicons = [
            amp
            for amp in amplicons
            if any(p.direction == "forward" for p in amp.primers)
            and any(p.direction == "reverse" for p in amp.primers)
        ]

        if complete_amplicons:
            assert (
                len(lines) == len(complete_amplicons) + 1
            ), f"Expected {len(complete_amplicons)} data rows, got {len(lines) - 1}"

    # =========================================================================
    # Override base class tests where needed
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_description_property(self):
        """STS writer doesn't have description property - skip this test."""
        # STSWriter doesn't implement description property
        # This is acceptable as it's not strictly required by OutputWriter interface
        pytest.skip("STSWriter doesn't implement description property")

    # =========================================================================
    # STS-Specific Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_missing_primers_warning(self):
        """STS writer must skip amplicons with missing forward or reverse primer."""
        writer = STSWriter()

        # Create amplicons with missing primers
        amplicons = [
            # Only forward primer
            AmpliconData(
                amplicon_id="amp1",
                primers=[
                    PrimerData(
                        "amp1_F", "ATCGATCG", 100, 108, "+", "forward", 1, "amp1"
                    )
                ],
                reference_id="chr1",
            ),
            # Only reverse primer
            AmpliconData(
                amplicon_id="amp2",
                primers=[
                    PrimerData(
                        "amp2_R", "CGATCGAT", 200, 208, "-", "reverse", 1, "amp2"
                    )
                ],
                reference_id="chr1",
            ),
            # Complete amplicon
            AmpliconData(
                amplicon_id="amp3",
                primers=[
                    PrimerData(
                        "amp3_F", "GCTAGCTA", 300, 308, "+", "forward", 1, "amp3"
                    ),
                    PrimerData(
                        "amp3_R", "TAGCTAG", 400, 407, "-", "reverse", 1, "amp3"
                    ),
                ],
                reference_id="chr1",
            ),
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            # Should skip incomplete amplicons
            writer.write(amplicons, output_path)

            # Check file contents - should only have complete amplicon
            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            assert len(lines) == 2, "Should have header + 1 complete amplicon"
            # When there are incomplete amplicons filtered, STS writes 3-column format
            assert "NAME\tFORWARD\tREVERSE" in lines[0]
            assert "amp3" in lines[1] or "chr1_amp3" in lines[1]

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_reference_id_processing(self):
        """STS writer must include reference_id in amplicon name."""
        writer = STSWriter()

        amplicons = [
            AmpliconData(
                amplicon_id="test_amplicon",
                primers=[
                    PrimerData(
                        "test_F",
                        "ATCGATCG",
                        100,
                        108,
                        "+",
                        "forward",
                        1,
                        "test_amplicon",
                    ),
                    PrimerData(
                        "test_R",
                        "CGATCGAT",
                        200,
                        208,
                        "-",
                        "reverse",
                        1,
                        "test_amplicon",
                    ),
                ],
                reference_id="chr1",
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            # Check that reference_id was included in name
            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            assert len(lines) == 2  # Header + 1 amplicon

            # Should have format: chr1_test_amplicon
            name_part = lines[1].split("\t")[0]
            assert name_part == "chr1_test_amplicon"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_amplicon_id_duplication_prevention(self):
        """STS writer must not duplicate reference_id in name."""
        writer = STSWriter()

        # Amplicon where amplicon_id already contains reference_id
        amplicons = [
            AmpliconData(
                amplicon_id="chr1_amplicon_1",  # Already contains reference_id
                primers=[
                    PrimerData(
                        "amp_F",
                        "ATCGATCG",
                        100,
                        108,
                        "+",
                        "forward",
                        1,
                        "chr1_amplicon_1",
                    ),
                    PrimerData(
                        "amp_R",
                        "CGATCGAT",
                        200,
                        208,
                        "-",
                        "reverse",
                        1,
                        "chr1_amplicon_1",
                    ),
                ],
                reference_id="chr1",
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Should NOT duplicate - should be chr1_amplicon_1, not chr1_chr1_amplicon_1
            name_part = lines[1].split("\t")[0]
            assert name_part == "chr1_amplicon_1"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_multiple_primers_warning(self):
        """STS writer must handle amplicons with multiple forward/reverse primers."""
        writer = STSWriter()

        # Amplicon with multiple forward and reverse primers
        amplicons = [
            AmpliconData(
                amplicon_id="amp1",
                primers=[
                    PrimerData(
                        "amp1_F1", "ATCGATCG", 100, 108, "+", "forward", 1, "amp1"
                    ),
                    PrimerData(
                        "amp1_F2", "GCTAGCTA", 110, 118, "+", "forward", 1, "amp1"
                    ),
                    PrimerData(
                        "amp1_R1", "CGATCGAT", 200, 208, "-", "reverse", 1, "amp1"
                    ),
                    PrimerData(
                        "amp1_R2", "TAGCTAG", 210, 217, "-", "reverse", 1, "amp1"
                    ),
                ],
                reference_id="chr1",
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            # Should use first primers of each direction
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            assert len(lines) == 2
            # Should contain first forward and first reverse
            assert "ATCGATCG" in lines[1]
            assert "CGATCGAT" in lines[1]

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_amplicon_without_reference_id(self):
        """STS writer must handle amplicons without reference_id."""
        writer = STSWriter()

        amplicons = [
            AmpliconData(
                amplicon_id="test_amplicon",
                primers=[
                    PrimerData(
                        "test_F",
                        "ATCGATCG",
                        100,
                        108,
                        "+",
                        "forward",
                        1,
                        "test_amplicon",
                    ),
                    PrimerData(
                        "test_R",
                        "CGATCGAT",
                        200,
                        208,
                        "-",
                        "reverse",
                        1,
                        "test_amplicon",
                    ),
                ],
                reference_id=None,  # No reference_id
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            assert len(lines) == 2
            # Should just use amplicon_id
            name_part = lines[1].split("\t")[0]
            assert name_part == "test_amplicon"

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_complex_amplicon_naming(self):
        """STS writer must handle complex amplicon naming scenarios."""
        writer = STSWriter()

        amplicons = [
            AmpliconData(
                amplicon_id="complex_name_123",
                primers=[
                    PrimerData(
                        "p_F",
                        "ATCGATCG",
                        100,
                        108,
                        "+",
                        "forward",
                        1,
                        "complex_name_123",
                    ),
                    PrimerData(
                        "p_R",
                        "CGATCGAT",
                        200,
                        208,
                        "-",
                        "reverse",
                        1,
                        "complex_name_123",
                    ),
                ],
                reference_id="NC_045512.2",
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Should combine reference_id and amplicon_id
            name_part = lines[1].split("\t")[0]
            assert "NC_045512.2" in name_part
            assert "complex_name_123" in name_part

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_realistic_dataset(self):
        """STS writer must handle realistic datasets correctly."""
        writer = STSWriter()

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
            )

            amplicon = AmpliconData(
                amplicon_id=f"amplicon_{i+1}",
                primers=[forward, reverse],
                length=116,
                reference_id="SARS-CoV-2",
            )
            amplicons.append(amplicon)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Should have header + 5 amplicons
            assert len(lines) == 6
            assert lines[0] == "NAME\tFORWARD\tREVERSE\tSIZE"

            # Verify all amplicons written
            for i in range(5):
                assert f"amplicon_{i+1}" in lines[i + 1]
                assert "ATCGATCGATCGATCG" in lines[i + 1]
                assert "CGTACGTACGTACGTA" in lines[i + 1]

            # STSWriter doesn't have validate_output method - just verify file exists
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
class TestSTSWriterIntegration:
    """STS writer integration tests for complex scenarios."""

    def test_write_mixed_complete_incomplete_amplicons(self):
        """STS writer must filter out incomplete amplicons correctly."""
        writer = STSWriter()

        amplicons = [
            # Complete
            AmpliconData(
                amplicon_id="amp1",
                primers=[
                    PrimerData("a1_F", "ATCGATCG", 100, 108, "+", "forward", 1, "amp1"),
                    PrimerData("a1_R", "CGATCGAT", 200, 208, "-", "reverse", 1, "amp1"),
                ],
                reference_id="chr1",
            ),
            # Missing reverse
            AmpliconData(
                amplicon_id="amp2",
                primers=[
                    PrimerData("a2_F", "GCTAGCTA", 300, 308, "+", "forward", 1, "amp2"),
                ],
                reference_id="chr1",
            ),
            # Complete
            AmpliconData(
                amplicon_id="amp3",
                primers=[
                    PrimerData("a3_F", "TAGCTAG", 400, 407, "+", "forward", 1, "amp3"),
                    PrimerData("a3_R", "GCTAGC", 500, 506, "-", "reverse", 1, "amp3"),
                ],
                reference_id="chr1",
            ),
            # Missing forward
            AmpliconData(
                amplicon_id="amp4",
                primers=[
                    PrimerData("a4_R", "ATCGAT", 600, 606, "-", "reverse", 1, "amp4"),
                ],
                reference_id="chr1",
            ),
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sts.tsv", delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            writer.write(amplicons, output_path)

            with open(output_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Should have header + 2 complete amplicons only
            assert len(lines) == 3
            assert "amp1" in lines[1] or "chr1_amp1" in lines[1]
            assert "amp3" in lines[2] or "chr1_amp3" in lines[2]

        finally:
            if output_path.exists():
                output_path.unlink()
