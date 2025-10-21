# Real Data Validation Framework

Comprehensive validation framework for PrePrimer real-world data testing.

## Overview

This framework provides automated validation of:
- Format conversions (all 5 output formats)
- Alignment tool integration (BLAST, Exonerate, merPCR)
- Data integrity and sequence validation
- Performance benchmarking
- Edge case handling

## Quick Start

### Run All Tests

```bash
# Run all real data tests (quick + standard)
python -m pytest tests/test_real_data_comprehensive.py -m real_data -v

# Run only quick tests (for CI)
python -m pytest tests/test_real_data_comprehensive.py -m quick -v

# Run only standard tests
python -m pytest tests/test_real_data_comprehensive.py -m standard -v

# Run stress tests (long-running)
python -m pytest tests/test_real_data_comprehensive.py -m stress -v
```

### Run Specific Test Categories

```bash
# Format conversion tests only
python -m pytest tests/test_real_data_comprehensive.py::TestFormatConversions -v

# Alignment tests only
python -m pytest tests/test_real_data_comprehensive.py::TestRealAlignments -v

# Edge case tests only
python -m pytest tests/test_real_data_comprehensive.py::TestEdgeCases -v

# Integration workflow tests
python -m pytest tests/test_real_data_comprehensive.py::TestIntegrationWorkflows -v
```

### Run Tests Requiring Specific Tools

```bash
# Only tests requiring BLAST
python -m pytest tests/test_real_data_comprehensive.py --requires_blast -v

# Only tests requiring Exonerate
python -m pytest tests/test_real_data_comprehensive.py --requires_exonerate -v

# Only tests requiring merPCR
python -m pytest tests/test_real_data_comprehensive.py --requires_merpcr -v
```

## Test Markers

Tests are organized with pytest markers for selective execution:

- **`@real_data`** - All real data validation tests
- **`@quick`** - Fast tests (<1s each, suitable for CI/CD)
- **`@standard`** - Standard validation tests (~3s total)
- **`@stress`** - Heavy/slow stress tests (>30s)
- **`@requires_blast`** - Requires BLAST installation
- **`@requires_exonerate`** - Requires Exonerate installation
- **`@requires_merpcr`** - Requires merPCR installation

### Examples

```bash
# Run quick tests only (CI pipeline)
pytest tests/test_real_data_comprehensive.py -m quick

# Run all tests except stress tests
pytest tests/test_real_data_comprehensive.py -m "real_data and not stress"

# Run standard tests that require BLAST
pytest tests/test_real_data_comprehensive.py -m "standard and requires_blast"
```

## Validation Framework

### Core Components

#### 1. `validator.py`

Provides validation functions for all output formats and data integrity checks.

**Key Classes:**
- `ValidationResult` - Dataclass for validation results (valid, errors, warnings, stats)
- `OutputValidator` - Static validation methods for files and sequences

**Format Validators:**
- `validate_artic_output(output_dir)` - Validates ARTIC BED structure
- `validate_varvamp_output(output_file)` - Validates VarVAMP 13-column TSV
- `validate_olivar_output(output_file)` - Validates Olivar CSV format
- `validate_fasta_output(output_file)` - Validates FASTA sequences
- `validate_sts_output(output_file)` - Validates STS 3-column format

**Comprehensive Validator:**
- `validate_conversion(input_format, output_format, input_file, output_path, amplicons)` - All-in-one validation

**Example Usage:**

```python
from tests.validation import validate_conversion, OutputValidator

# Validate a conversion
result = validate_conversion(
    input_format="varvamp",
    output_format="artic",
    input_file=Path("input.tsv"),
    output_path=Path("output/artic/"),
    amplicons=parsed_amplicons
)

if not result.valid:
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)

print("Statistics:", result.stats)
```

#### 2. `report_generator.py`

Generates validation reports in multiple formats.

**Key Class:**
- `ReportGenerator` - Static methods for report generation

**Report Types:**
- `generate_markdown_report(results, output_file, title)` - Markdown report with stats
- `generate_summary_json(results, output_file)` - JSON summary for automation
- `print_summary(results)` - Console output for quick feedback

**Example Usage:**

