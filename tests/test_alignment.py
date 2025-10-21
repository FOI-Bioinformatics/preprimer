"""
Tests for alignment functionality.

Tests alignment providers (BLAST, Exonerate, me-PCR) and the align_primers function.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from preprimer.align import align_primers
from preprimer.alignment.blast_provider import BlastProvider
from preprimer.alignment.exonerate_provider import ExonerateProvider
from preprimer.alignment.mepcr_provider import MePCRProvider
from preprimer.alignment.merpcr_provider import MerPCRProvider
from preprimer.core.exceptions import PrePrimerError
from preprimer.core.registry import alignment_registry


@pytest.fixture
def test_data_dir():
    """Get path to test data directory."""
    return Path(__file__).parent / "test_data" / "datasets" / "small"


@pytest.fixture
def sts_file(test_data_dir):
    """Get path to STS test file."""
    return test_data_dir / "sts.tsv"


@pytest.fixture
def reference_file(test_data_dir):
    """Get path to reference FASTA file."""
    return test_data_dir / "reference.fasta"


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    return tmp_path / "alignment_output"


class TestAlignmentRegistry:
    """Test alignment registry functionality."""

    def test_registry_has_providers(self):
        """Test that all providers are registered."""
        providers = alignment_registry.list_providers()
        assert "blast" in providers
        assert "exonerate" in providers
        assert "me-pcr" in providers
        assert "merpcr" in providers

    def test_get_blast_provider(self):
        """Test getting BLAST provider."""
        provider = alignment_registry.get_provider("blast")
        assert isinstance(provider, BlastProvider)
        assert provider.tool_name() == "blast"

    def test_get_exonerate_provider(self):
        """Test getting Exonerate provider."""
        provider = alignment_registry.get_provider("exonerate")
        assert isinstance(provider, ExonerateProvider)
        assert provider.tool_name() == "exonerate"

    def test_get_mepcr_provider(self):
        """Test getting me-PCR provider."""
        provider = alignment_registry.get_provider("me-pcr")
        assert isinstance(provider, MePCRProvider)
        assert provider.tool_name() == "me-pcr"

    def test_get_merpcr_provider(self):
        """Test getting merPCR provider."""
        provider = alignment_registry.get_provider("merpcr")
        assert isinstance(provider, MerPCRProvider)
        assert provider.tool_name() == "merpcr"

    def test_invalid_provider(self):
        """Test requesting invalid provider raises error."""
        with pytest.raises(PrePrimerError):
            alignment_registry.get_provider("invalid_tool")


class TestBlastProvider:
    """Test BLAST alignment provider."""

    def test_tool_name(self):
        """Test BLAST tool name."""
        provider = BlastProvider()
        assert provider.tool_name() == "blast"

    def test_is_available_when_installed(self):
        """Test availability check when BLAST is installed."""
        provider = BlastProvider()
        with patch("shutil.which", return_value="/usr/bin/blastn"):
            assert provider.is_available() is True

    def test_is_available_when_not_installed(self):
        """Test availability check when BLAST is not installed."""
        provider = BlastProvider()
        with patch("shutil.which", return_value=None):
            assert provider.is_available() is False

    @patch("subprocess.run")
    def test_align_primers(self, mock_run, sts_file, reference_file, output_dir):
        """Test primer alignment with BLAST."""
        provider = BlastProvider()

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock is_available
        with patch.object(provider, "is_available", return_value=True):
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
            )

        # Check output directory was created
        assert output_path == output_dir
        assert output_dir.exists()


class TestExonerateProvider:
    """Test Exonerate alignment provider."""

    def test_tool_name(self):
        """Test Exonerate tool name."""
        provider = ExonerateProvider()
        assert provider.tool_name() == "exonerate"

    def test_is_available_when_installed(self):
        """Test availability check when Exonerate is installed."""
        provider = ExonerateProvider()
        with patch("shutil.which", return_value="/usr/bin/exonerate"):
            assert provider.is_available() is True

    def test_is_available_when_not_installed(self):
        """Test availability check when Exonerate is not installed."""
        provider = ExonerateProvider()
        with patch("shutil.which", return_value=None):
            assert provider.is_available() is False

    @patch("subprocess.run")
    def test_align_primers(self, mock_run, sts_file, reference_file, output_dir):
        """Test primer alignment with Exonerate."""
        provider = ExonerateProvider()

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock is_available
        with patch.object(provider, "is_available", return_value=True):
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
            )

        # Check output directory was created
        assert output_path == output_dir
        assert output_dir.exists()

    def test_parse_exonerate_output_empty_file(self, tmp_path):
        """Test parsing empty Exonerate output."""
        provider = ExonerateProvider()
        empty_file = tmp_path / "empty.aln"
        empty_file.write_text("")

        alignments = provider.parse_exonerate_output(empty_file)
        assert alignments == []

    def test_parse_exonerate_output_nonexistent_file(self, tmp_path):
        """Test parsing nonexistent Exonerate output."""
        provider = ExonerateProvider()
        missing_file = tmp_path / "missing.aln"

        alignments = provider.parse_exonerate_output(missing_file)
        assert alignments == []


class TestMePCRProvider:
    """Test me-PCR alignment provider."""

    def test_tool_name(self):
        """Test me-PCR tool name."""
        provider = MePCRProvider()
        assert provider.tool_name() == "me-pcr"

    def test_is_available_when_installed(self):
        """Test availability check when me-PCR is installed."""
        provider = MePCRProvider()
        with patch("shutil.which", return_value="/usr/bin/me-PCR"):
            assert provider.is_available() is True

    def test_is_available_when_not_installed(self):
        """Test availability check when me-PCR is not installed."""
        provider = MePCRProvider()
        with patch("shutil.which", return_value=None):
            assert provider.is_available() is False

    @patch("subprocess.run")
    def test_align_primers(self, mock_run, sts_file, reference_file, output_dir):
        """Test primer alignment with me-PCR."""
        provider = MePCRProvider()

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock is_available
        with patch.object(provider, "is_available", return_value=True):
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                max_product_size=1000,
            )

        # Check output file path
        assert output_path == output_dir / "primers.mepcr.aln"

    @patch("subprocess.run")
    def test_run_mepcr(self, mock_run, sts_file, reference_file, output_dir):
        """Test direct me-PCR execution."""
        provider = MePCRProvider()
        output_file = output_dir / "test.mepcr.aln"

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        result = provider.run_mepcr(
            primer_file=sts_file,
            reference=reference_file,
            output_file=output_file,
            max_product_size=1000,
        )

        assert result == output_file
        # Check subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "me-PCR"
        assert f"O={output_file}" in call_args
        assert "M=1000" in call_args


class TestMerPCRProvider:
    """Test merPCR alignment provider."""

    def test_tool_name(self):
        """Test merPCR tool name."""
        provider = MerPCRProvider()
        assert provider.tool_name() == "merpcr"

    def test_is_available_when_installed(self):
        """Test availability check when merPCR is installed."""
        provider = MerPCRProvider()
        with patch("shutil.which", return_value="/usr/bin/merpcr"):
            assert provider.is_available() is True

    def test_is_available_when_not_installed(self):
        """Test availability check when merPCR is not installed."""
        provider = MerPCRProvider()
        with patch("shutil.which", return_value=None):
            assert provider.is_available() is False

    @patch("subprocess.run")
    def test_align_primers(self, mock_run, sts_file, reference_file, output_dir):
        """Test primer alignment with merPCR."""
        provider = MerPCRProvider()

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock is_available
        with patch.object(provider, "is_available", return_value=True):
            output_path = provider.align_primers(
                primer_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                max_product_size=1000,
            )

        # Check output file path
        assert output_path == output_dir / "primers.merpcr.aln"

    @patch("subprocess.run")
    def test_run_merpcr(self, mock_run, sts_file, reference_file, output_dir):
        """Test direct merPCR execution."""
        provider = MerPCRProvider()
        output_file = output_dir / "test.merpcr.aln"

        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        result = provider.run_merpcr(
            primer_file=sts_file,
            reference=reference_file,
            output_file=output_file,
            max_product_size=1000,
        )

        assert result == output_file
        # Check subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "merpcr"
        assert "-O" in call_args
        assert str(output_file) in call_args
        assert "-M" in call_args
        assert "50" in call_args  # default margin


class TestAlignPrimersFunction:
    """Test high-level align_primers function."""

    def test_missing_sts_file(self, reference_file, output_dir):
        """Test error when STS file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="STS file not found"):
            align_primers(
                sts_file=Path("nonexistent.sts"),
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["primers"],
            )

    def test_missing_reference_file(self, sts_file, output_dir):
        """Test error when reference file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Reference file not found"):
            align_primers(
                sts_file=sts_file,
                reference_file=Path("nonexistent.fasta"),
                output_dir=output_dir,
                output_formats=["primers"],
            )

    def test_invalid_aligner(self, sts_file, reference_file, output_dir):
        """Test error with invalid aligner."""
        with pytest.raises(ValueError, match="Invalid aligner"):
            align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["primers"],
                aligner="invalid",
            )

    def test_invalid_output_format(self, sts_file, reference_file, output_dir):
        """Test error with invalid output format."""
        with pytest.raises(ValueError, match="Invalid output format"):
            align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["invalid"],
            )

    @patch("subprocess.run")
    def test_primers_format_with_blast(
        self, mock_run, sts_file, reference_file, output_dir
    ):
        """Test alignment with primers format using BLAST."""
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock BLAST availability
        with patch("shutil.which", return_value="/usr/bin/blastn"):
            output_paths = align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["primers"],
                aligner="blast",
            )

        assert "primers" in output_paths
        assert output_paths["primers"] == output_dir / "alignment" / "primers"

    @patch("subprocess.run")
    def test_primers_format_with_exonerate(
        self, mock_run, sts_file, reference_file, output_dir
    ):
        """Test alignment with primers format using Exonerate."""
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock Exonerate availability
        with patch("shutil.which", return_value="/usr/bin/exonerate"):
            output_paths = align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["primers"],
                aligner="exonerate",
            )

        assert "primers" in output_paths
        assert output_paths["primers"] == output_dir / "alignment" / "primers"

    @patch("subprocess.run")
    def test_mepcr_format(self, mock_run, sts_file, reference_file, output_dir):
        """Test alignment with me-pcr format."""
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock me-PCR availability
        with patch("shutil.which", return_value="/usr/bin/me-PCR"):
            output_paths = align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["me-pcr"],
            )

        assert "me-pcr" in output_paths
        assert (
            output_paths["me-pcr"]
            == output_dir / "alignment" / "mepcr" / "primers.mepcr.aln"
        )

    @patch("subprocess.run")
    def test_merpcr_format(self, mock_run, sts_file, reference_file, output_dir):
        """Test alignment with merpcr format."""
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock merPCR availability
        with patch("shutil.which", return_value="/usr/bin/merpcr"):
            output_paths = align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["merpcr"],
            )

        assert "merpcr" in output_paths
        assert (
            output_paths["merpcr"]
            == output_dir / "alignment" / "merpcr" / "primers.merpcr.aln"
        )

    @patch("subprocess.run")
    def test_multiple_output_formats(
        self, mock_run, sts_file, reference_file, output_dir
    ):
        """Test alignment with multiple output formats."""
        # Mock subprocess success
        mock_run.return_value = MagicMock(returncode=0)

        # Mock tool availability
        with patch("shutil.which", return_value="/usr/bin/tool"):
            output_paths = align_primers(
                sts_file=sts_file,
                reference_file=reference_file,
                output_dir=output_dir,
                output_formats=["primers", "me-pcr"],
                aligner="blast",
            )

        assert "primers" in output_paths
        assert "me-pcr" in output_paths
        assert len(output_paths) == 2

    def test_tool_not_available(self, sts_file, reference_file, output_dir):
        """Test error when required tool is not available."""
        # Mock tool not available
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="not available on this system"):
                align_primers(
                    sts_file=sts_file,
                    reference_file=reference_file,
                    output_dir=output_dir,
                    output_formats=["primers"],
                    aligner="blast",
                )
