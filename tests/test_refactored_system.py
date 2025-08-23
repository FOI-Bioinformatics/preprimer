"""
Tests for the refactored preprimer system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from preprimer.core.interfaces import PrimerData, AmpliconData
from preprimer.core.config import PrePrimerConfig
from preprimer.core.converter import PrimerConverter
from preprimer.core.registry import parser_registry, writer_registry
from preprimer.parsers.varvamp_parser import VarVAMPParser
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.olivar_parser import OlivarParser
from preprimer.writers.artic_writer import ARTICWriter
from preprimer.writers.fasta_writer import FASTAWriter
from preprimer.writers.sts_writer import STSWriter


class TestDataStructures:
    """Test the core data structures."""

    def test_primer_data_creation(self):
        """Test PrimerData creation and properties."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            amplicon_id="amplicon_1",
            reference_id="test_ref",
        )

        assert primer.name == "test_primer"
        assert primer.length == 12
        assert primer.artic_name == "test_ref_1_LEFT_0"

    def test_amplicon_data_creation(self):
        """Test AmpliconData creation and properties."""
        primer1 = PrimerData("p1", "ATCG", 100, 104, "+", "forward", amplicon_id="amp1")
        primer2 = PrimerData("p2", "CGAT", 200, 204, "-", "reverse", amplicon_id="amp1")

        amplicon = AmpliconData("amp1", [primer1, primer2])

        assert len(amplicon.primers) == 2
        assert len(amplicon.forward_primers) == 1
        assert len(amplicon.reverse_primers) == 1
        assert len(amplicon.get_primer_pairs()) == 1


class TestRegistrySystem:
    """Test the parser and writer registry system."""

    def test_parser_registry(self):
        """Test that parsers are registered correctly."""
        formats = parser_registry.list_formats()

        assert "varvamp" in formats
        assert "artic" in formats
        assert "olivar" in formats

    def test_writer_registry(self):
        """Test that writers are registered correctly."""
        formats = writer_registry.list_formats()

        assert "artic" in formats
        assert "fasta" in formats
        assert "sts" in formats

    def test_parser_instantiation(self):
        """Test that parsers can be instantiated."""
        varvamp_parser = parser_registry.get_parser("varvamp")
        assert isinstance(varvamp_parser, VarVAMPParser)

        artic_parser = parser_registry.get_parser("artic")
        assert isinstance(artic_parser, ARTICParser)

        olivar_parser = parser_registry.get_parser("olivar")
        assert isinstance(olivar_parser, OlivarParser)

    def test_writer_instantiation(self):
        """Test that writers can be instantiated."""
        artic_writer = writer_registry.get_writer("artic")
        assert isinstance(artic_writer, ARTICWriter)

        fasta_writer = writer_registry.get_writer("fasta")
        assert isinstance(fasta_writer, FASTAWriter)

        sts_writer = writer_registry.get_writer("sts")
        assert isinstance(sts_writer, STSWriter)


class TestConfigSystem:
    """Test the configuration system."""

    def test_default_config(self):
        """Test default configuration creation."""
        config = PrePrimerConfig()

        assert config.aligner == "blast"
        assert config.output_formats == ["artic"]
        assert config.validate_sequences is True

    def test_config_validation(self):
        """Test configuration validation."""
        config = PrePrimerConfig()
        issues = config.validate()
        assert len(issues) == 0

        # Test invalid configuration
        config.aligner = "invalid_aligner"
        issues = config.validate()
        assert len(issues) > 0

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        data = {
            "aligner": "exonerate",
            "output_formats": ["fasta", "sts"],
            "force_overwrite": True,
        }

        config = PrePrimerConfig.from_dict(data)
        assert config.aligner == "exonerate"
        assert config.output_formats == ["fasta", "sts"]
        assert config.force_overwrite is True


