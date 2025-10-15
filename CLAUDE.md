# CLAUDE.md - PrePrimer Technical Guide

Technical guidance for Claude Code when working with the PrePrimer codebase.

## Current State (v1.0.0 Ready)

**Status:** Production-ready for v1.0.0 release

**Codebase Metrics:**
- **Code**: ~20,000 lines of Python across 59 files
- **Tests**: 611 tests with 96.90% coverage
- **Architecture**: Plugin-based with security focus
- **Documentation**: Complete, organized in docs/

**Key Capabilities:**
- 4 input formats: VarVAMP, ARTIC, Olivar, STS
- 5 output formats: ARTIC, VarVAMP, Olivar, FASTA, STS
- 20 bidirectional conversion pathways
- Circular genome topology detection and handling
- IUPAC degenerate nucleotide support
- Security hardening with 100% security module coverage

## Quick Commands

### Development

```bash
# Install for development
pip install -e ".[dev]"

# Run tests (fast)
python -m pytest

# Run tests with coverage
python -m pytest --cov=preprimer --cov-report=html

# Format code
black preprimer/ tests/
isort preprimer/ tests/

# Check code quality
flake8 preprimer/ tests/ --max-line-length=88 --extend-ignore=E203,W503
mypy preprimer/ --ignore-missing-imports
bandit -r preprimer/ -ll
```

### Testing Categories

```bash
# Security tests (38 tests, 100% coverage)
python -m pytest tests/test_security_comprehensive.py -v

# Core tests
python -m pytest tests/test_core_interfaces.py -v
python -m pytest tests/test_converter*.py -v

# Parser tests
python -m pytest tests/test_*_parser*.py -v

# Writer tests
python -m pytest tests/test_*_writer*.py -v

# Topology tests (circular genomes)
python -m pytest tests/test_topology.py -v
python -m pytest tests/test_circular_genome.py -v

# Integration tests
python -m pytest tests/test_integration.py -v

# Benchmarks
python -m pytest tests/test_benchmarks.py -v --benchmark-only
```

### CLI Usage

```bash
# List formats
preprimer list

# Get file info
preprimer info your_primers.tsv

# Convert
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic

# Multiple formats
preprimer convert --input primers.tsv --output-dir output/ \
                  --output-formats artic fasta sts varvamp olivar --prefix MyVirus
```

## Architecture

```
preprimer/
├── core/                          # Framework
│   ├── converter.py               # Main conversion orchestration
│   ├── interfaces.py              # Data models (PrimerData, AmpliconData)
│   ├── registry.py                # Plugin auto-registration
│   ├── topology.py                # Circular genome detection
│   ├── security.py                # Input validation (100% coverage)
│   ├── standardized_parser.py     # Base parser class
│   └── primerscheme_info.py       # Primal-page info.json schema
├── parsers/                       # Input format handlers
│   ├── varvamp_parser.py          # VarVAMP TSV (13-column, IUPAC)
│   ├── artic_parser.py            # ARTIC BED (v2.0/v3.0)
│   ├── olivar_parser.py           # Olivar CSV (circular genome support)
│   └── sts_parser.py              # STS TSV (3-column, minimal)
└── writers/                       # Output format generators
    ├── artic_writer.py            # ARTIC primerscheme structure
    ├── varvamp_writer.py          # VarVAMP TSV output
    ├── olivar_writer.py           # Olivar CSV output
    ├── fasta_writer.py            # Multi-FASTA with metadata
    └── sts_writer.py              # STS TSV output
```

## Key Implementation Patterns

### 1. Adding a New Parser

```python
from preprimer.core.standardized_parser import StandardizedParser
from preprimer.core.interfaces import AmpliconData

class MyFormatParser(StandardizedParser):
    @classmethod
    def format_name(cls) -> str:
        return "myformat"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".myformat"]

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        # Check if file is this format
        pass

    def _parse_file_content(self, file_path: Path, prefix: str) -> Dict[str, AmpliconData]:
        # Parse and return amplicons
        pass
```

Register in `preprimer/parsers/__init__.py`:
```python
from .myformat_parser import MyFormatParser
parser_registry.register(MyFormatParser)
```

### 2. Security Validation

