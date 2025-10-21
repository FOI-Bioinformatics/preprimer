# Performance Guide

Performance characteristics, optimization strategies, and benchmarking for PrePrimer.

## Performance Characteristics

### Processing Capabilities
PrePrimer demonstrates efficient processing across various dataset sizes:

- **Small datasets** (<50 amplicons): ~300μs processing time
- **Medium datasets** (50-500 amplicons): ~2.5ms processing time  
- **Large datasets** (500+ amplicons): ~26ms processing time
- **Average throughput**: 67,005 amplicons/second
- **Memory scaling**: Linear O(n) with amplicon count

### Benchmark Results

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Parser Creation | 4,244,769 ops/sec | Lightweight instantiation |
| Data Structure Creation | 3,211,140 ops/sec | Efficient object construction |
| Format Detection | 44,564 ops/sec | Content analysis |
| VarVAMP Parsing | 2,896 ops/sec | Small datasets |
| ARTIC Parsing | 3,021 ops/sec | Standard datasets |
| Large Dataset Processing | 37 ops/sec | 2000+ amplicons |

### Memory Usage
- **Baseline**: ~50MB for basic operations
- **Medium datasets**: ~100MB for 500 amplicons
- **Large datasets**: ~200MB for 2000+ amplicons
- **Scaling**: Linear relationship with dataset size

## Performance Testing

### Benchmark Suite
Run performance benchmarks:

```bash
# All performance benchmarks
python -m pytest tests/test_benchmarks.py --benchmark-only

# Specific parser benchmarks
python -m pytest tests/test_benchmarks.py::test_varvamp_parser_benchmark -v

# Compare with baseline
python -m pytest tests/test_benchmarks.py --benchmark-compare=baseline
```

### Custom Performance Testing
```python
import time
from preprimer.parsers.varvamp_parser import VarVAMPParser

# Time parser operations
parser = VarVAMPParser()
start_time = time.time()
amplicons = parser.parse(file_path, prefix="test")
processing_time = time.time() - start_time

print(f"Processed {len(amplicons)} amplicons in {processing_time:.3f} seconds")
print(f"Throughput: {len(amplicons)/processing_time:.0f} amplicons/second")
```

## Optimization Strategies

### Parser Optimization
1. **String Caching**: Cache repeated string sanitization operations
2. **Batch Validation**: Validate multiple fields simultaneously
3. **Pre-compiled Patterns**: Use compiled regex patterns for better performance
4. **Memory Pooling**: Reuse data structures where possible

### Implementation Example
```python
from functools import lru_cache

class OptimizedParser(StandardizedParser):
    @lru_cache(maxsize=10000)
    def _sanitize_string_cached(self, text: str, max_length: int) -> str:
        """Cache-optimized string sanitization."""
        return self._sanitize_string(text, max_length)
    
    def get_performance_stats(self) -> dict:
        """Monitor cache performance."""
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses)
        }
```

### Configuration Optimization
```python
# Optimize for performance vs. validation trade-offs
config = {
    "parsing": {
        "strict_validation": False,    # Faster parsing
        "cache_enabled": True,         # Enable caching
        "batch_size": 1000            # Batch processing
    }
}
```

## Profiling and Analysis

### Performance Profiling
```python
import cProfile
import pstats

def profile_parsing():
    """Profile parsing operations."""
    pr = cProfile.Profile()
    pr.enable()
    
    # Parsing operations
    parser.parse(large_dataset_file)
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative').print_stats(10)
```

### Memory Profiling
```python
import tracemalloc

def profile_memory():
    """Profile memory usage."""
    tracemalloc.start()
    
    # Operations to profile
    amplicons = parser.parse(dataset_file)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    tracemalloc.stop()
```

## Performance Best Practices

### For Users
1. **Virtual Environments**: Use isolated environments for consistent performance
2. **Dataset Size**: Consider dataset size when setting memory limits
3. **File Format**: VarVAMP format typically processes fastest
4. **Storage**: Use SSD storage for large dataset processing