```python
from tests.validation.report_generator import ReportGenerator

# Generate markdown report
ReportGenerator.generate_markdown_report(
    results=validation_results,
    output_file=Path("validation_report.md"),
    title="PrePrimer Validation Report"
)

# Generate JSON summary
ReportGenerator.generate_summary_json(
    results=validation_results,
    output_file=Path("validation_summary.json")
)

# Print to console
ReportGenerator.print_summary(validation_results)
```

### Validation Result Structure

```python
@dataclass
class ValidationResult:
    valid: bool  # Overall pass/fail
    errors: List[str]  # Critical errors
    warnings: List[str]  # Non-critical warnings
    stats: Dict[str, any]  # Statistics and metadata

    def add_error(self, message: str)
    def add_warning(self, message: str)
    def add_stat(self, key: str, value: any)
```

**Example ValidationResult:**

```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Low primer count: 4"],
  "stats": {
    "total_amplicons": 2,
    "total_primers": 4,
    "avg_primers_per_amplicon": 2.0,
    "sequences_checked": 4,
    "file_size": 1234,
    "conversion": "varvamp → artic"
  }
}
```

## Test Data

### Available Datasets

Located in `tests/test_data/datasets/`:

#### 1. Small Dataset (`small/`)
- **Amplicons**: 5
- **Source**: SARS-CoV-2 subset
- **Files**:
  - `varvamp.tsv` - VarVAMP format
  - `artic.scheme.bed` - ARTIC format
  - `sts.tsv` - STS format (4-column, no header)
  - `reference.fasta` - Reference genome
- **Use Case**: Quick validation, CI/CD
- **Performance**: <0.5 seconds

#### 2. Medium Dataset (`medium/`)
- **Amplicons**: 80
- **Source**: African Swine Fever Virus (ASFV)
- **Files**:
  - `varvamp.tsv` - VarVAMP format
  - `reference.fasta` - Reference genome
- **Use Case**: Performance testing, scalability
- **Performance**: ~3 seconds

#### 3. Mitochondrial Dataset (`mitochondrial/`)
- **Amplicons**: 8
- **Source**: Human mtDNA (circular genome)
- **Files**:
  - `varvamp.tsv` - VarVAMP format
  - `reference.fasta` - Circular reference (16,569 bp)
- **Use Case**: Topology detection, circular coordinate handling
- **Performance**: <1 second
- **Special**: Tests cross-origin amplicons

### Dataset Usage in Tests

```python
from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "datasets"
SMALL_DATASET = TEST_DATA_DIR / "small"
MEDIUM_DATASET = TEST_DATA_DIR / "medium"
MITOCHONDRIAL_DATASET = TEST_DATA_DIR / "mitochondrial"

# Use in tests
input_file = SMALL_DATASET / "varvamp.tsv"
reference = SMALL_DATASET / "reference.fasta"
```

## Writing New Validation Tests

### Test Structure Template

```python
import pytest
from pathlib import Path
from tests.validation import validate_conversion, ValidationResult

# Mark as real data test
pytestmark = [pytest.mark.real_data]

# Optional: Add performance/tool requirements
quick = pytest.mark.quick
requires_blast = pytest.mark.skipif(
    not shutil.which("blastn"),
    reason="BLAST not installed"
)

class TestMyValidation:
    @quick
    def test_my_conversion(self, converter, output_dir, validation_results):
        """Test my specific conversion scenario."""
        # Setup
        input_file = Path("test_data/my_input.tsv")

        # Execute conversion
        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "my_test",
            input_format="varvamp",
            output_formats=["artic"],
            prefix="test"
        )

        # Validate results
        result = validate_conversion(
            input_format="varvamp",
            output_format="artic",
            input_file=input_file,
            output_path=output_files["artic"]
        )

        # Store for reporting
        validation_results["my_conversion_test"] = result

        # Assert
        assert result.valid, f"Validation failed: {result.errors}"
```

### Fixtures Available

All tests have access to these fixtures (defined in `test_real_data_comprehensive.py`):

- **`converter`** - PrimerConverter instance with default config
- **`output_dir`** - Temporary output directory (auto-cleaned)
- **`validation_results`** - Dictionary to collect all validation results
- **`tmp_path`** - Pytest temporary path fixture

