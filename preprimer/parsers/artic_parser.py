"""
ARTIC primer format parser.
"""

from pathlib import Path
from typing import List, Union, Optional
import logging

from ..core.interfaces import PrimerParser, PrimerData, AmpliconData
from ..core.exceptions import ParserError

logger = logging.getLogger(__name__)


class ARTICParser(PrimerParser):
    """Parser for ARTIC primer format (BED format)."""
    
    @property
    def format_name(self) -> str:
        return "artic"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".bed", ".scheme.bed"]
    
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in ARTIC BED format."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 6:
                        return False
                    
                    # Check basic BED format
                    try:
                        int(parts[1])  # start
                        int(parts[2])  # stop
                        int(parts[4])  # pool
                        strand = parts[5]
                        if strand not in ['+', '-']:
                            return False
                    except ValueError:
                        return False
                    
                    # Check ARTIC naming convention
                    primer_name = parts[3]
                    if not ('LEFT' in primer_name or 'RIGHT' in primer_name):
                        return False
                    
                    break  # If first non-comment line passes, assume valid
                
                return True
        
        except Exception as e:
            logger.debug(f"ARTIC validation failed for {file_path}: {e}")
            return False
    
    def parse(self, file_path: Union[str, Path], prefix: str = "") -> List[AmpliconData]:
        """Parse ARTIC primer file."""
        file_path = Path(file_path)
        
        if not self.validate_file(file_path):
            raise ParserError(f"File {file_path} is not a valid ARTIC format")
        
        logger.info(f"Parsing ARTIC file: {file_path}")
        
        amplicons = {}
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) < 7:
                        logger.warning(f"Skipping malformed line: {line}")
                        continue
                    
                    # Extract BED fields
                    reference_id = parts[0]
                    start = int(parts[1])
                    stop = int(parts[2])
                    primer_name = parts[3]
                    pool = int(parts[4])
                    strand = parts[5]
                    sequence = parts[6]
                    
                    # Parse primer name to get amplicon info
                    # Format: PREFIX_AMPLICON_SIDE_ALT
                    # Example: SARS-CoV-2_400_1_LEFT_1
                    name_parts = primer_name.split('_')
                    if len(name_parts) < 4:
                        raise ParserError(f"Invalid ARTIC primer name format: {primer_name}")
                    
                    # Extract amplicon number 
                    amplicon_num = name_parts[-3]  # Second to last before SIDE_ALT
                    amplicon_id = f"amplicon_{amplicon_num}"
                    
                    # Determine direction
                    if 'LEFT' in primer_name:
                        direction = 'forward'
                    elif 'RIGHT' in primer_name:
                        direction = 'reverse'
                    else:
                        raise ParserError(f"Unknown primer side in: {primer_name}")
                    
                    # Create PrimerData object
                    primer = PrimerData(
                        name=primer_name,
                        sequence=sequence,
                        start=start,
                        stop=stop,
                        strand=strand,
                        direction=direction,
                        pool=pool,
                        amplicon_id=amplicon_id,
                        reference_id=reference_id,
                        metadata={'original_name': primer_name}
                    )
                    
                    # Group primers by amplicon
                    if amplicon_id not in amplicons:
                        amplicons[amplicon_id] = AmpliconData(
                            amplicon_id=amplicon_id,
                            primers=[],
                            reference_id=reference_id
                        )
                    
                    amplicons[amplicon_id].primers.append(primer)
        
        except Exception as e:
            raise ParserError(f"Failed to parse ARTIC file {file_path}: {e}")
        
        # Calculate amplicon lengths
        for amplicon in amplicons.values():
            if amplicon.primers:
                starts = [p.start for p in amplicon.primers]
                stops = [p.stop for p in amplicon.primers]
                amplicon.length = max(stops) - min(starts)
        
        amplicon_list = list(amplicons.values())
        logger.info(f"Parsed {len(amplicon_list)} amplicons with {sum(len(a.primers) for a in amplicon_list)} primers")
        
        return amplicon_list
    
    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """Get associated reference file."""
        file_path = Path(file_path)
        
        # Try to find reference file based on ARTIC naming convention
        # Usually: scheme.bed -> scheme.reference.fasta
        if file_path.name.endswith('.scheme.bed'):
            base_name = file_path.name.replace('.scheme.bed', '')
            ref_file = file_path.parent / f"{base_name}.reference.fasta"
            
            if ref_file.exists():
                return ref_file
        
        # Alternative naming
        base_name = file_path.stem
        ref_file = file_path.parent / f"{base_name}.reference.fasta"
        
        return ref_file if ref_file.exists() else None