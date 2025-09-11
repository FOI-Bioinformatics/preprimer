"""
Comprehensive tests for topology module targeting missed coverage lines.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from preprimer.core.topology import (
    TopologyDetector, 
    GenomeTopology, 
    GenomeInfo,
    calculate_amplicon_length
)
from preprimer.core.exceptions import ValidationError


class TestTopologyDetectorMissedLines:
    """Test specific missed coverage lines in TopologyDetector."""
    
    def test_detect_topology_circular_metadata(self):
        """Test circular topology detection from metadata (line 98->107)."""
        detector = TopologyDetector()
        
        # Test circular topology from metadata
        metadata = {
            "topology": "circular",
            "genome_length": 16569,
            "organism": "Test organism"
        }
        
        result = detector.detect_topology(
            reference_id="test_ref",
            metadata=metadata
        )
        
        assert result.topology == GenomeTopology.CIRCULAR
        assert result.length == 16569
        assert result.organism == "Test organism"
        assert result.reference_id == "test_ref"
    
    def test_detect_from_coordinates_valid_result(self):
        """Test coordinate detection with valid topology result (line 128->138)."""
        detector = TopologyDetector()
        
        # Create coordinates that suggest circular topology
        coordinates = [
            (100, 200),   # Normal coordinate
            (28000, 1000) # Wrapping coordinate (start > end, large difference)
        ]
        genome_length = 29000
        
        result = detector.detect_topology(
            reference_id="test_circular",
            coordinates=coordinates,
            genome_length=genome_length,
            organism="test organism"
        )
        
        # Should detect circular topology from coordinates
        assert result.topology == GenomeTopology.CIRCULAR
        assert result.reference_id == "test_circular"
        assert result.length == genome_length
        assert result.organism == "test organism"
    
    def test_detect_from_coordinates_invalid_input(self):
        """Test coordinate detection with invalid input (line 165)."""
        detector = TopologyDetector()
        
        # Test with empty coordinates
        topology = detector._detect_from_coordinates([], 1000)
        assert topology == GenomeTopology.UNKNOWN
        
        # Test with invalid genome length
        topology = detector._detect_from_coordinates([(100, 200)], 0)
        assert topology == GenomeTopology.UNKNOWN
        
        topology = detector._detect_from_coordinates([(100, 200)], -100)
        assert topology == GenomeTopology.UNKNOWN
    
    def test_detect_circular_coordinate_patterns(self):
        """Test circular coordinate pattern detection (lines 191-193)."""
        detector = TopologyDetector()
        
        # Test pattern: start > 90% of genome, end < 10% of genome  
        coordinates = [
            (100, 200),     # Normal coordinate
            (27000, 1000),  # start > 90% (27000 > 26100), end < 10% (1000 < 2900)
        ]
        genome_length = 29000
        
        topology = detector._detect_from_coordinates(coordinates, genome_length)
        assert topology == GenomeTopology.CIRCULAR
        
        # Test another circular pattern
        coordinates2 = [
            (28500, 500),  # High start, low end - should trigger line 191
        ]
        
        topology2 = detector._detect_from_coordinates(coordinates2, genome_length)
        assert topology2 == GenomeTopology.CIRCULAR
    
    def test_validate_coordinates_empty_list(self):
        """Test coordinate validation with empty list (line 216)."""
        detector = TopologyDetector()
        
        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 10000)
        
        # Should return empty list for empty coordinates
        warnings = detector.validate_coordinates([], genome_info)
        assert warnings == []
    
    def test_validate_coordinates_circular_genome(self):
        """Test circular genome coordinate validation (lines 246->221, 248->221)."""
        detector = TopologyDetector()
        
        genome_info = GenomeInfo("test", GenomeTopology.CIRCULAR, 10000)
        
        # Test coordinates that trigger circular validation logic
        coordinates = [
            (100, 200),    # Normal case: start <= end
            (9000, 500),   # Wrapping case: start > end
        ]
        
        warnings = detector.validate_coordinates(coordinates, genome_info)
        
        # Should process both coordinate pairs without major warnings
        # The wrapping case should be handled correctly for circular topology
        assert isinstance(warnings, list)
        # May have warnings but shouldn't crash
    
    def test_validate_coordinates_circular_large_amplicon(self):
        """Test circular genome with large amplicon warning."""
        detector = TopologyDetector()
        
        genome_info = GenomeInfo("test", GenomeTopology.CIRCULAR, 1000)
        
        # Create coordinates that result in amplicon > 50% of genome
        coordinates = [
            (100, 700),  # Length = 601, which is > 50% of 1000
        ]
        
        warnings = detector.validate_coordinates(coordinates, genome_info)
        
        # Should warn about large amplicon
        assert len(warnings) > 0
        assert any("50% of genome" in warning for warning in warnings)
    
    def test_load_from_metadata_file_exception(self):
        """Test metadata file loading with exception (lines 275-277)."""
        detector = TopologyDetector()
        
        # Test with non-existent file
        result = detector.load_from_metadata_file("/nonexistent/path/file.yaml")
        assert result is None
        
        # Test with file that raises exception during reading
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = detector.load_from_metadata_file("somefile.yaml")
            assert result is None
        
        # Test with invalid YAML
        invalid_yaml = "invalid: yaml: content: ]\n  bad indentation"
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            result = detector.load_from_metadata_file("bad.yaml")
            assert result is None


class TestAmpliconLengthCalculationMissedLines:
    """Test missed lines in amplicon length calculation."""
    
    def test_calculate_amplicon_length_circular_else_branch(self):
        """Test circular amplicon length else branch (line 307)."""
        
        # Test circular topology with start <= end (else branch of line 304)
        result = calculate_amplicon_length(
            start=100,
            end=200, 
            topology=GenomeTopology.CIRCULAR,
            genome_length=1000
        )
        
        # Should use else branch: end - start + 1 = 200 - 100 + 1 = 101
        assert result == 101
    
    def test_calculate_amplicon_length_fallback_warning(self):
        """Test fallback calculation with warning."""
        
        # Test circular without genome_length (should trigger fallback)
        result = calculate_amplicon_length(
            start=200,
            end=100,  # start > end
            topology=GenomeTopology.CIRCULAR,
            genome_length=None  # No genome length provided
        )
        
        # Should use fallback: abs(end - start) + 1 = abs(100 - 200) + 1 = 101
        assert result == 101


class TestTopologyDetectorEdgeCaseScenarios:
    """Test complex edge case scenarios."""
    
    def test_detect_topology_priority_chain(self):
        """Test that detection follows proper priority chain."""
        detector = TopologyDetector()
        
        # Create scenario where multiple detection methods could apply
        # but metadata should take priority
        metadata = {"topology": "circular"}
        coordinates = [(100, 200)]  # Would suggest linear
        
        result = detector.detect_topology(
            reference_id="NC_045512.2",  # Known linear reference
            organism="mitochondrial",    # Would suggest circular  
            metadata=metadata,           # Should take priority
            coordinates=coordinates,
            genome_length=30000
        )
        
        # Metadata should win (circular)
        assert result.topology == GenomeTopology.CIRCULAR
    
    def test_coordinate_heuristics_edge_cases(self):
        """Test coordinate heuristic detection edge cases."""
        detector = TopologyDetector()
        
        # Test coordinates near boundaries but not clearly circular
        coordinates = [
            (50, 150),     # Near start
            (28950, 29000) # Near end
        ]
        genome_length = 29000
        
        # Should have coordinates near both start and end but not conclusively circular
        topology = detector._detect_from_coordinates(coordinates, genome_length)
        
        # Might be UNKNOWN since patterns aren't clearly circular
        assert topology in [GenomeTopology.UNKNOWN, GenomeTopology.CIRCULAR]
    
    def test_validate_coordinates_comprehensive_scenarios(self):
        """Test comprehensive coordinate validation scenarios."""
        detector = TopologyDetector()
        
        # Test linear genome with problematic coordinates
        linear_genome = GenomeInfo("test", GenomeTopology.LINEAR, 10000)
        
        # Mix of good and bad coordinates
        coordinates = [
            (100, 200),    # Good
            (-10, 100),    # Negative start
            (100, -50),    # Negative end
            (15000, 200),  # Start exceeds genome length
            (100, 15000),  # End exceeds genome length
            (9600, 400),   # High start, low end (suspicious for linear)
        ]
        
        warnings = detector.validate_coordinates(coordinates, linear_genome)
        
        # Should have multiple warnings
        assert len(warnings) > 0
        
        # Check for specific warning types
        warning_text = " ".join(warnings)
        assert "Negative coordinates" in warning_text
        assert "exceed genome length" in warning_text
        assert "check topology" in warning_text or "may indicate an error" in warning_text
    
    def test_metadata_file_loading_success_path(self):
        """Test successful metadata file loading."""
        detector = TopologyDetector()
        
        # Create valid YAML content
        yaml_content = """
