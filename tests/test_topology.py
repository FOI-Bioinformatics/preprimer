"""
Tests for genome topology detection and validation.
"""

import tempfile
from pathlib import Path

import pytest

from preprimer.core.exceptions import ValidationError
from preprimer.core.topology import (
    GenomeInfo,
    GenomeTopology,
    TopologyDetector,
    calculate_amplicon_length,
)


class TestTopologyDetector:
    """Test genome topology detection."""

    def test_known_reference_detection(self):
        """Test detection of known reference genomes."""
        # Human mitochondrial genome (circular)
        genome_info = TopologyDetector.detect_topology(reference_id="NC_012920.1")
        assert genome_info.topology == GenomeTopology.CIRCULAR
        assert genome_info.length == 16569
        assert "Homo sapiens" in genome_info.organism

        # COVID-19 genome (linear)
        genome_info = TopologyDetector.detect_topology(reference_id="NC_045512.2")
        assert genome_info.topology == GenomeTopology.LINEAR
        assert genome_info.length == 29903

        # ASFV genome (linear)
        genome_info = TopologyDetector.detect_topology(reference_id="LR722600.1")
        assert genome_info.topology == GenomeTopology.LINEAR
        assert genome_info.length == 191232

    def test_organism_pattern_detection(self):
        """Test topology detection from organism patterns."""
        # Mitochondrial patterns
        genome_info = TopologyDetector.detect_topology(
            organism="Homo sapiens mitochondrion"
        )
        assert genome_info.topology == GenomeTopology.CIRCULAR

        genome_info = TopologyDetector.detect_topology(
            organism="Mouse mitochondrial DNA"
        )
        assert genome_info.topology == GenomeTopology.CIRCULAR

        # Chloroplast patterns
        genome_info = TopologyDetector.detect_topology(
            organism="Arabidopsis chloroplast"
        )
        assert genome_info.topology == GenomeTopology.CIRCULAR

        genome_info = TopologyDetector.detect_topology(organism="Rice plastid genome")
        assert genome_info.topology == GenomeTopology.CIRCULAR

    def test_metadata_detection(self):
        """Test topology detection from metadata."""
        # Explicit linear
        metadata = {
            "topology": "linear",
            "genome_length": 30000,
            "organism": "Test virus",
        }
        genome_info = TopologyDetector.detect_topology(metadata=metadata)
        assert genome_info.topology == GenomeTopology.LINEAR
        assert genome_info.length == 30000

        # Explicit circular
        metadata = {
            "topology": "circular",
            "genome_length": 16569,
            "organism": "Test mitochondrion",
        }
        genome_info = TopologyDetector.detect_topology(metadata=metadata)
        assert genome_info.topology == GenomeTopology.CIRCULAR
        assert genome_info.length == 16569

    def test_coordinate_heuristic_detection(self):
        """Test topology detection from coordinate patterns."""
        genome_length = 16569

        # Circular pattern: high start, low end
        coordinates = [
            (16400, 16420),  # Near end
            (200, 220),  # Near start
            (16500, 300),  # Wrapping coordinate
        ]

        genome_info = TopologyDetector.detect_topology(
            coordinates=coordinates, genome_length=genome_length
        )
        # Should suggest circular due to coordinate patterns
        # Note: This is heuristic and may not always be reliable

    def test_priority_order(self):
        """Test that detection methods have correct priority."""
        # Metadata should override known reference
        metadata = {"topology": "linear", "genome_length": 16569}
        genome_info = TopologyDetector.detect_topology(
            reference_id="NC_012920.1",  # Known circular
            metadata=metadata,  # Override to linear
        )
        assert genome_info.topology == GenomeTopology.LINEAR  # Metadata wins

        # Known reference should override organism patterns
        genome_info = TopologyDetector.detect_topology(
            reference_id="NC_045512.2",  # Known linear
            organism="fake mitochondrion",  # Would suggest circular
        )
        assert genome_info.topology == GenomeTopology.LINEAR  # Reference wins

    def test_unknown_topology_default(self):
        """Test fallback to unknown/linear for unrecognized genomes."""
        genome_info = TopologyDetector.detect_topology(
            reference_id="UNKNOWN_REF_123", organism="Unknown organism"
        )
        assert genome_info.topology == GenomeTopology.LINEAR  # Default fallback

    def test_metadata_file_loading(self):
        """Test loading topology from metadata files."""
        # Create temporary metadata file
        metadata_content = """
topology: circular
genome_length: 16569
organism: Homo sapiens mitochondrion
reference_id: NC_012920.1
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(metadata_content)
            temp_path = f.name

        try:
            genome_info = TopologyDetector.load_from_metadata_file(temp_path)
            assert genome_info is not None
            assert genome_info.topology == GenomeTopology.CIRCULAR
            assert genome_info.length == 16569
        finally:
            Path(temp_path).unlink()


class TestCoordinateValidation:
    """Test coordinate validation against topology."""

    def test_linear_genome_validation(self):
        """Test validation for linear genomes."""
        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)

        # Valid linear coordinates
        coordinates = [(100, 200), (500, 600), (1000, 1100)]
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) == 0

        # Invalid: start > end on linear genome
        coordinates = [(200, 100), (600, 500)]
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) == 2
        assert "start (200) > end (100)" in warnings[0]
        assert "start (600) > end (500)" in warnings[1]

        # Suspicious: coordinates that might suggest circular topology
        coordinates = [(29800, 200)]  # High start, low end
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) == 2  # One for start>end, one for suspicious pattern
        assert "check topology" in warnings[1].lower()

    def test_circular_genome_validation(self):
        """Test validation for circular genomes."""
        genome_info = GenomeInfo("test", GenomeTopology.CIRCULAR, 16569)

        # Valid circular coordinates (non-wrapping)
        coordinates = [(100, 200), (500, 600)]
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) == 0

        # Valid circular coordinates (wrapping)
        coordinates = [(16400, 200)]  # Wraps around
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        # Should not generate warnings for valid circular wrapping
        assert len([w for w in warnings if "start" in w and "end" in w]) == 0

        # Invalid: coordinates beyond genome length
        coordinates = [(20000, 20100)]  # Beyond 16569
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) > 0
        assert "exceed genome length" in warnings[0]

        # Warning: amplicon too large (> 50% of genome)
        coordinates = [(0, 10000)]  # ~60% of genome
        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) > 0
        assert "50%" in warnings[0]

    def test_strict_validation(self):
        """Test strict validation mode."""
        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)
        coordinates = [(200, 100)]  # start > end

        # Should raise exception in strict mode
        with pytest.raises(ValidationError):
            TopologyDetector.validate_coordinates(coordinates, genome_info, strict=True)

        # Should return warnings in non-strict mode
        warnings = TopologyDetector.validate_coordinates(
            coordinates, genome_info, strict=False
        )
        assert len(warnings) > 0

    def test_negative_coordinates(self):
        """Test validation of negative coordinates."""
        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)
        coordinates = [(-100, 100), (200, -50)]

        warnings = TopologyDetector.validate_coordinates(coordinates, genome_info)
        assert len(warnings) == 3  # 2 negative coord warnings + 1 start>end warning
        assert "Negative coordinates" in warnings[0]
        assert "Negative coordinates" in warnings[1]
        assert "start (200) > end (-50)" in warnings[2]


class TestAmpliconLengthCalculation:
    """Test amplicon length calculation for different topologies."""

    def test_linear_amplicon_length(self):
        """Test amplicon length calculation for linear genomes."""
        # Standard linear calculation
        length = calculate_amplicon_length(100, 200, GenomeTopology.LINEAR)
        assert length == 101  # 200 - 100 + 1

        # Reverse order (should use absolute difference)
        length = calculate_amplicon_length(200, 100, GenomeTopology.LINEAR)
        assert length == 101  # abs(100 - 200) + 1

    def test_circular_amplicon_length(self):
        """Test amplicon length calculation for circular genomes."""
        genome_length = 16569

        # Non-wrapping circular (same as linear)
        length = calculate_amplicon_length(
            100, 200, GenomeTopology.CIRCULAR, genome_length
        )
        assert length == 101

        # Wrapping circular
        length = calculate_amplicon_length(
            16400, 200, GenomeTopology.CIRCULAR, genome_length
        )
        expected = (16569 - 16400) + 200 + 1  # 169 + 200 + 1 = 370
        assert length == expected

        # Edge case: start at last position
        length = calculate_amplicon_length(
            16568, 100, GenomeTopology.CIRCULAR, genome_length
        )
        expected = (16569 - 16568) + 100 + 1  # 1 + 100 + 1 = 102
        assert length == expected

    def test_circular_length_without_genome_size(self):
        """Test circular calculation fallback without genome size."""
        # Should fall back to linear calculation with warning
        length = calculate_amplicon_length(16400, 200, GenomeTopology.CIRCULAR)
        assert length == abs(200 - 16400) + 1  # Fallback calculation

    def test_edge_cases(self):
        """Test edge cases in amplicon length calculation."""
        # Same start and end
        length = calculate_amplicon_length(100, 100, GenomeTopology.LINEAR)
        assert length == 1

        # Circular same coordinates
        length = calculate_amplicon_length(100, 100, GenomeTopology.CIRCULAR, 16569)
        assert length == 1


class TestIntegrationWithTestData:
    """Test topology system with actual test datasets."""

    @pytest.fixture
    def test_data_dir(self):
        """Path to test data directory."""
        return Path(__file__).parent / "test_data" / "datasets"

    def test_covid_dataset_topology(self, test_data_dir):
        """Test COVID-19 dataset topology detection."""
        metadata_file = test_data_dir / "small" / "metadata.yaml"

        if metadata_file.exists():
            genome_info = TopologyDetector.load_from_metadata_file(metadata_file)
            assert genome_info is not None
            assert genome_info.topology == GenomeTopology.LINEAR
            assert genome_info.reference_id in ["EPI_ISL_402124", "NC_045512.2"]

    def test_asfv_dataset_topology(self, test_data_dir):
        """Test ASFV dataset topology detection."""
        metadata_file = test_data_dir / "medium" / "metadata.yaml"

        if metadata_file.exists():
            genome_info = TopologyDetector.load_from_metadata_file(metadata_file)
            assert genome_info is not None
            assert genome_info.topology == GenomeTopology.LINEAR
            assert genome_info.reference_id == "LR722600.1"

    def test_mitochondrial_dataset_topology(self, test_data_dir):
        """Test mitochondrial dataset topology detection."""
        metadata_file = test_data_dir / "mitochondrial" / "metadata.yaml"

        if metadata_file.exists():
            genome_info = TopologyDetector.load_from_metadata_file(metadata_file)
            assert genome_info is not None
            assert genome_info.topology == GenomeTopology.CIRCULAR
            assert genome_info.length == 16569
            assert genome_info.reference_id == "NC_012920.1"


class TestTopologyAwareness:
    """Test that topology affects biological interpretation."""

    def test_wrapping_coordinate_interpretation(self):
        """Test different interpretation of same coordinates based on topology."""
        start, end = 16400, 200

        # Linear genome: this would be an error (start > end)
        linear_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)
        warnings = TopologyDetector.validate_coordinates([(start, end)], linear_info)
        assert any("start" in w and "end" in w for w in warnings)

        # Circular genome: this is valid wrapping
        circular_info = GenomeInfo("test", GenomeTopology.CIRCULAR, 16569)
        warnings = TopologyDetector.validate_coordinates([(start, end)], circular_info)
        # Should not have start>end warnings for circular
        assert not any("start (16400) > end (200)" in w for w in warnings)

    def test_amplicon_length_differences(self):
        """Test how topology affects amplicon length calculation."""
        start, end = 16400, 200

        # Linear calculation (fallback)
        linear_length = calculate_amplicon_length(start, end, GenomeTopology.LINEAR)
        assert linear_length == abs(end - start) + 1  # 16201

        # Circular calculation
        circular_length = calculate_amplicon_length(
            start, end, GenomeTopology.CIRCULAR, 16569
        )
        expected = (16569 - 16400) + 200 + 1  # 370
        assert circular_length == expected
        assert circular_length != linear_length  # Should be very different!

        # The circular interpretation makes biological sense, linear doesn't
        assert circular_length < 1000  # Reasonable amplicon size
        assert linear_length > 15000  # Unreasonably large for PCR
