# Enhanced Testing Framework Documentation

PrePrimer includes a comprehensive testing framework with advanced features for ensuring code quality, performance, and reliability. This framework incorporates property-based testing, performance benchmarks, integration testing, and mutation testing.

## Table of Contents

1. [Overview](#overview)
2. [Property-Based Testing](#property-based-testing)
3. [Performance Benchmarking](#performance-benchmarking)
4. [Integration Testing](#integration-testing)
5. [Mutation Testing](#mutation-testing)
6. [Running Tests](#running-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Best Practices](#best-practices)

## Overview

The enhanced testing framework provides multiple layers of testing to ensure comprehensive coverage:

- **Unit Tests**: Traditional unit tests for individual components
- **Property-Based Tests**: Hypothesis-driven tests that explore edge cases automatically
- **Benchmark Tests**: Performance regression testing
- **Integration Tests**: End-to-end workflow testing
- **Mutation Tests**: Test quality assessment through code mutation

## Property-Based Testing

Property-based testing uses the Hypothesis library to automatically generate test inputs and discover edge cases that traditional unit tests might miss.

### Key Features

- **Automatic Test Case Generation**: Hypothesis generates diverse test inputs
- **Edge Case Discovery**: Automatically finds corner cases and boundary conditions
- **Shrinking**: When a test fails, Hypothesis minimizes the failing input
- **Stateful Testing**: Test complex state machines and workflows

### Example Usage

```python
from hypothesis import given, strategies as st

@given(
    sequence=st.text(alphabet='ATCG', min_size=10, max_size=100),
    start=st.integers(min_value=1, max_value=1000)
)
def test_primer_properties(sequence, start):
    """Test that primer creation maintains invariants."""
    stop = start + len(sequence)
    
    primer = PrimerData(
        name="test_primer",
        sequence=sequence,
        start=start,
        stop=stop,
        strand='+',
        direction='forward',
        pool=1,
        amplicon_id='test_amplicon',
        reference_id='test_ref'
    )
    
    # Properties that should always hold
    assert primer.stop > primer.start
    assert len(primer.sequence) == (primer.stop - primer.start)
    assert set(primer.sequence).issubset(set('ATCG'))
```

### Configuration

Property-based test behavior is configured in `pyproject.toml`:

```toml
[tool.hypothesis]
max_examples = 100
deadline = 1000

[tool.hypothesis.profiles.ci]
max_examples = 200
deadline = 2000
```

### Running Property-Based Tests

```bash
# Run all property-based tests
pytest tests/test_property_based.py -v

# Run with specific Hypothesis profile
HYPOTHESIS_PROFILE=ci pytest tests/test_property_based.py

# Enable Hypothesis verbosity for debugging
pytest tests/test_property_based.py --hypothesis-verbosity=verbose
```

## Performance Benchmarking

Performance benchmarks ensure that code changes don't introduce performance regressions and help identify optimization opportunities.

### Key Features

- **Regression Detection**: Compare performance across code changes
- **Statistical Analysis**: Multiple runs with statistical significance testing
- **Memory Usage Tracking**: Monitor memory consumption patterns
- **Scalability Testing**: Test performance with various dataset sizes

### Example Usage

```python
import pytest

def test_parser_performance_benchmark(benchmark):
    """Benchmark parser performance with medium dataset."""
    parser = VarVAMPParser()
    
    # The benchmark function will run this multiple times
    result = benchmark(parser.parse, test_file_path, "test_prefix")
    
    assert len(result) > 0  # Verify functionality
```

### Benchmark Configuration

Configure benchmarks in `pyproject.toml`:

```toml
[tool.pytest_benchmark]
only_show_min = true
sort = "mean"
disable_gc = true
min_rounds = 5
max_time = 1.0
```

### Running Benchmarks

```bash
# Run only benchmark tests
pytest tests/test_benchmarks.py --benchmark-only

# Compare with previous results
pytest tests/test_benchmarks.py --benchmark-compare=0001

# Save benchmark results
pytest tests/test_benchmarks.py --benchmark-save=baseline

# Generate HTML report
pytest tests/test_benchmarks.py --benchmark-histogram=histogram.html
```

## Integration Testing

Integration tests verify that all components work together correctly in realistic scenarios.

### Key Features

- **End-to-End Workflows**: Complete conversion workflows
- **Configuration Integration**: Test with various configuration scenarios
- **Error Handling**: Verify error handling across component boundaries
- **Concurrent Operations**: Test thread safety and concurrent access

### Example Usage

```python
def test_varvamp_to_artic_conversion(self, temp_workspace, varvamp_test_file):
    """Test complete VarVAMP to ARTIC conversion workflow."""
    output_dir = temp_workspace / "output"
    
    converter = PrimerConverter()
    
    # Convert VarVAMP to ARTIC format
    result = converter.convert(
        input_file=varvamp_test_file,
        output_dir=output_dir,
        input_format="varvamp",
        output_formats=["artic"],
        prefix="SARS-CoV-2"
    )
    
    # Verify conversion results
    assert "artic" in result
    assert result["artic"].exists()
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific integration test categories
pytest tests/test_integration.py -k "workflow" -v

# Run with parallel execution
pytest tests/test_integration.py -n auto
```

## Mutation Testing

Mutation testing assesses test quality by introducing small code changes (mutations) and verifying that tests catch them.

### Key Features

- **Test Quality Assessment**: Measure how well tests detect code changes
- **Surviving Mutant Analysis**: Identify gaps in test coverage
- **Configurable Targeting**: Focus on specific modules or files
- **Comprehensive Reporting**: Detailed analysis of test effectiveness

### Mutation Testing Process

1. **Baseline Tests**: Ensure all tests pass before mutation
2. **Mutation Generation**: Create variants of source code
3. **Test Execution**: Run tests against each mutant
4. **Results Analysis**: Calculate mutation score and identify survivors

### Running Mutation Tests

```bash
# Run complete mutation testing
python scripts/run_mutation_tests.py

# Test specific modules
python scripts/run_mutation_tests.py --target-modules preprimer/core/

# Test specific files
python scripts/run_mutation_tests.py --target-files preprimer/core/converter.py

# Run baseline tests only
python scripts/run_mutation_tests.py --baseline

# Analyze previous results
python scripts/run_mutation_tests.py --analyze
```

### Mutation Score Interpretation

- **90-100%**: Excellent test coverage
- **80-89%**: Good test coverage
- **70-79%**: Fair test coverage, room for improvement
- **60-69%**: Poor test coverage, needs attention
- **<60%**: Very poor test coverage, critical improvements needed

### Configuration

Mutation testing is configured in `.mutmut_config`:

```ini
[mutmut]
runner = python -m pytest tests/ -x --tb=no --disable-warnings
paths_to_mutate = preprimer/
timeout = 300
use_cache = true
show_mutants = true
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=preprimer --cov-report=html

# Run specific test types
pytest tests/test_property_based.py  # Property-based tests
pytest tests/test_benchmarks.py      # Benchmark tests
pytest tests/test_integration.py     # Integration tests

# Run with markers
pytest -m "not slow"                 # Skip slow tests
pytest -m "property"                 # Only property-based tests
pytest -m "benchmark"                # Only benchmark tests
```

### Advanced Test Execution

```bash
# Parallel execution
pytest -n auto

# Verbose output with timing
pytest -v --tb=short --durations=10

# Run until first failure
pytest -x

# Run failed tests from last run
pytest --lf

# Generate multiple report formats
pytest --cov=preprimer \
       --cov-report=html \
       --cov-report=xml \
       --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Enhanced Testing

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run unit tests
      run: |
        pytest tests/ --cov=preprimer --cov-report=xml
    
    - name: Run property-based tests
      env:
        HYPOTHESIS_PROFILE: ci
      run: |
        pytest tests/test_property_based.py -v
    
    - name: Run integration tests
      run: |
        pytest tests/test_integration.py -v
    
    - name: Run benchmarks
      run: |
        pytest tests/test_benchmarks.py --benchmark-only --benchmark-json=benchmark.json
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  mutation-testing:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'pull_request'

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    
    - name: Run mutation testing
      run: |
        python scripts/run_mutation_tests.py --max-mutations 100
    
    - name: Comment mutation results
      uses: actions/github-script@v6
      if: always()
      with:
        script: |
          const fs = require('fs');
          try {
            const results = JSON.parse(fs.readFileSync('mutation_results/latest_results.json', 'utf8'));
            const report = fs.readFileSync('mutation_results/latest_report.txt', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Mutation Testing Results\n\n**Mutation Score: ${results.mutation_score.toFixed(1)}%**\n\n\`\`\`\n${report}\n\`\`\``
            });
          } catch (error) {
            console.log('Could not read mutation testing results');
          }
```

### Pre-commit Hooks

Configure pre-commit hooks in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        args: [tests/, --tb=short, -q]
      
      - id: property-tests
        name: property-based tests
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        args: [tests/test_property_based.py, -v]
```

## Best Practices

### 1. Test Organization

```
tests/
├── unit/                    # Traditional unit tests
├── integration/             # Integration tests
├── property/                # Property-based tests
├── benchmarks/              # Performance benchmarks
├── fixtures/                # Test fixtures and data
├── conftest.py             # Pytest configuration
└── test_*.py               # Test modules
```

### 2. Property-Based Testing Guidelines

- **Start Simple**: Begin with basic properties, add complexity gradually
- **Focus on Invariants**: Test properties that should always hold
- **Use Custom Strategies**: Create domain-specific data generators
- **Example-Based Fallbacks**: Include `@example` decorators for important cases

### 3. Benchmark Testing Guidelines

- **Stable Environment**: Run benchmarks in consistent environments
- **Multiple Measurements**: Use statistical significance for reliability
- **Realistic Data**: Use representative datasets for meaningful results
- **Baseline Comparisons**: Always compare against established baselines

### 4. Integration Testing Guidelines

- **Realistic Scenarios**: Test actual user workflows
- **Environment Isolation**: Use temporary directories and mock external services
- **Error Conditions**: Test failure scenarios as thoroughly as success cases
- **Configuration Variants**: Test with different configuration combinations

### 5. Mutation Testing Guidelines

- **Regular Execution**: Run mutation tests regularly, not just before releases
- **Incremental Approach**: Start with core modules, expand coverage gradually
- **Survivor Investigation**: Always investigate surviving mutants
- **Quality Threshold**: Maintain mutation scores above 80% for critical code

### 6. Test Data Management

```python
# Good: Use property-based testing for data generation
@given(st.text(alphabet='ATCG', min_size=10, max_size=50))
def test_sequence_processing(sequence):
    result = process_sequence(sequence)
    assert len(result) > 0

# Good: Use fixtures for complex setup
@pytest.fixture
def sample_amplicon_data():
    return AmpliconData(
        amplicon_id="test_amp",
        primers=[...],
        length=300,
        reference_id="test_ref"
    )
```

### 7. Performance Considerations

- **Selective Benchmarking**: Don't benchmark every function
- **Statistical Validity**: Run enough iterations for statistical significance
- **Resource Monitoring**: Track memory usage alongside execution time
- **Threshold Alerts**: Set up alerts for performance regressions

### 8. Continuous Improvement

- **Regular Review**: Review test results and coverage reports regularly
- **Survivor Analysis**: Investigate mutation testing survivors
- **Performance Trends**: Monitor benchmark trends over time
- **Test Refactoring**: Keep tests maintainable and readable

## Troubleshooting

### Common Issues

1. **Slow Property-Based Tests**
   - Reduce `max_examples` in development profile
   - Use more specific strategies to reduce search space
   - Add `assume()` statements to filter invalid inputs

2. **Flaky Benchmarks**
   - Increase number of rounds (`min_rounds`)
   - Disable garbage collection during benchmarks
   - Run on dedicated hardware when possible

3. **Low Mutation Scores**
   - Review surviving mutants for test gaps
   - Add edge case tests
   - Test error conditions more thoroughly

4. **Integration Test Failures**
   - Check for proper cleanup between tests
   - Verify temporary directory isolation
   - Mock external dependencies consistently

### Performance Tips

- Use `pytest-xdist` for parallel test execution
- Configure appropriate timeouts for different test types
- Use test markers to selectively run test suites
- Cache expensive setup operations when possible

### Debugging

```bash
# Debug property-based test failures
pytest tests/test_property_based.py --hypothesis-verbosity=verbose

# Debug benchmark variations
pytest tests/test_benchmarks.py --benchmark-histogram=debug.html

# Debug integration test setup
pytest tests/test_integration.py -v -s

# Debug mutation testing
python scripts/run_mutation_tests.py --target-files specific_file.py
```

This enhanced testing framework provides comprehensive quality assurance for the preprimer project, ensuring reliability, performance, and maintainability across all development phases.