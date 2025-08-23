"""
Olivar primer format parser.
"""

import csv
from pathlib import Path
from typing import List, Union, Optional
import logging

from ..core.interfaces import PrimerParser, PrimerData, AmpliconData
from ..core.exceptions import ParserError

logger = logging.getLogger(__name__)


class OlivarParser(PrimerParser):
    """Parser for Olivar primer format."""
    
    @property
    def format_name(self) -> str:
        return "olivar"
    
    @property
    def file_extensions(self) -> List[str]:
        return [".csv"]
    
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that file is in Olivar format."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        # Look for typical Olivar naming patterns
        if "olivar-design" in file_path.name.lower():
            return True
        
        try:
            with open(file_path, 'r') as f:
                # Check header for Olivar-specific columns
                header = f.readline().strip().split(',')
                
                # Olivar CSV has these specific columns
                olivar_required = ['amplicon_id', 'fP', 'rP', 'start', 'end']
                olivar_common = ['reference', 'pool', 'amplicon', 'insert']
                
                # Look for Olivar-specific patterns
                header_lower = [col.lower().strip('"') for col in header]
                
                # Check for required columns (forward primer fP, reverse primer rP)
                required_matches = sum(1 for col in olivar_required 
                                     if col.lower() in header_lower)
                
                # Check for common columns
                common_matches = sum(1 for col in olivar_common
                                   if col.lower() in header_lower)
                
                # Must have most required columns and at least one common column
                # Or if we have all 5 required columns, that's sufficient
                return (required_matches >= 5) or (required_matches >= 4 and common_matches >= 1)
        
        except Exception as e:
            logger.debug(f"Olivar validation failed for {file_path}: {e}")
            return False
    
    def parse(self, file_path: Union[str, Path], prefix: str = "") -> List[AmpliconData]:
        """Parse Olivar primer file."""
        file_path = Path(file_path)
        
        if not self.validate_file(file_path):
            raise ParserError(f"File {file_path} is not a valid Olivar format")
        
        logger.info(f"Parsing Olivar file: {file_path}")
        
        amplicons = {}
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                
                # Try to map Olivar column names to our standard format
                header = reader.fieldnames
                col_mapping = self._map_columns(header)
                
                if not col_mapping:
                    raise ParserError("Could not identify required columns in Olivar file")
                
                for row in reader:
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    try:
                        # Olivar CSV has a unique format where each row contains both forward and reverse primers
                        amplicon_id = row.get('amplicon_id', '')
                        reference_id = row.get('reference', prefix or 'olivar_target')
                        pool = int(row.get('pool', 1))
                        
                        # Get primer sequences and positions
                        fwd_seq = row.get('fP', '')  # forward primer
                        rev_seq = row.get('rP', '')  # reverse primer
                        start_pos = int(row.get('start', 0))
                        end_pos = int(row.get('end', 0))
                        
                        if not amplicon_id or not fwd_seq or not rev_seq:
                            logger.warning(f"Skipping incomplete row: missing amplicon_id or primer sequences")
                            continue
                        
                        # Create forward primer
                        fwd_primer = PrimerData(
                            name=f"{amplicon_id}_F",
                            sequence=fwd_seq,
                            start=start_pos,
                            stop=start_pos + len(fwd_seq),
                            strand='+',
                            direction='forward',
                            pool=pool,
                            amplicon_id=amplicon_id,
                            reference_id=reference_id,
                            metadata={
                                'original_data': {k: v for k, v in row.items() if v}
                            }
                        )
                        
                        # Create reverse primer
                        rev_primer = PrimerData(
                            name=f"{amplicon_id}_R",
                            sequence=rev_seq,
                            start=end_pos - len(rev_seq),
                            stop=end_pos,
                            strand='-',
                            direction='reverse',
                            pool=pool,
                            amplicon_id=amplicon_id,
                            reference_id=reference_id,
                            metadata={
                                'original_data': {k: v for k, v in row.items() if v}
                            }
                        )
                        
                        # Group primers by amplicon
                        if amplicon_id not in amplicons:
                            amplicons[amplicon_id] = AmpliconData(
                                amplicon_id=amplicon_id,
                                primers=[],
                                reference_id=reference_id
                            )
                        
                        amplicons[amplicon_id].primers.extend([fwd_primer, rev_primer])
                    
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping malformed row in Olivar file: {e}")
                        continue
        
        except Exception as e:
            raise ParserError(f"Failed to parse Olivar file {file_path}: {e}")
        
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
        
        # Olivar typically generates reference files with _ref suffix
        base_name = file_path.stem.replace('-design', '').replace('olivar-', '')
        
        # Try common Olivar reference file patterns
        possible_refs = [
            file_path.parent / f"{base_name}_ref.fasta",
            file_path.parent / f"{base_name}.reference.fasta", 
            file_path.parent / "reference.fasta"
        ]
        
        for ref_file in possible_refs:
            if ref_file.exists():
                return ref_file
        
        return None
    
    def _map_columns(self, header: List[str]) -> dict:
        """Map Olivar column names to standard names."""
        header_lower = [col.lower().strip('"') for col in header]
        
        mapping = {}
        
        # Define possible column name variations
        column_patterns = {
            'amplicon_id': ['amplicon_id', 'amplicon', 'amp_id', 'region'],
            'primer_id': ['primer_id', 'id', 'name', 'primer_name'],
            'sequence': ['sequence', 'seq', 'primer_seq'],
            'start': ['start', 'begin', 'pos_start', 'start_pos'],
            'end': ['end', 'stop', 'pos_end', 'end_pos'],
            'strand': ['strand', 'orientation', 'dir', 'direction'],
            'pool': ['pool', 'multiplex', 'group']
        }
        
        for std_name, patterns in column_patterns.items():
            for col_idx, col_name in enumerate(header_lower):
                if any(pattern in col_name for pattern in patterns):
                    mapping[std_name] = [header[col_idx]]  # Use original case
                    break
        
        return mapping
    
    def _safe_get(self, row: dict, possible_keys: List[str], default: str = '') -> str:
        """Safely get value from row using possible key names."""
        for key in possible_keys:
            if key in row and row[key]:
                return row[key].strip()
        return default