class TestVarVAMPParser:
    """Test VarVAMP parser functionality."""

    def create_test_varvamp_file(self):
        """Create a test VarVAMP file."""
        content = """amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\tseq\tsize\tgc_best\ttemp_best\tmean_gc\tmean_temp\tscore
amplicon_0\t2737\tFW_0\t0\t5\t26\tactgctgtaggcgtcaaagatt\t22\t45.5\t58.3\t45.5\t58.3\t4.7
amplicon_0\t2737\tRW_60\t0\t2719\t2741\tcggaaataatacggtgggcgaga\t23\t52.2\t60.8\t52.2\t60.8\t3.0
amplicon_1\t2914\tFW_87\t1\t4171\t4192\ttcctcatgcgaattcactccca\t22\t50.0\t59.8\t50.0\t59.8\t0.9
amplicon_1\t2914\tRW_135\t1\t7063\t7084\tcgaacagaatgcccacaacaca\t22\t50.0\t60.0\t50.0\t60.0\t0.6"""

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False)
        temp_file.write(content)
        temp_file.close()

        return Path(temp_file.name)

    def test_varvamp_validation(self):
        """Test VarVAMP file validation."""
        parser = VarVAMPParser()
        test_file = self.create_test_varvamp_file()

        try:
            assert parser.validate_file(test_file) is True
        finally:
            test_file.unlink()

    def test_varvamp_parsing(self):
        """Test VarVAMP file parsing."""
        parser = VarVAMPParser()
        test_file = self.create_test_varvamp_file()

        try:
            amplicons = parser.parse(test_file, "TEST")

            assert len(amplicons) == 2
            assert amplicons[0].amplicon_id == "amplicon_0"
            assert amplicons[1].amplicon_id == "amplicon_1"

            # Check primer counts
            assert len(amplicons[0].primers) == 2
            assert len(amplicons[1].primers) == 2

            # Check primer directions
            assert len(amplicons[0].forward_primers) == 1
            assert len(amplicons[0].reverse_primers) == 1

        finally:
            test_file.unlink()


class TestConverter:
    """Test the main converter functionality."""

    def create_simple_varvamp_file(self):
        """Create a simple VarVAMP file for testing."""
        content = """amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\tseq\tsize\tgc_best\ttemp_best\tmean_gc\tmean_temp\tscore
amplicon_0\t300\tFW_0\t1\t1\t20\tATCGATCGATCGATCGATCG\t20\t50.0\t60.0\t50.0\t60.0\t1.0
amplicon_0\t300\tRW_0\t1\t280\t300\tCGATCGATCGATCGATCGAT\t20\t50.0\t60.0\t50.0\t60.0\t1.0"""

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False)
        temp_file.write(content)
        temp_file.close()

        return Path(temp_file.name)

    def test_converter_basic_functionality(self):
        """Test basic converter functionality."""
        config = PrePrimerConfig()
        converter = PrimerConverter(config)

        test_file = self.create_simple_varvamp_file()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_files = converter.convert(
                    input_file=test_file,
                    output_dir=Path(temp_dir),
                    input_format="varvamp",
                    output_formats=["fasta"],
                    prefix="TEST",
                )

                assert "fasta" in output_files
                assert output_files["fasta"].exists()

                # Check FASTA content
                content = output_files["fasta"].read_text()
                assert ">TEST_0_LEFT_0" in content
                assert ">TEST_0_RIGHT_0" in content
                assert "ATCGATCGATCGATCGATCG" in content

        finally:
            test_file.unlink()


if __name__ == "__main__":
    # Run basic tests
    test_structures = TestDataStructures()
    test_structures.test_primer_data_creation()
    test_structures.test_amplicon_data_creation()

    test_registry = TestRegistrySystem()
    test_registry.test_parser_registry()
    test_registry.test_writer_registry()
    test_registry.test_parser_instantiation()
    test_registry.test_writer_instantiation()

    test_config = TestConfigSystem()
    test_config.test_default_config()
    test_config.test_config_validation()

    print("✅ All basic tests passed!")
    print("🚀 Refactored preprimer system is working correctly!")