### Adding Custom Validators

```python
# In tests/validation/validator.py

def validate_my_format(output_file: Path) -> ValidationResult:
    """Validate my custom format."""
    result = ValidationResult(valid=True)

    if not output_file.exists():
        result.add_error(f"Output file does not exist: {output_file}")
        return result

    with open(output_file) as f:
        lines = f.readlines()

    result.add_stat("line_count", len(lines))

    # Add your validation logic here
    if len(lines) < 2:
        result.add_error("File has insufficient lines")

    return result

# Export in __init__.py
__all__ = ["validate_my_format", ...]
```

## Performance Targets

Tests include performance assertions based on dataset size:

| Dataset | Amplicons | Conversion Target | Alignment Target | Total Target |
|---------|-----------|-------------------|------------------|--------------|
| Small   | 5         | <1s               | <10s             | <15s         |
| Medium  | 80        | <5s               | <30s             | <45s         |
| Large   | 500+      | <30s              | <120s            | <180s        |

**Example Performance Assertion:**

```python
import time

start_time = time.time()
output_files = converter.convert(...)
conversion_time = time.time() - start_time

# Assert meets performance target
assert conversion_time < 5.0, f"Conversion too slow: {conversion_time}s"

# Add to statistics
result.add_stat("conversion_time_seconds", conversion_time)
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Real Data Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Install BLAST
        run: |
          sudo apt-get update
          sudo apt-get install -y ncbi-blast+

      - name: Run quick validation tests
        run: |
          pytest tests/test_real_data_comprehensive.py -m quick -v

      - name: Run standard validation tests
        run: |
          pytest tests/test_real_data_comprehensive.py -m standard -v
```

## Troubleshooting

### Common Issues

#### 1. Tests Skip Due to Missing Tools

**Problem**: Tests marked with `@requires_blast` are skipped

**Solution**: Install required tools:

```bash
# macOS
brew install blast exonerate
pip install merpcr

# Ubuntu
sudo apt-get install ncbi-blast+ exonerate
pip install merpcr
```

#### 2. Validation Fails Due to Format Changes

**Problem**: Validation error after modifying writer

**Solution**: Update validator to match new format:

```python
# In tests/validation/validator.py
def validate_artic_output(output_dir: Path) -> ValidationResult:
    # Update validation logic to match new format
    pass
```

#### 3. Performance Tests Fail

**Problem**: Conversion too slow on CI

**Solution**:
- Check if running on slower CI hardware
- Increase timeout if appropriate
- Profile to find bottlenecks

```python
import cProfile
profiler = cProfile.Profile()
profiler.enable()
converter.convert(...)
profiler.disable()
profiler.print_stats(sort='cumulative')
```

## Best Practices

### 1. Test Organization

- Group related tests in classes
- Use descriptive test names
- Add docstrings explaining what's tested
- Use markers for categorization

### 2. Validation Strategy

- Always validate file existence first
- Check format structure before content
- Use warnings for non-critical issues
- Collect comprehensive statistics

### 3. Error Handling

- Provide clear error messages
- Include suggestions when possible
- Add context (file paths, line numbers)
- Don't fail fast - collect all errors

### 4. Performance

- Time critical operations
- Add performance assertions
- Compare against baselines
- Profile slow tests

### 5. Reporting

- Store all validation results
- Generate reports after test run
- Include both passes and failures
- Provide actionable recommendations

## Future Enhancements

### Planned Features

1. **HTML Reports** - Rich interactive reports with charts
2. **Baseline Comparison** - Compare results against previous runs
3. **Performance Regression Detection** - Alert on slowdowns
4. **External Dataset Integration** - Auto-download from PrimerSchemes
5. **Parallel Test Execution** - Speed up test suite
6. **Coverage Metrics** - Track format/feature coverage

### Contributing

To add new validation tests:

1. Create test in `test_real_data_comprehensive.py`
2. Add required validator in `validator.py`
3. Update this README with examples
4. Add test data if needed
5. Document any new markers or fixtures

---

**Questions?** See main project documentation or open an issue.
