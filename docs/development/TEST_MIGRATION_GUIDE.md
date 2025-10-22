# Test Migration Guide

## Overview

This guide provides step-by-step instructions for migrating tests to the new organized structure. The infrastructure is now complete:

✅ **Completed Setup**:
- New directory structure (`unit/`, `integration/`, `e2e/`, `performance/`, `property/`, `fixtures/`, `utils/`)
- Test utilities (`assertions.py`, `builders.py`, `factories.py`)
- Updated `pyproject.toml` with comprehensive markers and timeout configuration
- New dependencies: `pytest-timeout`, `pytest-rerunfailures`

## Quick Start

### 1. Install New Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest-timeout>=2.1` - Test timeout detection
- `pytest-rerunfailures>=12.0` - Automatic flaky test retries

### 2. Verify Infrastructure

```bash
# Run tests to verify nothing broke
python -m pytest tests/test_core_interfaces.py -v

# List all available markers
python -m pytest --markers
```

---

## Migration Workflow

For each test file, follow this process:

### Step 1: Determine Test Layer

**Ask**: What does this test file test?

| Layer | Criteria | Examples |
|-------|----------|----------|
| **unit** | - No file I/O<br>- No external dependencies<br>- Tests single function/class<br>- <50ms per test | - `test_interfaces.py`<br>- `test_exceptions.py`<br>- `test_topology.py` (logic only) |
| **integration** | - File I/O allowed<br>- Tests component interaction<br>- <500ms per test | - `test_converter.py`<br>- `test_parser_writer_integration.py`<br>- `test_config_integration.py` |
| **e2e** | - Full system tests<br>- Complete workflows<br>- >500ms allowed | - `test_cli.py`<br>- `test_real_data.py`<br>- `test_cross_format.py` |
| **performance** | - Benchmarks<br>- Performance testing<br>- Time measurements | - `test_benchmarks.py`<br>- `test_parser_performance.py` |
| **property** | - Hypothesis tests<br>- Property-based testing | - `test_parsers_property.py` |

### Step 2: Move and Refactor

**For Unit Tests**: `tests/unit/{domain}/test_{module}.py`

Example: `test_security.py` → `tests/unit/core/test_security.py`

```bash
# Create if needed
mkdir -p tests/unit/core

# Move and add markers
# (See detailed example below)
```

**For Integration Tests**: `tests/integration/test_{component}.py`

**For E2E Tests**: `tests/e2e/test_{workflow}.py`

### Step 3: Add Test Markers

Add appropriate markers to ALL tests:

```python
import pytest

@pytest.mark.unit  # Test layer (required)
@pytest.mark.security  # Domain marker (recommended)
class TestPathValidator:
    """Unit tests for PathValidator."""

    def test_valid_path(self):
        """Test with valid path."""
        # Test implementation
```

**Marker Combinations**:
```python
# Unit test for parser
@pytest.mark.unit
@pytest.mark.parser

# Integration test for converter
@pytest.mark.integration
@pytest.mark.quick  # If fast enough

# E2E test for CLI
@pytest.mark.e2e
@pytest.mark.slow  # If >5 seconds

# Flaky test
@pytest.mark.flaky(reruns=2)
@pytest.mark.integration
```

### Step 4: Use Test Utilities

Replace custom test code with utilities:

**Before**:
```python
# Old assertion pattern
assert amplicon.amplicon_id == "test_1"
assert len(amplicon.primers) == 2
assert amplicon.primers[0].direction == "forward"
assert amplicon.primers[1].direction == "reverse"
```

**After**:
```python
from tests.utils.assertions import assert_amplicon_structure_valid

# Clean, reusable assertion
assert_amplicon_structure_valid(amplicon)
```

**Before**:
```python
# Old test data creation
primer = PrimerData(
    name="test_F",
    sequence="ATCGATCGATCGATCGATCG",
    start=100,
    stop=120,
    strand="+",
    direction="forward",
    pool=1,
    amplicon_id="amp1",
    reference_id="ref1",
    gc_content=0.5,
    tm=60.0,
    score=1.0
)
```

**After**:
```python
from tests.utils.builders import PrimerDataBuilder

# Fluent, readable builder
primer = (
    PrimerDataBuilder()
    .with_name("test_F")
    .with_sequence("ATCGATCGATCGATCGATCG")
    .forward()
    .in_pool(1)
    .for_amplicon("amp1")
    .build()
)
```

**Before**:
```python
# Manual dataset creation
amplicons = {}
for i in range(5):
    # Create primers...
    amplicon = AmpliconData(...)
    amplicons[f"amp_{i}"] = amplicon
```

