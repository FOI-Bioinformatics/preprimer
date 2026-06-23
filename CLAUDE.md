# CLAUDE.md - PrePrimer Technical Reference

Technical reference for AI assistants working with the PrePrimer codebase.

## Current State (v0.3.0)

**Status:** Beta (active hardening; see CHANGELOG). Matches the
`Development Status :: 4 - Beta` classifier in `pyproject.toml`.

**Codebase Metrics** (measured; keep in sync when they change):
- **Source Code**: ~7,300 lines of Python across 30 modules
- **Test Suite**: 708 tests (700 passing, 8 skipped; 100% of non-skipped pass)
- **Test Coverage**: ~94% line / ~92% branch (`pytest --cov`, `branch=true`).
  The remaining gap is defensive error branches (e.g. permission/timeout
  handlers) and the external-tool alignment success paths not run in CI.
- **Architecture**: Plugin-based with security-focused validation
- **Documentation**: Organized in docs/ directory

**Supported Capabilities:**
- 4 input format parsers: VarVAMP, ARTIC, Olivar, STS
- 5 output format writers: ARTIC, VarVAMP, Olivar, FASTA, STS
- 20 bidirectional conversion pathways
- Primer-to-reference alignment: BLAST, Exonerate, merPCR, me-PCR providers
- Circular genome topology detection and handling
- IUPAC degenerate nucleotide support
- Security validation with 100% security module coverage

**Recent Changes (v0.3.0):**
- Comprehensive writer test coverage (110/113 tests, 97.3%)
- BaseWriterTest pattern for reusable test infrastructure
- Performance baselines established for all writers (51-591µs)
- Enhanced pytest configuration with test layer markers

See [CHANGELOG.md](CHANGELOG.md) for complete release history

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
python -m pytest tests/test_security.py -v

# Core tests
python -m pytest tests/test_core_interfaces.py -v
python -m pytest tests/test_converter*.py -v

# Parser tests
python -m pytest tests/test_*_parser*.py -v

# Writer tests
python -m pytest tests/test_*_writer*.py -v

# Alignment tests (36 tests)
python -m pytest tests/test_alignment.py -v

# Real data validation (23 tests)
python -m pytest tests/test_real_data_comprehensive.py -m real_data -v

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

# Align primers to reference (NEW in v0.2.0)
preprimer align --primers primers.bed --reference genome.fasta --aligner merpcr
preprimer align --primers primers.tsv --reference genome.fasta --aligner blast --output alignment.tsv
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
├── alignment/                     # Alignment providers (NEW in v0.2.0)
│   ├── blast_provider.py          # NCBI BLAST integration
│   ├── exonerate_provider.py      # Exonerate integration
│   ├── merpcr_provider.py         # merPCR (modern Python, recommended)
│   └── mepcr_provider.py          # me-PCR (legacy C tool)
├── parsers/                       # Input format handlers
│   ├── varvamp_parser.py          # VarVAMP TSV (13-column, IUPAC)
│   ├── artic_parser.py            # ARTIC BED (v2.0/v3.0)
│   ├── olivar_parser.py           # Olivar CSV (circular genome support)
│   └── sts_parser.py              # STS TSV (3/4-column, auto-detect)
└── writers/                       # Output format generators
    ├── artic_writer.py            # ARTIC primerscheme structure
    ├── varvamp_writer.py          # VarVAMP TSV output
    ├── olivar_writer.py           # Olivar CSV output
    ├── fasta_writer.py            # Multi-FASTA with metadata
    └── sts_writer.py              # STS TSV output (3/4-column)
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

- **Overall**: ~94% line / ~92% branch coverage (target: do not regress)
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
    ├── testing.md
    ├── security.md
    ├── windows-compatibility.md
    └── validation/      # Validation reports (NEW in v0.2.0)
        ├── README.md
        ├── real-data-testing.md
        └── v0.2.0-validation.md
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

### `release.yml` - Planned (not yet present)
A tag-triggered release workflow (run tests, build wheel + sdist, create the
GitHub release, attach artifacts) is documented here as the intended process but
is **not yet committed** under `.github/workflows/`. Only `ci.yml` exists today.
Add `release.yml` before relying on the tag-push flow below.

**Intended release trigger** (once `release.yml` exists):
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

## Performance Benchmarks

Current performance (v0.3.0):
- Parser creation: ~4.2M ops/sec
- Format detection: ~45K ops/sec
- Small dataset parsing: ~3K ops/sec
- Large dataset (2000+ amplicons): ~37 ops/sec
- Memory baseline: ~50MB

Writer performance:
- FASTA: 51.3µs (19.5K ops/sec)
- Olivar: 55.5µs (18.0K ops/sec)
- STS: 62.9µs (15.9K ops/sec)
- VarVAMP: 69.2µs (14.4K ops/sec)
- ARTIC: 591µs (1.7K ops/sec)

## Design Principles

1. **Security First**: All input validated, no path traversal, size limits enforced
2. **Plugin Architecture**: New formats added without core changes
3. **Topology Aware**: Automatic circular genome detection
4. **Standards Compliant**: Follow primal-page, articbedversion specifications
5. **Well-Tested**: High coverage, comprehensive test suite
6. **Clear Errors**: Informative messages with actionable suggestions
7. **Performance**: Sub-second for typical workloads

## Test Patterns

### BaseParserTest Pattern
- Abstract base class: `tests/unit/parsers/test_base_parser.py`
- 16 inherited tests per parser
- Contract enforcement, security validation, performance benchmarking
- 4 parsers migrated: VarVAMP, ARTIC, Olivar, STS
- 99/99 tests passing (100%)

### BaseWriterTest Pattern
- Abstract base class: `tests/unit/writers/test_base_writer.py`
- 12 inherited tests per writer
- Contract enforcement, validation, performance benchmarking
- 5 writers migrated: VarVAMP, Olivar, STS, ARTIC, FASTA
- 110/113 tests passing (97.3%)

See `docs/development/patterns/` for detailed documentation.

## When in Doubt

1. **Check existing tests** - Patterns already exist
2. **Use StandardizedParser** - Base class handles security and validation
3. **Write tests first** - TDD approach prevents bugs
4. **Run full suite** - `pytest` before committing
5. **Update documentation** - Keep docs synchronized with code changes

---

**Version**: 0.3.0
**Last Updated**: 2026-06-23
**Test Coverage**: ~94% line / ~92% branch (708 tests: 700 passing, 8 skipped)
**Codebase**: ~7,300 lines source across 30 modules
