"""
Performance-optimized parser base class with caching and batch processing.
"""

import logging
import re
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set
from functools import lru_cache

from .exceptions import ParserError, SecurityError, InvalidFormatError
from .interfaces import AmpliconData, PrimerData, PrimerParser
from .security import InputValidator, PathValidator
from .standardized_parser import StandardizedParser

logger = logging.getLogger(__name__)


class OptimizedParser(StandardizedParser):
    """
    Performance-optimized parser with caching and batch processing.
    
    Key optimizations:
    1. String sanitization caching - avoids reprocessing identical strings
    2. Compiled regex patterns - faster pattern matching
    3. Batch validation - reduces overhead for large datasets
    4. Memory-efficient data structures
    """
    
    def __init__(self):
        """Initialize optimized parser with caching enabled."""
        super().__init__()
        
        # Pre-compile regex patterns for better performance
        self._invalid_chars_pattern = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]')
        self._whitespace_pattern = re.compile(r'\s+')
        self._primer_direction_pattern = re.compile(r'^(FW|RW)_')
        
        # Caches for performance optimization
        self._string_cache: Dict[str, str] = {}
        self._validation_cache: Dict[str, bool] = {}
        
        # Statistics tracking
        self._cache_hits = 0
        self._cache_misses = 0
    
    @lru_cache(maxsize=10000)
    def _sanitize_string_cached(self, text: str, max_length: int = 1000) -> str:
        """
        Cache-optimized string sanitization.
        
        Uses LRU cache to avoid reprocessing identical strings,
        which is common with amplicon names and repeated sequences.
        """
        if not text:
            return ""
        
        # Trim to max length first (most efficient)
        if len(text) > max_length:
            text = text[:max_length]
        
        # Fast path for already clean strings (common case)
        if not self._invalid_chars_pattern.search(text):
            return text.strip()
        
        # Clean invalid characters
        cleaned = self._invalid_chars_pattern.sub('_', text)
        
        # Normalize whitespace  
        cleaned = self._whitespace_pattern.sub(' ', cleaned).strip()
        
        return cleaned
    
    def _sanitize_string_field_optimized(
        self, value: Any, field_name: str, row_num: int, max_length: int = 1000
    ) -> str:
        """
        Optimized string field sanitization with caching.
        
        Performance improvements:
        1. Early type checking
        2. Cached sanitization
        3. Reduced string operations
        """
        if not value:
            raise InvalidFormatError(
                "unknown_file",
                expected_format="valid string",
                user_message=f"Missing required field '{field_name}' in row {row_num}."
            )
        
        # Convert to string efficiently
        if isinstance(value, str):
            text = value
        else:
            text = str(value)
        
        # Use cached sanitization
        cache_key = f"{text}:{max_length}"
        if cache_key in self._string_cache:
            self._cache_hits += 1
            return self._string_cache[cache_key]
        
        self._cache_misses += 1
        sanitized = self._sanitize_string_cached(text, max_length)
        
        # Cache result for future use
        if len(self._string_cache) < 50000:  # Prevent memory bloat
            self._string_cache[cache_key] = sanitized
        
        return sanitized
    
    @lru_cache(maxsize=1000)
    def _get_primer_direction_cached(self, primer_name: str) -> tuple[str, str]:
        """
        Cached primer direction determination.
        
        Returns (direction, strand) tuple.
        """
        if primer_name.startswith("FW"):
            return ("forward", "+")
        elif primer_name.startswith("RW"):  
            return ("reverse", "-")
        else:
            raise ValueError(f"Invalid primer name format: {primer_name}")
    
    def _validate_numeric_batch(
        self, rows: List[Dict[str, str]], field_names: List[str]
    ) -> List[Dict[str, Union[int, float]]]:
        """
        Batch numeric validation for improved performance.
        
        Validates multiple numeric fields across multiple rows in one operation.
        """
        results = []
        
        for row_idx, row in enumerate(rows):
            row_result = {}
            
            for field_name in field_names:
                value = row.get(field_name, "")
                if not value:
                    continue
                
                try:
                    # Determine type and convert
                    if field_name in ['start', 'stop', 'pool', 'amplicon_length']:
                        row_result[field_name] = int(value)
                    else:
                        row_result[field_name] = float(value)
                        
                except ValueError:
                    logger.warning(f"Invalid {field_name} value '{value}' in row {row_idx + 2}")
                    row_result[field_name] = None
            
            results.append(row_result)
        
        return results
    
    def _create_primer_batch(
        self, primer_data_list: List[Dict[str, Any]]
    ) -> List[PrimerData]:
        """
        Batch primer creation for improved memory efficiency.
        """
        primers = []
        
        for data in primer_data_list:
            try:
                primer = PrimerData(
                    name=data['name'],
                    sequence=data['sequence'], 
                    start=data['start'],
                    stop=data['stop'],
                    strand=data['strand'],
                    direction=data['direction'],
                    pool=data['pool'],
                    amplicon_id=data['amplicon_id'],
                    reference_id=data['reference_id'],
                    gc_content=data.get('gc_content'),
                    tm=data.get('tm'),
                    score=data.get('score')
                )
                primers.append(primer)
            except Exception as e:
                logger.warning(f"Failed to create primer {data.get('name', 'unknown')}: {e}")
                continue
        
        return primers
    
    def _group_primers_by_amplicon(
        self, primers: List[PrimerData]
    ) -> Dict[str, AmpliconData]:
        """
        Efficiently group primers into amplicons.
        
        Uses dictionary-based grouping for O(n) performance.
        """
        amplicon_primers: Dict[str, List[PrimerData]] = {}
        amplicon_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Group primers and collect metadata
        for primer in primers:
            amp_id = primer.amplicon_id
            
            if amp_id not in amplicon_primers:
                amplicon_primers[amp_id] = []
                amplicon_metadata[amp_id] = {
                    'reference_id': primer.reference_id,
                    'min_start': primer.start,
                    'max_stop': primer.stop
                }
            
            amplicon_primers[amp_id].append(primer)
            
            # Update amplicon boundaries
            meta = amplicon_metadata[amp_id]
            meta['min_start'] = min(meta['min_start'], primer.start)
            meta['max_stop'] = max(meta['max_stop'], primer.stop)
        
        # Create AmpliconData objects
        amplicons = {}
        for amp_id, primers_list in amplicon_primers.items():
            meta = amplicon_metadata[amp_id]
            length = meta['max_stop'] - meta['min_start']
            
            amplicons[amp_id] = AmpliconData(
                amplicon_id=amp_id,
                primers=primers_list,
                length=length,
                reference_id=meta['reference_id']
            )
        
        return amplicons
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0
            else 0
        )
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'string_cache_size': len(self._string_cache),
            'validation_cache_size': len(self._validation_cache)
        }
    
    def clear_caches(self) -> None:
        """Clear all caches to free memory."""
        self._string_cache.clear()
        self._validation_cache.clear()
        self._sanitize_string_cached.cache_clear()
        self._get_primer_direction_cached.cache_clear()
        
        # Reset statistics
        self._cache_hits = 0
        self._cache_misses = 0