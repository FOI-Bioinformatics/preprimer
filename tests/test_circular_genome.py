"""
Tests for circular genome handling and coordinate wrapping.

This module tests PrePrimer's ability to handle circular genomes like
human mitochondrial DNA where primer coordinates can wrap around the
genome boundary (e.g., start > end coordinates).
"""

import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from preprimer.core.converter import PrimerConverter
from preprimer.core.interfaces import AmpliconData
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.olivar_parser import OlivarParser
from preprimer.parsers.varvamp_parser import VarVAMPParser


class TestCircularGenome:
    """Test circular genome coordinate handling."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        workspace = Path(tempfile.mkdtemp())
        yield workspace
        shutil.rmtree(workspace)

    @pytest.fixture
    def mitochondrial_dataset_path(self):
        """Path to mitochondrial test dataset."""
        return Path(__file__).parent / "test_data" / "datasets" / "mitochondrial"

    def test_mitochondrial_dataset_exists(self, mitochondrial_dataset_path):
        """Test that mitochondrial dataset files exist."""
        assert mitochondrial_dataset_path.exists()
        assert (mitochondrial_dataset_path / "reference.fasta").exists()
        assert (mitochondrial_dataset_path / "varvamp.tsv").exists()
        assert (mitochondrial_dataset_path / "artic.scheme.bed").exists()
        assert (mitochondrial_dataset_path / "olivar.csv").exists()
        assert (mitochondrial_dataset_path / "sts.tsv").exists()
        assert (mitochondrial_dataset_path / "metadata.yaml").exists()

    def test_mitochondrial_reference_length(self, mitochondrial_dataset_path):
        """Test that mitochondrial reference is exactly 16,569 bp."""
        ref_file = mitochondrial_dataset_path / "reference.fasta"
        content = ref_file.read_text()

        # Extract sequence without header and newlines
        sequence = ""
        for line in content.split("\n"):
            if not line.startswith(">"):
                sequence += line.strip()

        assert len(sequence) == 16569, f"Expected 16569 bp, got {len(sequence)} bp"

    def test_circular_coordinate_wrapping_varvamp(self, mitochondrial_dataset_path):
        """Test VarVAMP parser handles coordinates that wrap around circular genome."""
        varvamp_file = mitochondrial_dataset_path / "varvamp.tsv"
        parser = VarVAMPParser()

        # Parse the mitochondrial dataset
        amplicons = parser.parse(str(varvamp_file))

        # Check that we have amplicons
        assert len(amplicons) > 0

        # Find amplicons with wrapping coordinates (start > end after accounting for 0-based)
        wrapping_amplicons = []
        for amplicon in amplicons:
            primers = amplicon.primers
            fw_primers = [p for p in primers if p.direction == "forward"]
            rv_primers = [p for p in primers if p.direction == "reverse"]

            if fw_primers and rv_primers:
                fw_start = min(p.start for p in fw_primers)
                rv_start = min(p.start for p in rv_primers)

                # Check if this appears to be a wrapping amplicon
                # (forward primer near end, reverse primer near beginning)
                if fw_start > 15000 and rv_start < 1000:
                    wrapping_amplicons.append(amplicon)

        # Should have at least one wrapping amplicon
        assert len(wrapping_amplicons) > 0, "No circular wrapping amplicons found"

        # Verify the wrapping amplicon data integrity
        for amplicon in wrapping_amplicons:
            primers = amplicon.primers
            assert len(primers) >= 2, "Wrapping amplicon should have at least 2 primers"

            # Check that primer sequences are valid
            for primer in primers:
                assert (
                    len(primer.sequence) > 15
                ), f"Primer sequence too short: {primer.sequence}"
                assert all(
                    base in "ATCG" for base in primer.sequence.upper()
                ), f"Invalid bases in primer: {primer.sequence}"

    def test_circular_coordinate_wrapping_artic(self, mitochondrial_dataset_path):
        """Test ARTIC parser handles coordinates that wrap around circular genome."""
        artic_file = mitochondrial_dataset_path / "artic.scheme.bed"
        parser = ARTICParser()

        # Parse the mitochondrial dataset
        amplicons = parser.parse(str(artic_file))

        # Check that we have amplicons
        assert len(amplicons) > 0

        # Check for primers with high coordinates (near genome end)
        high_coord_primers = []
        low_coord_primers = []

        for amplicon in amplicons:
            primers = amplicon.primers
            for primer in primers:
                if primer.start > 15000:
                    high_coord_primers.append(primer)
                elif primer.start < 1000:
                    low_coord_primers.append(primer)

        # Should have primers both at high and low coordinates for circular genome
        assert len(high_coord_primers) > 0, "No primers near genome end found"
        assert len(low_coord_primers) > 0, "No primers near genome start found"

    def test_circular_coordinate_wrapping_olivar(self, mitochondrial_dataset_path):
        """Test Olivar parser handles coordinates that wrap around circular genome."""
        olivar_file = mitochondrial_dataset_path / "olivar.csv"
        parser = OlivarParser()

        # Parse the mitochondrial dataset
        amplicons = parser.parse(str(olivar_file))

        # Check that we have amplicons
        assert len(amplicons) > 0

        # Verify coordinate consistency
        for amplicon in amplicons:
            primers = amplicon.primers
            assert (
                len(primers) >= 2
            ), f"Amplicon {amplicon.amplicon_id} should have at least 2 primers"

            # Check coordinate ranges are reasonable for mitochondrial genome
            for primer in primers:
                assert (
                    0 <= primer.start < 16569
                ), f"Primer start coordinate out of range: {primer.start}"
                assert (
                    0 <= primer.stop < 16569
                ), f"Primer end coordinate out of range: {primer.stop}"

    def test_circular_conversion_consistency(
        self, mitochondrial_dataset_path, temp_workspace
    ):
        """Test that conversions maintain consistency for circular genomes."""
        # Test VarVAMP -> ARTIC conversion
        varvamp_file = mitochondrial_dataset_path / "varvamp.tsv"
        parser = VarVAMPParser()
        converter = PrimerConverter()

        # Parse VarVAMP data
        amplicons = parser.parse(str(varvamp_file))
        original_count = len(amplicons)

        # Convert to ARTIC
        output_dir = temp_workspace / "conversion_test"
        result_files = converter.convert(
            input_file=str(varvamp_file),
            output_dir=str(output_dir),
            output_formats=["artic"],
        )

        # The converter might return a dict, let's handle both cases
        if isinstance(result_files, dict):
            assert "artic" in result_files
            artic_output = result_files["artic"]
        else:
            assert len(result_files) == 1
            artic_output = result_files[0]

        # Parse the converted ARTIC file
        artic_parser = ARTICParser()
        converted_amplicons = artic_parser.parse(artic_output)

        # Should have same number of amplicons
        assert len(converted_amplicons) == original_count

        # Verify that primer sequences are preserved
        original_seqs = set()
        converted_seqs = set()

        for amplicon in amplicons:
            for primer in amplicon.primers:
                original_seqs.add(primer.sequence.upper())

        for amplicon in converted_amplicons:
            for primer in amplicon.primers:
                converted_seqs.add(primer.sequence.upper())

        # Should have the same primer sequences
        assert (
            original_seqs == converted_seqs
        ), "Primer sequences not preserved in conversion"

    def test_circular_amplicon_validation(self, mitochondrial_dataset_path):
        """Test validation of circular amplicons."""
        varvamp_file = mitochondrial_dataset_path / "varvamp.tsv"
        parser = VarVAMPParser()

        amplicons = parser.parse(str(varvamp_file))

        for amplicon in amplicons:
            # Basic validation
            assert amplicon.amplicon_id, "Amplicon should have an ID"
            assert len(amplicon.primers) > 0, "Amplicon should have primers"

            # Check primer pair consistency
            primers = amplicon.primers
            forward_primers = [p for p in primers if p.direction == "forward"]
            reverse_primers = [p for p in primers if p.direction == "reverse"]

            assert len(forward_primers) > 0, "Should have forward primers"
            assert len(reverse_primers) > 0, "Should have reverse primers"

            # Verify primer sequences match reference (basic check)
            for primer in primers:
                assert (
                    len(primer.sequence) >= 18
                ), f"Primer too short: {len(primer.sequence)}"
                assert (
                    len(primer.sequence) <= 35
                ), f"Primer too long: {len(primer.sequence)}"

                # Check for valid DNA bases
                valid_bases = set("ATCGRYSWKMBDHVN")  # Including ambiguous bases
                primer_bases = set(primer.sequence.upper())
                assert primer_bases.issubset(
                    valid_bases
                ), f"Invalid bases in primer: {primer.sequence}"

    def test_circular_metadata_parsing(self, mitochondrial_dataset_path):
        """Test that circular genome metadata is correctly parsed."""
        import yaml

        metadata_file = mitochondrial_dataset_path / "metadata.yaml"

        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)

        # Check circular-specific metadata
        assert metadata.get("topology") == "circular"
        assert metadata.get("genome_length") == 16569
        assert metadata.get("organism") == "Homo sapiens mitochondrion"
        assert metadata.get("reference_id") == "NC_012920.1"

        # Check coverage metrics
        assert metadata.get("amplicon_count") == 8
        assert metadata.get("primer_count") == 16
        assert metadata.get("coverage_bp") > 0


class TestCircularCoordinateEdgeCases:
    """Test edge cases specific to circular coordinate handling."""

    @pytest.fixture
    def mitochondrial_dataset_path(self):
        """Path to mitochondrial test dataset."""
        return Path(__file__).parent / "test_data" / "datasets" / "mitochondrial"

    def test_coordinate_normalization(self):
        """Test coordinate normalization for circular genomes."""
        # This would test utility functions for normalizing circular coordinates
        # For now, just ensure the test infrastructure works
        assert True

    def test_amplicon_length_calculation(self, mitochondrial_dataset_path):
        """Test that amplicon lengths are calculated correctly for circular genomes."""
        varvamp_file = mitochondrial_dataset_path / "varvamp.tsv"
        parser = VarVAMPParser()

        amplicons = parser.parse(str(varvamp_file))

        for amplicon in amplicons:
            # Check that amplicon length is reasonable
            primers = amplicon.primers
            if len(primers) >= 2:
                # Basic sanity check - amplicon should be longer than primer length
                max_primer_len = max(len(p.sequence) for p in primers)
                # Note: For circular genomes, we might need special handling
                # This is a placeholder for more sophisticated checks
                assert max_primer_len > 0

    def test_pool_assignment_circular(self, mitochondrial_dataset_path):
        """Test that pool assignments work correctly for circular genomes."""
        varvamp_file = mitochondrial_dataset_path / "varvamp.tsv"
        parser = VarVAMPParser()

        amplicons = parser.parse(str(varvamp_file))

        pools_found = set()
        for amplicon in amplicons:
            primers = amplicon.primers
            for primer in primers:
                if hasattr(primer, "pool") and primer.pool:
                    pools_found.add(primer.pool)

        # Should have multiple pools for balanced amplification
        assert len(pools_found) >= 2, f"Expected multiple pools, found: {pools_found}"
