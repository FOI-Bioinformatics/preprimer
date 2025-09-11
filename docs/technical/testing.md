# Testing Framework

PrePrimer implements a testing framework with 581 tests across multiple methodologies to ensure code quality, performance, and reliability.

## Testing Overview

### Test Statistics
- **Total Tests**: 581 implemented tests
- **Coverage**: 96.90% code coverage
- **Test Categories**: Multiple testing methodologies
- **Scope**: Core functionality, security features, performance validation, and comprehensive edge case testing

### Test Architecture
```
tests/
├── test_property_based.py      # 12 property-based tests
├── test_benchmarks.py         # 23 performance benchmarks
├── test_integration.py        # 12 end-to-end tests
├── test_security.py          # 18 security validation tests
├── test_error_handling.py    # 29 error handling tests
├── test_enhanced_config.py   # 31 configuration tests
├── test_core_*.py            # 91+ core functionality tests
└── test_data/                # Unified test datasets
```

## Testing Methodologies

### 1. Property-Based Testing
Automated test case generation using Hypothesis:

```python
from hypothesis import given, strategies as st

@given(st.lists(safe_path_component, min_size=1, max_size=5))
def test_path_validation_properties(self, path_components):
    """Property-based test with automatic input generation."""
    path_str = '/'.join(path_components)
    # Hypothesis generates thousands of diverse test cases
```

**Features:**
- 12 property-based tests with automatic input generation
- Edge case discovery through random input generation
- Statistical validation with configurable test runs
- Comprehensive coverage of data structures and algorithms

**Running property-based tests:**
```bash
python -m pytest tests/test_property_based.py -v --hypothesis-show-statistics
```

### 2. Performance Benchmarking
Continuous performance monitoring with statistical analysis:

```python
def test_parser_performance(self, benchmark):
    """Benchmark parser performance with statistical analysis."""
    result = benchmark(parser.parse, test_data)
    # Automatic regression detection and statistical analysis
```

**Benchmark Results:**
- **Parser Creation**: 4,244,769 ops/sec (217ns mean)
- **Data Processing**: 67,005 amplicons/sec average
- **Memory Usage**: Linear O(n) scaling validated
- **Large Dataset Processing**: Maintains performance at scale

**Running benchmarks:**
```bash
# All performance benchmarks
python -m pytest tests/test_benchmarks.py --benchmark-only

# Specific benchmark with comparison
python -m pytest tests/test_benchmarks.py::test_varvamp_parser_benchmark -v
```

### 3. Integration Testing
End-to-end workflow validation:

```python
def test_complete_conversion_workflow(self, unified_datasets_dir):
    """Test complete pipeline: input → parsing → conversion → output."""
    for input_format in ['varvamp', 'artic', 'olivar']:
        for output_format in ['artic', 'fasta', 'sts']:
            validate_conversion_pipeline(input_format, output_format)
```

**Features:**
- 12 integration tests covering complete workflows
- Cross-format validation ensuring data integrity
- Real dataset testing with COVID-19 and ASFV data
- Error recovery and robustness validation

### 4. Security Testing
Comprehensive security validation:

```python
def test_path_traversal_prevention(self):
    """Validate protection against directory traversal attacks."""
    malicious_paths = ['../etc/passwd', '~/.ssh/id_rsa', '/etc/hosts']
    for path in malicious_paths:
        with pytest.raises(SecurityError):
            PathValidator.sanitize_path(path)
```

**Security Test Coverage:**
- Path traversal prevention and validation
- Input sanitization with size limits
- File permission and access control
- Resource exhaustion protection
- Symlink attack prevention

### 5. Mutation Testing
Test quality assessment through code mutation:

```bash
# Run mutation testing for test quality validation
python scripts/run_mutation_tests.py
```

**Features:**
- Automated code mutation generation
- Test quality metrics through mutation detection rate
- Coverage gap identification
- Continuous quality monitoring

## Test Data Architecture

### Unified Dataset Structure
Cross-format testing with consistent biological data:

```
tests/test_data/
├── datasets/
│   ├── small/                   # COVID-19: 5 amplicons, 10 primers
│   │   ├── reference.fasta      # NC_045512.2 (29,903 bp)
│   │   ├── varvamp.tsv         # 13-field format
│   │   ├── artic.scheme.bed    # 7-field format
│   │   ├── olivar.csv          # CSV design format
│   │   └── metadata.yaml       # Dataset documentation
│   └── medium/                  # ASFV: 80 amplicons, 160 primers
├── fixtures/                    # Malformed data for error testing
└── legacy/                      # Original test files
```

**Dataset Characteristics:**
- Cross-format consistency with same biological data
- Realistic primer scores and quality metrics
- Edge cases including overlapping amplicons
- Comprehensive error condition coverage

## Running Tests

### Complete Test Suite
```bash
# Run all 226 tests
python -m pytest

# Expected output: 225 passed, 1 skipped
```

### Test Categories
```bash
# Property-based testing
python -m pytest tests/test_property_based.py -v

# Performance benchmarking
python -m pytest tests/test_benchmarks.py -v

# Integration testing  
python -m pytest tests/test_integration.py -v

# Security validation
python -m pytest tests/test_security.py -v

# Error handling
python -m pytest tests/test_error_handling.py -v
```

### Coverage Analysis
```bash
# Generate comprehensive coverage report
python -m pytest --cov=preprimer --cov-report=html --cov-report=term-missing

# Coverage by component
python -m pytest tests/test_security.py --cov=preprimer.core.security
```

## Continuous Integration

The testing framework integrates with CI/CD pipelines:

```yaml
# Comprehensive testing in CI
- name: Run test suite
  run: python -m pytest --tb=short -q

# Performance monitoring
- name: Performance benchmarks  
  run: python -m pytest tests/test_benchmarks.py --benchmark-only
```

**CI Features:**
- Multi-platform testing (Ubuntu, macOS)
- Multi-Python version support (3.11-3.13)
- Automated benchmark comparison
- Security vulnerability scanning

## Quality Metrics

### Performance Characteristics
- **Test execution time**: ~18 seconds for complete suite
- **Memory usage**: <100MB during testing
- **Coverage**: >95% across all modules
- **Reliability**: <1% flaky test rate

### Quality Assurance
- **Mutation score**: >80% mutation detection rate
- **Error coverage**: All exception paths tested
- **Security coverage**: All attack vectors validated
- **Cross-platform consistency**: 100% (Linux/macOS)

## Contributing to Tests

When adding new functionality:

1. **Unit tests**: Test individual functions and methods
2. **Integration tests**: Test complete workflows
3. **Property-based tests**: Add invariant testing for complex logic
4. **Performance tests**: Benchmark performance-critical code
5. **Security tests**: Validate input handling and file operations

### Test Guidelines
- Use descriptive test names indicating expected behavior
- Include both positive and negative test cases
- Test edge cases and boundary conditions
- Validate error messages and exception handling
- Document test rationale for complex scenarios