**After**:
```python
from tests.utils.factories import create_small_dataset

# One-liner for common scenarios
amplicons = create_small_dataset(amplicons=5, pools=2)
```

### Step 5: Update Imports

```python
# Common imports for tests
import pytest
from pathlib import Path

# Test utilities
from tests.utils.assertions import (
    assert_amplicons_equal,
    assert_primer_valid,
    assert_file_format_valid,
    assert_conversion_successful,
)
from tests.utils.builders import (
    PrimerDataBuilder,
    AmpliconDataBuilder,
    ConfigBuilder,
)
from tests.utils.factories import (
    create_small_dataset,
    create_temp_fasta_file,
    SCENARIO_MINIMAL,
)

# PrePrimer imports
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.exceptions import ParserError, ValidationError
```

### Step 6: Run Tests

```bash
# Run just your migrated tests
python -m pytest tests/unit/core/test_security.py -v

# Run all unit tests
python -m pytest -m unit -v

# Run fast tests only
python -m pytest -m "unit or (integration and quick)" -v
```

---

## Complete Migration Example

### Example: Migrating Security Tests

**Goal**: Merge `test_security.py` (404 lines) + `test_security_comprehensive.py` (584 lines) → organized `unit/core/test_security.py`

#### Step 1: Analyze Current Tests

```bash
# See what's in the files
grep -n "^class Test" tests/test_security.py
grep -n "^class Test" tests/test_security_comprehensive.py
```

Output shows 12 test classes total across both files.

#### Step 2: Create New File Structure

Create `tests/unit/core/test_security.py`:

```python
"""
Unit tests for security validation components.

Tests PathValidator, InputValidator, and security policies.
"""

import os
import pytest
from pathlib import Path

from tests.utils.assertions import assert_file_format_valid
from tests.utils.factories import create_temp_fasta_file

from preprimer.core.security import PathValidator, InputValidator
from preprimer.core.exceptions import SecurityError


@pytest.mark.unit
@pytest.mark.security
class TestPathValidator:
    """Unit tests for PathValidator."""

    def test_sanitize_path_basic(self):
        """Test basic path sanitization."""
        path = PathValidator.sanitize_path("/tmp/test.txt")
        assert isinstance(path, Path)

    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention."""
        with pytest.raises(SecurityError):
            PathValidator.sanitize_path("../../etc/passwd")

    def test_absolute_path_required(self):
        """Test that absolute paths are required."""
        result = PathValidator.sanitize_path("relative/path.txt")
        assert result.is_absolute()

    # ... more tests


@pytest.mark.unit
@pytest.mark.security
class TestInputValidator:
    """Unit tests for InputValidator."""

    def test_validate_sequence_valid(self):
        """Test validation of valid DNA sequence."""
        assert InputValidator.validate_sequence("ATCG")

    def test_validate_sequence_invalid_chars(self):
        """Test rejection of invalid characters."""
        with pytest.raises(ValidationError):
            InputValidator.validate_sequence("ATCGX")

    # ... more tests


@pytest.mark.unit
@pytest.mark.security
class TestFileSizeValidation:
    """Unit tests for file size validation."""

    def test_file_size_within_limit(self, tmp_path):
        """Test file within size limit."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("small content")

        # Should not raise
        PathValidator.validate_file_size(test_file)

    @pytest.mark.slow  # Large file creation is slow
    def test_file_size_exceeds_limit(self, tmp_path):
        """Test file exceeding size limit."""
        test_file = tmp_path / "large.txt"
        # Create large file
        with open(test_file, 'wb') as f:
            f.seek(200 * 1024 * 1024)  # 200MB
            f.write(b'\0')

        with pytest.raises(SecurityError):
            PathValidator.validate_file_size(test_file, max_size=100*1024*1024)

    # ... more tests
```

#### Step 3: Extract Tests from Old Files

For each test class in old files:

1. **Identify unique tests** (skip duplicates)
2. **Copy to new file** under appropriate class
3. **Add markers**
4. **Update assertions** to use test utilities
5. **Simplify test data** using builders/factories

Example transformation:

**Before** (from `test_security_comprehensive.py`):
```python
def test_path_traversal_attack(self):
    """Test path traversal prevention."""
    # Old style - verbose
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/../etc/passwd"
    ]

    for path in malicious_paths:
        with pytest.raises(SecurityError) as exc:
            PathValidator.sanitize_path(path)
        assert "path traversal" in str(exc.value).lower()
```