ALL file operations must use security validation:

```python
from preprimer.core.security import PathValidator

# Validate and sanitize paths
safe_path = PathValidator.sanitize_path(user_input)
PathValidator.validate_file_size(safe_path)
PathValidator.validate_output_directory(output_dir)
```

### 3. Topology Handling

For circular genomes (mitochondrial, plasmids):

```python
from preprimer.core.topology import TopologyDetector, GenomeTopology

detector = TopologyDetector()
topology = detector.detect_topology(amplicons, reference_length=16569)

if topology == GenomeTopology.CIRCULAR:
    # Handle cross-origin amplicons (start > end)
    actual_length = detector.calculate_amplicon_length(
        start=16400, end=200, reference_length=16569, is_circular=True
    )
```

### 4. Error Handling

Use structured exceptions:

```python
from preprimer.core.exceptions import (
    ParserError,
    InvalidFormatError,
    CorruptedDataError,
    SecurityError,
)

# Raise with user-friendly messages
raise InvalidFormatError(
    file_path,
    expected_format="VarVAMP TSV",
    user_message="File does not match VarVAMP format."
).add_suggestion("Check file has 13 tab-separated columns")
```

## Test Data

```
tests/test_data/datasets/
├── small/              # COVID-19, 5 amplicons (fast testing)
├── medium/             # ASFV, 80 amplicons (performance)
└── mitochondrial/      # Human mtDNA, 8 amplicons (circular genome)

tests/test_data/external_schemes/
├── yale-tb/            # M. tuberculosis, 2,564 amplicons
├── yale-west-nile-virus/  # WNV, 38 amplicons
├── varvamp-hav/        # Hepatitis A with degenerate primers
├── nCoV-2019-V532/     # ARTIC SARS-CoV-2 V5.3.2
└── olivar-mitochondrial/  # Olivar-generated, 15 amplicons
```

## Code Quality Standards

### Required Before Commit

```bash
# Format code
black preprimer/ tests/

# Sort imports
isort preprimer/ tests/

# Check linting (warnings OK, errors not OK)
flake8 preprimer/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Run tests
python -m pytest
```

### Test Coverage Requirements

- **Overall**: ≥95% (currently 96.90%)
- **Security module**: 100% (achieved)
- **New features**: Must include tests
- **Bug fixes**: Must include regression test

### Performance Targets

- Small datasets (<50 amplicons): <1 second
- Medium datasets (50-500): <5 seconds
- Large datasets (500+): <30 seconds
- Validated up to 2,564 amplicons

## Common Development Tasks

### Task: Fix a Parser Bug

1. **Write failing test**:
```python
def test_bug_description():
    parser = VarVAMPParser()
    # Test case that reproduces bug
    amplicons = parser.parse("test_file.tsv", prefix="test")
    assert expected_behavior
```

2. **Fix the bug** in parser code

3. **Verify fix**:
```bash
python -m pytest tests/test_varvamp_parser.py -v
python -m pytest  # Full suite
```

4. **Check code quality**:
```bash
black preprimer/parsers/varvamp_parser.py
flake8 preprimer/parsers/varvamp_parser.py
```

### Task: Add New Output Format

1. **Create writer** in `preprimer/writers/`:
```python
class MyFormatWriter(OutputWriter):
    def format_name(self) -> str:
        return "myformat"

    def write(self, amplicons, output_path, **kwargs):
        # Implementation
        pass
```

2. **Register** in `preprimer/writers/__init__.py`

3. **Write tests** in `tests/test_myformat_writer.py`

4. **Update documentation** in `docs/user-guide/supported-formats.md`

### Task: Improve Performance

1. **Profile current performance**:
```python
import cProfile
profiler = cProfile.Profile()
profiler.enable()
# Run conversion
profiler.disable()
profiler.print_stats(sort='cumulative')
```

2. **Run benchmarks**:
```bash
python -m pytest tests/test_benchmarks.py --benchmark-only
```

3. **Optimize bottlenecks**

4. **Verify no regression**:
```bash
python -m pytest tests/test_benchmarks.py --benchmark-compare
```

## Documentation Structure

