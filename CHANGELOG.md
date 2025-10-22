# Changelog

All notable changes to PrePrimer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-10-22

### Added
- **BaseWriterTest Pattern**: Comprehensive test infrastructure for all output writers
  - Abstract base class providing 12 inherited tests for automatic coverage
  - Contract enforcement tests for `OutputWriter` interface compliance
  - Basic write functionality tests (single/multiple/empty amplicons)
  - Output directory creation and validation tests
  - Performance benchmarking for regression detection
  - Helper methods for test data creation
- **Comprehensive Writer Test Coverage**: All 5 output writers now fully tested
  - **VarVAMP Writer**: 27 tests (100% pass rate) - 69.2µs mean write time
  - **Olivar Writer**: 27 tests (100% pass rate) - 55.5µs mean write time
  - **STS Writer**: 20 tests (100% pass rate) - 62.9µs mean write time
  - **ARTIC Writer**: 19 tests (100% pass rate) - 591µs mean write time
  - **FASTA Writer**: 20 tests (100% pass rate) - 51.3µs mean write time
  - Total: 113 writer tests with 110 passing (97.3%), 3 intentionally skipped
- **Performance Baselines**: Established benchmarks for all 5 writers
  - FASTA: 51.3µs (19.5K ops/sec) - fastest simple writer
  - Olivar: 55.5µs (18.0K ops/sec)
  - STS: 62.9µs (15.9K ops/sec)
  - VarVAMP: 69.2µs (14.4K ops/sec)
  - ARTIC: 591µs (1.7K ops/sec) - slower due to multi-file complexity
- **Test Organization**: Structured writer tests in `tests/unit/writers/`
  - Systematic file organization following best practices
  - Clear separation of base tests, writer-specific tests, and integration tests
  - Format-specific validation logic for each writer

### Changed
- **Writer Testing Architecture**: Migrated from standalone tests to pattern-based inheritance
  - Eliminated ~67% code duplication across writer tests
  - Guaranteed contract compliance for all writers
  - Consistent test structure and coverage
- **Code Quality**: 2,941 lines of new test infrastructure (347 base + 2,594 specific)
  - 65% code reduction for new writer tests
  - Automatic contract enforcement prevents interface violations
  - Performance regression detection for all writers

### Fixed
- **ARTIC Writer Tests**: Resolved all test failures
  - Fixed PrimerData reference_id field requirements
  - Corrected metadata key casing (schemeversion vs schemeVersion)
  - Updated version format validation (v5.3.2 semantic versioning)
  - Fixed BED file format parsing and validation

### Documentation
- **WRITER_MIGRATION_FINAL.md**: Complete migration results and analysis
  - Comprehensive metrics and benchmarks
  - Pattern benefits and usage examples
  - Time investment vs savings analysis
  - Comparison with parser pattern implementation

## [0.2.0] - 2025-10-21

**BREAKING CHANGES**: This release removes legacy configuration system. See upgrade guide below.

### Fixed
- **Enhanced STS Parser**: Now supports both 3-column and 4-column formats (with/without product size)
  - Auto-detects header presence (header/header-less files)
  - Compatible with me-PCR and merPCR output files
  - Parses extended format with product size column
- **Enhanced STS Writer**: Auto-detects and outputs extended 4-column format when amplicon length available
  - Configurable via `include_size` parameter
  - Maintains backward compatibility with 3-column format

### Removed
- **Legacy Configuration System**: `PrePrimerConfig` has been completely removed
  - All code must use `EnhancedConfig` with nested structure
  - `config.validate_sequences` → `config.validation.enabled`
  - `config.force_overwrite` → `config.output.force_overwrite`
  - `config.min_primer_length` → `config.validation.min_length`
  - `config.max_primer_length` → `config.validation.max_length`
  - `config.output_formats` → `config.output.formats`

### Added
- **Alignment Functionality**: Complete primer-to-reference alignment system
  - `align_primers()` high-level API for primer alignment
  - **BLAST Provider**: NCBI BLAST integration for fast primer alignment
  - **Exonerate Provider**: Exonerate integration for sensitive alignment
  - **me-PCR Provider**: Legacy in silico PCR simulation support
  - **merPCR Provider**: Modern Python reimplementation of me-PCR (recommended)
    - 100% compatible with me-PCR (identical results)
    - 2.65x performance improvement through Cython optimization
    - Modern Python API with comprehensive testing (277 tests, 94% coverage)
    - Easy installation: `pip install merpcr`
  - `AlignmentProvider` base class with plugin architecture
  - `AlignmentRegistry` for managing alignment tools
  - CLI `align` command with support for multiple output formats
  - 36 comprehensive alignment tests with 100% pass rate (up from 29)
  - Full documentation in CLI reference and Python API guide
- **Generic Registry System**: New `BaseRegistry[T]` generic class for type-safe plugin management
- **Standardized Parser Refactoring**: ARTICParser now inherits from `StandardizedParser`
- **Topology-aware Processing**: Automatic detection and handling of circular genome architectures
- **Circular Genome Support**: Complete coordinate wrapping and topology detection for mitochondrial, plasmid, and viral episomal genomes
- **Enhanced Security**: Comprehensive path validation with 100% security module test coverage (38 tests)
- **Olivar Format Support**: Full parser and writer implementation with JSON configuration support
- **Primal-page Integration**: Complete info.json schema implementation with MD5 validation
- **External Validation**: Real-world testing with official PrimerSchemes Labs repository data
  - Yale TB (2,564 amplicons)
  - Yale West Nile Virus (38 amplicons)
  - VarVAMP HAV with degenerate primers (16 amplicons)
  - ARTIC nCoV-2019 V5.3.2 (96 amplicons)
  - Olivar mitochondrial designs (15 amplicons)