**After** (in `unit/core/test_security.py`):
```python
@pytest.mark.unit
@pytest.mark.security
@pytest.mark.parametrize("malicious_path", [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32",
    "/etc/../etc/passwd",
])
def test_path_traversal_prevention(self, malicious_path):
    """Test path traversal attack prevention."""
    with pytest.raises(SecurityError, match="path traversal"):
        PathValidator.sanitize_path(malicious_path)
```

**Improvements**:
- ✅ Added markers
- ✅ Used `@pytest.mark.parametrize` for cleaner test data
- ✅ Simplified assertion with `match=` parameter
- ✅ More focused test name

#### Step 4: Remove Old Files

```bash
# After all tests migrated and passing:
git rm tests/test_security.py
git rm tests/test_security_comprehensive.py

# Verify tests still pass
python -m pytest -m security -v
```

#### Step 5: Update Documentation

Add entry to migration log:

```bash
echo "✅ Security tests: tests/test_security*.py → tests/unit/core/test_security.py" >> TEST_MIGRATION_LOG.md
```

---

## Available Test Utilities

### Assertions (`tests/utils/assertions.py`)

| Function | Purpose |
|----------|---------|
| `assert_amplicons_equal()` | Compare two amplicon dictionaries |
| `assert_primer_valid()` | Validate primer meets constraints |
| `assert_file_format_valid()` | Validate file format |
| `assert_conversion_successful()` | Check conversion output |
| `assert_amplicon_structure_valid()` | Validate amplicon structure |
| `assert_no_validation_errors()` | Bulk validation |

### Builders (`tests/utils/builders.py`)

| Builder | Purpose |
|---------|---------|
| `PrimerDataBuilder` | Fluent API for creating primers |
| `AmpliconDataBuilder` | Fluent API for creating amplicons |
| `ConfigBuilder` | Fluent API for creating configs |
| `TestDatasetBuilder` | Create multi-amplicon datasets |

Quick functions:
- `build_primer()` - Quick primer creation
- `build_amplicon()` - Quick amplicon creation
- `build_config()` - Quick config creation

### Factories (`tests/utils/factories.py`)

| Function | Purpose |
|----------|----------|
| `create_minimal_dataset()` | 1 amplicon dataset |
| `create_small_dataset()` | 5 amplicon dataset |
| `create_medium_dataset()` | 80 amplicon dataset |
| `create_circular_genome_dataset()` | Circular genome amplicons |
| `create_degenerate_primer_dataset()` | IUPAC degenerate primers |
| `create_multi_pool_dataset()` | Multi-pool amplicons |
| `create_alternates_dataset()` | Alternate primer options |
| `create_temp_fasta_file()` | Temporary FASTA |
| `create_temp_bed_file()` | Temporary BED |
| `create_temp_varvamp_file()` | Temporary VarVAMP TSV |
| `create_malformed_file()` | Malformed files for error testing |

Scenarios:
```python
from tests.utils.factories import create_dataset_from_scenario, SCENARIO_SMALL

dataset = create_dataset_from_scenario(SCENARIO_SMALL)
```

---

## Running Tests by Layer

### Unit Tests Only (Fast Feedback)

```bash
# All unit tests
python -m pytest -m unit -v

# Specific domain
python -m pytest -m "unit and parser" -v
python -m pytest -m "unit and security" -v

# With coverage
python -m pytest -m unit --cov=preprimer --cov-report=term
```

### Integration Tests

```bash
# All integration tests
python -m pytest -m integration -v

# Quick integration tests only
python -m pytest -m "integration and quick" -v
```

### E2E Tests

```bash
# All end-to-end tests
python -m pytest -m e2e -v

# E2E tests for CLI
python -m pytest tests/e2e/test_cli.py -v
```

### Performance Tests

```bash
# Benchmarks only
python -m pytest -m performance --benchmark-only

# Skip slow performance tests
python -m pytest -m "performance and not stress"
```

### CI-style Layered Run

```bash
# Layer 1: Unit tests (fast feedback)
python -m pytest -m unit --timeout=60

# Layer 2: Integration tests (if unit passes)
python -m pytest -m integration --timeout=300

# Layer 3: E2E tests (if integration passes)
python -m pytest -m e2e --timeout=600

# Layer 4: Performance (optional)
python -m pytest -m performance --benchmark-only
```

---

## Handling Flaky Tests

### Mark Flaky Tests

```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.integration
def test_file_watcher():
    """Test that may fail due to timing issues."""
    # Test implementation
```

### Skip in CI

```python
import os

@pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Flaky in CI due to timing issues"
)
def test_timing_sensitive():
    """Test that's flaky in CI."""
    # Test implementation
```

---

## Fixture Migration

### Before (in root conftest.py)