### For Developers
1. **Benchmark Changes**: Always benchmark performance-critical modifications
2. **Cache Appropriately**: Use caching for repeated operations
3. **Batch Operations**: Process data in batches when possible
4. **Profile Regularly**: Use profiling tools to identify bottlenecks
5. **Memory Management**: Explicitly clean up large data structures

### Code Optimization Guidelines
```python
# Good: Efficient data processing
def process_primers_batch(primers: List[PrimerData]) -> List[AmpliconData]:
    """Process primers in batches for better performance."""
    amplicons = {}
    for primer in primers:
        amp_id = primer.amplicon_id
        if amp_id not in amplicons:
            amplicons[amp_id] = AmpliconData(amplicon_id=amp_id, primers=[])
        amplicons[amp_id].primers.append(primer)
    return list(amplicons.values())

# Avoid: Inefficient nested operations
def process_primers_slow(primers: List[PrimerData]) -> List[AmpliconData]:
    """Inefficient processing with repeated operations."""
    amplicons = []
    for primer in primers:
        # This creates O(n²) complexity
        existing_amp = None
        for amp in amplicons:
            if amp.amplicon_id == primer.amplicon_id:
                existing_amp = amp
                break
        # ... rest of inefficient logic
```

## Scalability Considerations

### Dataset Size Limits
- **Recommended maximum**: 5,000 amplicons per file
- **Memory considerations**: Monitor memory usage for datasets >1,000 amplicons
- **Processing time**: Linear scaling generally maintained up to 10,000 amplicons

### Parallel Processing
For very large datasets, consider parallel processing:

```python
from multiprocessing import Pool
from pathlib import Path

def process_large_dataset(input_files: List[Path]) -> dict:
    """Process multiple files in parallel."""
    with Pool() as pool:
        results = pool.map(process_single_file, input_files)
    return combine_results(results)
```

### Resource Management
```python
# Efficient resource usage
def process_with_cleanup(file_path: Path) -> List[AmpliconData]:
    """Process file with explicit cleanup."""
    try:
        parser = VarVAMPParser()
        amplicons = parser.parse(file_path)
        return amplicons
    finally:
        # Explicit cleanup if needed
        if hasattr(parser, 'clear_caches'):
            parser.clear_caches()
```

## Continuous Performance Monitoring

### CI/CD Integration
Performance benchmarks run automatically in CI/CD:

```yaml
# Performance monitoring in CI
- name: Run performance benchmarks
  run: |
    python -m pytest tests/test_benchmarks.py --benchmark-only \
      --benchmark-json=benchmark-results.json
```

### Performance Regression Detection
- **Baseline comparison**: Compare against previous performance baselines
- **Threshold alerts**: Alert on performance regressions >10%
- **Historical tracking**: Monitor performance trends over time

### Monitoring Metrics
- **Throughput**: Amplicons processed per second
- **Latency**: Processing time for standard datasets  
- **Memory efficiency**: Peak memory usage per amplicon
- **Cache efficiency**: Hit rates for optimization caches

## Performance Troubleshooting

### Common Performance Issues

#### Slow Parsing
```python
# Diagnostic: Check file characteristics
def diagnose_slow_parsing(file_path: Path):
    """Diagnose parsing performance issues."""
    file_size = file_path.stat().st_size
    print(f"File size: {file_size / 1024 / 1024:.1f} MB")
    
    with open(file_path) as f:
        line_count = sum(1 for _ in f)
    print(f"Line count: {line_count}")
    
    # Check for problematic content
    with open(file_path) as f:
        sample_lines = [f.readline() for _ in range(5)]
    print(f"Sample lines: {sample_lines}")
```

#### Memory Issues
```python
# Monitor memory usage during processing
import psutil
import os

def monitor_memory_usage():
    """Monitor memory usage during processing."""
    process = psutil.Process(os.getpid())
    
    def log_memory():
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Memory usage: {memory_mb:.1f} MB")
    
    return log_memory
```

#### Performance Regression
1. **Compare benchmarks**: Use benchmark comparison tools
2. **Profile differences**: Identify changed code paths
3. **Validate optimizations**: Ensure optimizations are active
4. **Check configuration**: Verify performance-related settings

This guide provides the foundation for understanding and optimizing PrePrimer performance while maintaining code quality and reliability.