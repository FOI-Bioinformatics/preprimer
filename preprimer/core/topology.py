"""
Genome topology detection and validation for PrePrimer.

This module handles the detection and validation of genome topology (linear vs circular)
to ensure biologically accurate primer scheme interpretation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class GenomeTopology(Enum):
    """Genome topology types."""
    LINEAR = "linear"
    CIRCULAR = "circular"
    UNKNOWN = "unknown"


@dataclass
class GenomeInfo:
    """Information about a reference genome."""
    reference_id: str
    topology: GenomeTopology
    length: Optional[int] = None
    organism: Optional[str] = None
    description: Optional[str] = None


class TopologyDetector:
    """Detects and validates genome topology from various sources."""
    
    # Known reference genomes and their topologies
    KNOWN_REFERENCES = {
        # Mitochondrial genomes (circular)
        "NC_012920.1": GenomeInfo("NC_012920.1", GenomeTopology.CIRCULAR, 16569, 
                                  "Homo sapiens", "Human mitochondrial genome"),
        
        # Viral genomes (mostly linear)
        "NC_045512.2": GenomeInfo("NC_045512.2", GenomeTopology.LINEAR, 29903,
                                  "SARS-CoV-2", "COVID-19 reference genome"),
        "EPI_ISL_402124": GenomeInfo("EPI_ISL_402124", GenomeTopology.LINEAR, 29903,
                                     "SARS-CoV-2", "Early COVID-19 isolate"),
        "LR722600.1": GenomeInfo("LR722600.1", GenomeTopology.LINEAR, 191232,
                                 "ASFV", "African Swine Fever Virus"),
        
        # Add more as needed
    }
    
    # Organism patterns that suggest topology
    ORGANISM_PATTERNS = {
        "mitochondrion": GenomeTopology.CIRCULAR,
        "mitochondrial": GenomeTopology.CIRCULAR,
        "chloroplast": GenomeTopology.CIRCULAR,
        "plastid": GenomeTopology.CIRCULAR,
    }
    
    @classmethod
    def detect_topology(
        cls,
        reference_id: Optional[str] = None,
        organism: Optional[str] = None,
        metadata: Optional[Dict] = None,
        coordinates: Optional[List[tuple]] = None,
        genome_length: Optional[int] = None
    ) -> GenomeInfo:
        """
        Detect genome topology from available information.
        
        Args:
            reference_id: Reference sequence identifier
            organism: Organism name
            metadata: Metadata dictionary
            coordinates: List of (start, end) coordinate pairs
            genome_length: Known genome length
            
        Returns:
            GenomeInfo with detected topology
        """
        # Method 1: Explicit metadata
        if metadata and "topology" in metadata:
            topology_str = metadata["topology"].lower()
            if topology_str == "linear":
                return GenomeInfo(
                    reference_id or "unknown",
                    GenomeTopology.LINEAR,
                    metadata.get("genome_length", genome_length),
                    metadata.get("organism", organism)
                )
            elif topology_str == "circular":
                return GenomeInfo(
                    reference_id or "unknown", 
                    GenomeTopology.CIRCULAR,
                    metadata.get("genome_length", genome_length),
                    metadata.get("organism", organism)
                )
        
        # Method 2: Known reference lookup
        if reference_id and reference_id in cls.KNOWN_REFERENCES:
            known = cls.KNOWN_REFERENCES[reference_id]
            logger.info(f"Detected {known.topology.value} topology for known reference {reference_id}")
            return known
        
        # Method 3: Organism pattern matching
        if organism:
            organism_lower = organism.lower()
            for pattern, topology in cls.ORGANISM_PATTERNS.items():
                if pattern in organism_lower:
                    logger.info(f"Detected {topology.value} topology from organism pattern '{pattern}' in '{organism}'")
                    return GenomeInfo(
                        reference_id or "unknown",
                        topology,
                        genome_length,
                        organism
                    )
        
        # Method 4: Heuristic detection from coordinates
        if coordinates and genome_length:
            topology = cls._detect_from_coordinates(coordinates, genome_length)
            if topology != GenomeTopology.UNKNOWN:
                logger.warning(f"Detected {topology.value} topology from coordinate analysis - please verify!")
                return GenomeInfo(
                    reference_id or "unknown",
                    topology,
                    genome_length,
                    organism
                )
        
        # Default: Unknown topology
        logger.warning("Could not determine genome topology - assuming linear")
        return GenomeInfo(
            reference_id or "unknown",
            GenomeTopology.LINEAR,  # Default to linear for safety
            genome_length,
            organism
        )
    
    @classmethod
    def _detect_from_coordinates(
        cls,
        coordinates: List[tuple],
        genome_length: int,
        wrap_threshold: float = 0.1
    ) -> GenomeTopology:
        """
        Detect topology from coordinate patterns.
        
        Args:
            coordinates: List of (start, end) coordinate pairs
            genome_length: Genome length
            wrap_threshold: Fraction of genome length to consider as "near boundary"
            
        Returns:
            Detected topology
        """
        if not coordinates or genome_length <= 0:
            return GenomeTopology.UNKNOWN
        
        boundary_distance = int(genome_length * wrap_threshold)
        
        # Look for potential wrapping coordinates
        near_start = []  # Coordinates near genome start (0)
        near_end = []    # Coordinates near genome end
        
        for start, end in coordinates:
            # Check if coordinates are near boundaries
            if start < boundary_distance or end < boundary_distance:
                near_start.append((start, end))
            
            if start > (genome_length - boundary_distance) or end > (genome_length - boundary_distance):
                near_end.append((start, end))
        
        # If we have primers both near start AND end, might be circular
        if near_start and near_end:
            # Additional check: look for coordinates that would only make sense if circular
            for start, end in coordinates:
                # Classic circular wrapping: start > end after accounting for coordinate systems
                if start > end and (start - end) > (genome_length / 2):
                    return GenomeTopology.CIRCULAR
                
                # Another pattern: very high start with very low end
                if start > (genome_length * 0.9) and end < (genome_length * 0.1):
                    return GenomeTopology.CIRCULAR
        
        return GenomeTopology.UNKNOWN
    
    @classmethod
    def validate_coordinates(
        cls,
        coordinates: List[tuple],
        genome_info: GenomeInfo,
        strict: bool = False
    ) -> List[str]:
        """
        Validate coordinates against genome topology.
        
        Args:
            coordinates: List of (start, end) coordinate pairs
            genome_info: Genome topology information
            strict: Whether to raise errors or just warnings
            
        Returns:
            List of validation messages
        """
        warnings = []
        
        if not coordinates:
            return warnings
        
        genome_length = genome_info.length
        topology = genome_info.topology
        
        for i, (start, end) in enumerate(coordinates):
            # Basic coordinate validation
            if genome_length:
                if start < 0 or end < 0:
                    warnings.append(f"Coordinate pair {i+1}: Negative coordinates not allowed")
                
                if start >= genome_length or end >= genome_length:
                    warnings.append(f"Coordinate pair {i+1}: Coordinates exceed genome length {genome_length}")
            
            # Topology-specific validation
            if topology == GenomeTopology.LINEAR:
                # For linear genomes, start should generally be < end
                if start > end:
                    msg = (f"Coordinate pair {i+1}: start ({start}) > end ({end}) "
                           f"on linear genome - this may indicate an error")
                    if strict:
                        raise ValidationError(msg)
                    warnings.append(msg)
                    
                # Check for coordinates that might suggest circular topology
                if genome_length and start > (genome_length * 0.95) and end < (genome_length * 0.05):
                    msg = (f"Coordinate pair {i+1}: High start ({start}) with low end ({end}) "
                           f"on linear genome - check topology specification")
                    warnings.append(msg)
            
            elif topology == GenomeTopology.CIRCULAR:
                # For circular genomes, wrapping coordinates are valid
                if genome_length:
                    # Calculate amplicon length considering circularity
                    if start <= end:
                        amp_length = end - start + 1
                    else:
                        # Wrapping case
                        amp_length = (genome_length - start) + end + 1
                    
                    # Sanity check - amplicon shouldn't be > 50% of genome
                    if amp_length > (genome_length * 0.5):
                        warnings.append(f"Coordinate pair {i+1}: Amplicon length ({amp_length}) "
                                      f"is > 50% of genome ({genome_length}) - verify coordinates")
        
        return warnings
    
    @classmethod
    def load_from_metadata_file(cls, metadata_path: Union[str, Path]) -> Optional[GenomeInfo]:
        """Load genome info from a metadata YAML file."""
        try:
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            
            return cls.detect_topology(
                reference_id=metadata.get('reference_id'),
                organism=metadata.get('organism'),
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Could not load metadata from {metadata_path}: {e}")
            return None


def calculate_amplicon_length(
    start: int,
    end: int,
    topology: GenomeTopology,
    genome_length: Optional[int] = None
) -> int:
    """
    Calculate amplicon length considering genome topology.
    
    Args:
        start: Start coordinate
        end: End coordinate  
        topology: Genome topology
        genome_length: Genome length (required for circular)
        
    Returns:
        Amplicon length
    """
    if topology == GenomeTopology.LINEAR or start <= end:
        # Linear calculation
        return abs(end - start) + 1
    
    elif topology == GenomeTopology.CIRCULAR and genome_length:
        # Circular wrapping calculation
        if start > end:
            return (genome_length - start) + end + 1
        else:
            return end - start + 1
    
    else:
        # Fallback to absolute difference
        logger.warning(f"Cannot calculate amplicon length for topology {topology} "
                      f"without genome length")
        return abs(end - start) + 1