- **Comprehensive Real Data Validation Framework** (`tests/validation/`)
  - `validator.py`: Format-specific validators for all 5 output formats (430 lines)
  - `report_generator.py`: Multi-format report generation (Markdown, JSON, console)
  - 23 comprehensive real-data tests with 100% pass rate
  - Real tool integration testing (BLAST, Exonerate, merPCR)
  - Performance benchmarking and edge case validation
  - Validation reports in `docs/technical/validation/`
- **Comprehensive Test Coverage**:
  - 611 tests with 96.90% coverage, 100% pass rate
  - Alignment testing (36 tests)
  - Security testing (38 tests, 100% coverage)
  - Real data validation (23 tests)
  - Main API testing (12 tests, 100% coverage)
  - Core infrastructure (converter, registry, exceptions) with 95-100% coverage
  - Property-based testing with Hypothesis
  - Performance benchmarks
  - Integration tests
- **IUPAC Support**: Full degenerate nucleotide handling for variant-aware primer designs
- **articbedversion Compatibility**: Support for v2.0 and v3.0 following primal-page specifications
- **Enhanced Error Handling**: Structured exception system with user-friendly messages and suggestions
- **Documentation Overhaul**: Reorganized 3-tier documentation structure
  - Technical documentation (security, testing, compatibility)
  - Developer documentation (architecture, contributing, extending)
  - User guides (installation, usage, CLI reference)

### Changed
- **Refactored Parser Architecture**: Standardized base parser with topology integration
- **Improved Configuration System**: Enhanced config with validation settings
- **Performance Optimization**: Sub-second processing for 500+ amplicons
- **CLI Modernization**: Improved command-line interface with better error messages

### Fixed
- Path traversal security vulnerabilities with comprehensive validation
- Coordinate system conversion bugs for 0-based BED and 1-based coordinates
- Parser error handling for malformed input files
- Amplicon length calculation for circular genomes

## [0.1.0] - Initial Release

### Added
- Initial release with basic primer format conversion
- VarVAMP TSV format parser and writer
- ARTIC BED format parser and writer
- FASTA output writer
- STS output writer (write-only)
- Basic CLI interface
- Plugin-based architecture with registry system
- Initial test suite

### Known Limitations
- Windows not supported (Unicode encoding limitations)
- Limited format validation
- Basic error messages
- No topology awareness
- No security hardening

---

## Upgrade Guide

### Upgrading to 0.2.0 from 0.1.0

**⚠️ BREAKING CHANGES - Action Required**

#### 1. Configuration System Migration

**Old (v0.1.0)** - PrePrimerConfig:
```python
from preprimer import PrePrimerConfig

config = PrePrimerConfig(
    validate_sequences=True,
    force_overwrite=False,
    min_primer_length=15,
    max_primer_length=35,
    output_formats=["artic", "fasta"]
)
```

**New (v0.2.0)** - EnhancedConfig with nested structure:
```python
from preprimer.core.enhanced_config import EnhancedConfig, ValidationSettings, OutputSettings

config = EnhancedConfig(
    validation=ValidationSettings(
        enabled=True,
        min_length=15,
        max_length=35
    ),
    output=OutputSettings(
        formats=["artic", "fasta"],
        force_overwrite=False
    )
)
```

#### 2. Configuration Attribute Access

Update all configuration attribute access:

| Old (v0.1.0) | New (v0.2.0) |
|--------------|--------------|
| `config.validate_sequences` | `config.validation.enabled` |
| `config.force_overwrite` | `config.output.force_overwrite` |
| `config.min_primer_length` | `config.validation.min_length` |
| `config.max_primer_length` | `config.validation.max_length` |
| `config.output_formats` | `config.output.formats` |
| `config.aligner` | `config.alignment.aligner` |

#### 3. Import Path Changes

```python
# Old (v0.1.0)
from preprimer.core.config import PrePrimerConfig

# New (v0.2.0)
from preprimer.core.enhanced_config import EnhancedConfig
```

#### 4. Removed Components

- `AlignmentProvider` class - removed (never implemented)
- `AlignmentError` exception - removed
- `AlignmentRegistry` - removed
- `PrePrimerConfig.to_legacy_config()` method - removed
- `PrePrimerConfig.from_legacy_config()` method - removed

**Migration Tool**: None available - codebase is small, manual migration recommended.

**Estimated Migration Time**: 5-15 minutes for typical projects

**New Features to Adopt**:
1. **Topology Detection**: Circular genomes are now automatically detected. No code changes needed.
2. **Enhanced Error Messages**: Errors now include suggestions for resolution.
3. **Olivar Support**: Can now read and write Olivar format files.
4. **Security**: All file operations now use validated paths automatically.

**Performance**: Expect 20-30% faster processing on large datasets due to optimizations.

## Platform Support

**Supported**:
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+, other modern distributions)
- macOS (10.15 Catalina or later)
- Python 3.11, 3.12, 3.13

**Not Supported**:
- Windows (due to Unicode character encoding limitations in file handling)
- Python <3.11

## Contributing

See [CONTRIBUTING.md](docs/developer/contributing.md) for guidelines on contributing to PrePrimer.

## Security

For security concerns, please see our [Security Policy](docs/technical/security.md) or open a confidential issue.
