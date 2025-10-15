# Changelog

All notable changes to PrePrimer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- STS parser implementation for bidirectional format conversion
- Comprehensive STS parser test suite
- API documentation with code examples
- Examples directory with practical usage samples
- PyPI publishing automation via GitHub Actions
- Release checklist and version management documentation
- Large-scale stress tests (10,000+ amplicons)
- Windows incompatibility documentation

### Changed
- Updated package metadata for accurate OS support declaration
- Fixed repository URLs in pyproject.toml
- Improved package distribution configuration

### Fixed
- Package classifiers now correctly reflect Linux/macOS-only support

## [0.2.0] - 2024-10-14

### Added
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
- **Comprehensive Test Coverage**:
  - 581 tests with 96.90% coverage
  - Security testing (38 tests, 100% coverage)
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

**Breaking Changes**: None - v0.2.0 is backward compatible with v0.1.0.

**New Features to Adopt**:
1. **Topology Detection**: Circular genomes are now automatically detected. No code changes needed.
2. **Enhanced Error Messages**: Errors now include suggestions for resolution.
3. **Olivar Support**: Can now read and write Olivar format files.
4. **Security**: All file operations now use validated paths automatically.

**Deprecated**: None

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