```python
@pytest.fixture
def sample_primer_data():
    """Sample primer data."""
    return [
        PrimerData(
            name="test_F",
            sequence="ATCG" * 5,
            # ... many fields
        ),
        # ... more primers
    ]
```

### After (in fixtures/conftest.py)

```python
from tests.utils.builders import PrimerDataBuilder

@pytest.fixture
def sample_primer_pair():
    """Sample forward/reverse primer pair."""
    forward = PrimerDataBuilder().with_name("test_F").forward().build()
    reverse = PrimerDataBuilder().with_name("test_R").reverse().build()
    return [forward, reverse]
```

Or use factories directly in tests:

```python
def test_something():
    """Test something."""
    from tests.utils.factories import create_small_dataset

    amplicons = create_small_dataset()
    # Use amplicons in test
```

---

## Migration Checklist

For each test file:

- [ ] Determine test layer (unit/integration/e2e/performance)
- [ ] Create new file in appropriate directory
- [ ] Add test markers (`@pytest.mark.unit`, etc.)
- [ ] Replace custom assertions with utilities
- [ ] Replace manual test data with builders/factories
- [ ] Update imports
- [ ] Run tests and verify they pass
- [ ] Remove old test file
- [ ] Update TEST_MIGRATION_LOG.md

---

## Troubleshooting

### Import Errors

```python
# If you get import errors for test utilities
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Or add to conftest.py
```

### Fixture Not Found

- Check that fixtures are defined in appropriate conftest.py
- Ensure conftest.py is in parent directory or test directory
- Use `pytest --fixtures` to see available fixtures

### Tests Taking Too Long

```bash
# Find slow tests
python -m pytest --durations=10

# Run only fast tests
python -m pytest -m "unit or (integration and quick)" --timeout=10
```

### Markers Not Recognized

```bash
# Verify markers are configured
python -m pytest --markers

# Check pyproject.toml has all markers
```

---

## Migration Priority Order

Suggested order for migrating tests:

### Phase 1: Quick Wins (Week 1)
1. ✅ Infrastructure setup (DONE)
2. `test_core_interfaces.py` → `unit/core/test_interfaces.py` (simple, no dependencies)
3. `test_exceptions*.py` → `unit/core/test_exceptions.py` (merge two files)
4. `test_security*.py` → `unit/core/test_security.py` (merge two files)

### Phase 2: Core Components (Week 2)
5. `test_registry*.py` → `unit/core/test_registry.py` + `performance/test_registry_performance.py`
6. `test_topology*.py` → `unit/utils/test_topology.py` + `integration/test_circular_genome.py`
7. `test_converter*.py` → `unit/core/test_converter.py` + `integration/test_converter.py`
8. `test_enhanced_config.py` → split into unit & integration

### Phase 3: Parsers & Writers (Week 3)
9. All `test_*_parser*.py` → `unit/parsers/`
10. All `test_*_writer*.py` → `unit/writers/`
11. `test_standardized_parser.py` → `unit/parsers/`
12. `test_primerscheme_info*.py` → `unit/core/`

### Phase 4: Integration & E2E (Week 4)
13. `test_integration.py` → `integration/test_parser_writer_integration.py`
14. `test_all_parsers.py` → `integration/test_all_parsers.py`
15. `test_cli.py` → `e2e/test_cli.py` (split into multiple files)
16. `test_real_data*.py` → `e2e/test_real_data.py`
17. `test_main_api*.py` → `integration/test_main_api.py`

### Phase 5: Specialized Tests (Week 5)
18. `test_property_based.py` → `property/test_parsers_property.py`
19. `test_benchmarks.py` → `performance/test_benchmarks.py`
20. `test_alignment.py` → `unit/alignment/test_alignment.py`
21. Fixture cleanup and optimization

---

## Success Metrics

Track progress with:

```bash
# Count migrated tests
find tests/unit tests/integration tests/e2e -name "test_*.py" | wc -l

# Count remaining legacy tests
find tests -maxdepth 1 -name "test_*.py" | wc -l

# Run all tests
python -m pytest -v

# Check coverage
python -m pytest --cov=preprimer --cov-report=term
```

**Goals**:
- [ ] All 636 tests still pass
- [ ] Coverage maintained at ≥96%
- [ ] No root-level test files (except conftest.py)
- [ ] All tests have appropriate markers
- [ ] conftest.py <100 lines
- [ ] conftest_legacy.py removed

---

## Questions?

See also:
- `TEST_REORGANIZATION_PLAN.md` - Detailed reorganization plan
- `tests/utils/assertions.py` - Available assertions
- `tests/utils/builders.py` - Builder patterns
- `tests/utils/factories.py` - Factory functions

Happy migrating! 🚀