```
docs/
├── user-guide/          # User-facing documentation
│   ├── installation.md
│   ├── quick-start.md
│   ├── basic-usage.md
│   ├── cli-reference.md
│   ├── supported-formats.md
│   └── configuration.md
├── developer/           # Developer documentation
│   ├── architecture.md
│   ├── adding-parsers.md
│   ├── contributing.md
│   └── release-checklist.md
├── api/                 # API reference
│   └── python-api.md
└── technical/           # Technical specifications
    └── windows-compatibility.md
```

**Update documentation when:**
- Adding new formats
- Changing CLI commands
- Modifying API
- Fixing bugs that affect usage

## CI/CD

**GitHub Actions workflows** (simplified):

### `ci.yml` - Runs on every push/PR
- Tests on Ubuntu + macOS
- Python 3.11, 3.12, 3.13
- Code quality checks (black, isort, flake8, mypy)
- Security scan (bandit)
- ~3-5 minutes

### `release.yml` - Runs on version tags
- Run tests
- Build package (wheel + sdist)
- Create GitHub release
- Attach build artifacts
- ~2-3 minutes

**Trigger release**:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Important Files

### Root Directory
- `README.md` - User-facing overview
- `CLAUDE.md` - This file (for Claude Code)
- `CHANGELOG.md` - Version history
- `SECURITY.md` - Security policy
- `CITATION.cff` - Citation metadata
- `LICENSE` - MIT license

### Configuration
- `pyproject.toml` - Dependencies, build config
- `MANIFEST.in` - Package distribution files

### Examples
- `examples/` - 5 runnable examples

## Platform-Specific Notes

### Linux/macOS
- ✅ Full support
- ✅ All Unicode characters work
- ✅ Performance optimized

### Windows
- ❌ Not supported (Unicode console issues)
- ✅ WSL2 works perfectly
- See `docs/technical/windows-compatibility.md` for details

## Security Considerations

**ALL file operations must**:
1. Validate paths (no path traversal)
2. Check file sizes
3. Sanitize input
4. Use secure temporary files

**Security module has 100% test coverage** - maintain this!

## Release Process

**See full checklist**: `docs/developer/release-checklist.md`

**Quick version**:
1. Update version in `preprimer/__init__.py`
2. Update `CHANGELOG.md` with release date
3. Commit: `git commit -m "chore: Prepare v1.0.0"`
4. Tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Push tag: `git push origin v1.0.0`
6. CI automatically builds and creates release

## Debugging Tips

### Parser Issues
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Parse with detailed logs
parser = VarVAMPParser()
amplicons = parser.parse("file.tsv", prefix="debug")
```

### Topology Issues
```python
# Check topology detection
from preprimer.core.topology import TopologyDetector
detector = TopologyDetector()
topology = detector.detect_topology(amplicons, reference_length=16569)
print(f"Detected: {topology.value}")
```

### Security Issues
```python
# Test path validation
from preprimer.core.security import PathValidator
safe_path = PathValidator.sanitize_path("../../etc/passwd")  # Should fail
```

## Performance Benchmarks (Reference)

**Current performance** (as of v1.0.0):
- Parser creation: ~4.2M ops/sec
- Format detection: ~45K ops/sec
- Small dataset parsing: ~3K ops/sec
- Large dataset (2000+ amplicons): ~37 ops/sec
- Memory: ~50MB baseline

**If making changes that affect performance**, run benchmarks and compare.

## Key Design Principles

1. **Security First**: All input validated, no path traversal, size limits
2. **Plugin Architecture**: Easy to add new formats without core changes
3. **Topology Aware**: Automatic circular genome detection and handling
4. **Standards Compliant**: Follow primal-page, articbedversion specs
5. **Well-Tested**: High coverage, comprehensive test suite
6. **User-Friendly Errors**: Informative messages with suggestions
7. **Performance**: Sub-second for typical workloads

## When in Doubt

1. **Check existing tests**: Pattern already exists
2. **Use StandardizedParser**: Base class handles security, validation
3. **Write tests first**: TDD approach prevents bugs
4. **Run full suite**: `pytest` before committing
5. **Check documentation**: Update if behavior changes

---

**Version**: 1.0.0
**Last Updated**: 2024-10-14
**Test Coverage**: 96.90% (611 tests)