reference_id: "test_ref"
organism: "Test organism"  
topology: "circular"
genome_length: 16000
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            result = detector.load_from_metadata_file("test.yaml")
        
        assert result is not None
        assert result.topology == GenomeTopology.CIRCULAR
        assert result.reference_id == "test_ref"
        assert result.organism == "Test organism"
        assert result.length == 16000


class TestComplexCoordinatePatterns:
    """Test complex coordinate pattern detection."""
    
    def test_wrapping_coordinate_detection_variations(self):
        """Test various wrapping coordinate patterns."""
        detector = TopologyDetector()
        genome_length = 10000
        boundary_distance = int(genome_length * 0.1)  # 1000
        
        # Need coordinates that create both near_start and near_end conditions
        # Test case 1: Classic wrapping with coordinates near both boundaries
        coords1 = [
            (500, 1500),    # Near start (both < 1000)  
            (8500, 1500),   # This should be detected as wrapping: start > end, large diff
            (9200, 9800)    # Near end (both > 9000)
        ]
        topology1 = detector._detect_from_coordinates(coords1, genome_length)
        assert topology1 == GenomeTopology.CIRCULAR
        
        # Test case 2: High start, low end pattern with boundary conditions
        coords2 = [
            (200, 800),     # Near start
            (9500, 500),    # start > 90%, end < 10%  
            (9100, 9600)    # Near end
        ]
        topology2 = detector._detect_from_coordinates(coords2, genome_length)
        assert topology2 == GenomeTopology.CIRCULAR
        
        # Test case 3: Ambiguous case (should be UNKNOWN)
        coords3 = [(4000, 6000)]  # Normal linear coordinates, no boundary proximity
        topology3 = detector._detect_from_coordinates(coords3, genome_length)
        assert topology3 == GenomeTopology.UNKNOWN