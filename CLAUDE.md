# CLAUDE.md - PrePrimer Technical Guide

Technical guidance for Claude Code when working with the PrePrimer codebase.

## Current State (v0.2.0)

**Codebase Metrics:**
- 12,853 total lines of Python code across 49 files
- 226 tests (225 passing, 1 skipped) with comprehensive coverage
- Plugin-based architecture with security and performance focus
- Documentation: 16 organized files in 3-tier structure

**Key Strengths:**
- Comprehensive security implementation with path validation
- Performance benchmarks showing sub-second processing for 500+ amplicons
- Property-based testing with Hypothesis for robust validation
- Clean plugin architecture enabling format extensibility

**Documentation Structure (Recently Reorganized):**
```
docs/
├── README.md                 # Navigation hub
├── technical/               # Security, testing, compatibility (3 files)
├── developer/               # Architecture, contributing, extending (5 files)
└── user-guide/              # Installation, usage, CLI reference (7 files)
```

## Development Commands

### Installation and Setup
```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Testing Commands
```bash
# Run all tests (226 total: 225 passing, 1 skipped)
python -m pytest

# Run specific categories
python -m pytest tests/test_security.py -v           # Security validation
python -m pytest tests/test_benchmarks.py -v         # Performance benchmarks
python -m pytest tests/test_property_based.py -v     # Property-based testing
python -m pytest tests/test_integration.py -v        # End-to-end testing

# Coverage and analysis
python -m pytest --cov=preprimer --cov-report=html
python scripts/run_mutation_tests.py                 # Test quality assessment
```

**Test Categories:**
- Property-based (12): Automated input generation with Hypothesis
- Benchmarks (23): Performance validation and regression detection  
- Integration (12): End-to-end workflow testing
- Security (18): Input validation and vulnerability prevention
- Unit tests: Core functionality across all components

### Code Quality
```bash
# Format code with black
black preprimer/ tests/

# Lint with flake8
flake8 preprimer/ tests/

# Type checking with mypy
mypy preprimer/
```

### Running PrePrimer
```bash
# CLI entry point
preprimer --help

# List supported formats
preprimer list

# Get file information
preprimer info your_primers.tsv

# Convert formats
preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic

# Multiple formats with custom prefix
preprimer convert --input primers.tsv --output-dir output/ \
                 --output-formats artic fasta sts --prefix MyVirus
```

## Architecture

Plugin-based primer scheme converter with clean separation of concerns.

### Core Structure
```
preprimer/
├── core/                    # Framework and abstractions
│   ├── interfaces.py        # Abstract base classes (PrimerData, AmpliconData)
│   ├── registry.py          # Plugin auto-registration system
│   ├── converter.py         # Main conversion orchestration
│   ├── config.py            # Configuration management
│   └── security.py          # Input validation and path sanitization
├── parsers/                 # Input format handlers
│   ├── varvamp_parser.py    # VarVAMP TSV format
│   ├── artic_parser.py      # ARTIC BED format  
│   └── olivar_parser.py     # Olivar CSV format
└── writers/                 # Output format generators
    ├── artic_writer.py      # ARTIC BED files
    ├── fasta_writer.py      # Multi-FASTA sequences
    ├── sts_writer.py        # STS validation files
    ├── varvamp_writer.py    # VarVAMP TSV format
    └── olivar_writer.py     # Olivar CSV format
```

### Format Support
**Input**: VarVAMP (.tsv), ARTIC (.bed), Olivar (.csv)  
**Output**: ARTIC (.bed), FASTA (.fasta), STS (.sts.tsv), VarVAMP (.tsv), Olivar (.csv)

### Plugin Registration
```python
from preprimer.core.registry import parser_registry, writer_registry
# Auto-registration on import - new formats integrate seamlessly
```

## Development Guidelines

### Adding New Formats

**Parser** (input format):
```python
from preprimer.core.interfaces import PrimerParser

class MyFormatParser(PrimerParser):
    def can_parse(self, file_path: str) -> bool:
        # Format detection logic
    
    def parse(self, file_path: str) -> list[AmpliconData]:
        # Parsing implementation
```

**Writer** (output format):  
```python
from preprimer.core.interfaces import OutputWriter

class MyFormatWriter(OutputWriter):
    def write(self, amplicons: list[AmpliconData], output_path: str) -> None:
        # Writing implementation
```

Place in `parsers/` or `writers/` directory and import in `__init__.py` for auto-registration.

### Key Specifications

- **Platform**: Linux and macOS only (Unicode limitations prevent Windows support)
- **Python**: 3.8+ (tested through 3.13)
- **Dependencies**: Pydantic ≥2.0, PyYAML ≥6.0, Click ≥8.0
- **Performance**: Sub-second processing for 500+ amplicons
- **Security**: All file operations use path validation and input sanitization

### Security Implementation

```python
from preprimer.core.security import PathValidator, SecurityError

# All file operations use security validation
safe_path = PathValidator.sanitize_path(user_input)
PathValidator.validate_output_directory(output_dir)
```

**Security Features:**
- Path traversal prevention and input sanitization
- Configurable file size limits (default 50MB)
- Safe temporary file handling with cleanup
- Comprehensive security event logging

### Performance Benchmarks

**Key Metrics (Operations/Second):**
- Parser creation: ~4.2M ops/sec
- Format detection: ~45K ops/sec  
- Small dataset parsing: ~3K ops/sec
- Large dataset processing: ~37 ops/sec (2000+ amplicons)

**Processing Times:**
- Small datasets (<50 amplicons): ~300μs
- Medium datasets (50-500): ~2.5ms
- Large datasets (500+): ~26ms

## Current Priorities and Future Plans

### Development Focus Areas

**Near-term (v0.2.x):**
- Maintain comprehensive test coverage (currently 225/226 tests passing)  
- Continue security hardening and input validation improvements
- Performance optimization for larger datasets (>2000 amplicons)
- Documentation maintenance following recent reorganization

**Medium-term (v0.3.x):**
- Windows support investigation (Unicode encoding challenges)
- Additional format support based on community requests
- Web API/service implementation for remote conversion
- Enhanced validation rules and biological constraint checking

**Long-term:**
- Integration with popular sequencing pipelines
- Real-time format validation and conversion
- Advanced primer quality assessment algorithms

### Key Implementation Notes

**Essential Principles:**
- All format conversions preserve data integrity bidirectionally
- Automatic format detection using content analysis + file extensions
- Security-first approach: all file operations use validation utilities
- Plugin architecture enables custom formats without core changes
- Comprehensive error handling with informative validation messages

**Test Data Structure:**
```
tests/test_data/datasets/
├── small/      # COVID-19: 5 amplicons (fast testing)
└── medium/     # ASFV: 80 amplicons (performance testing)
```
Each dataset includes cross-format consistency with realistic biological data.

### Quality Standards

- **Test Coverage**: Maintain >95% across all modules
- **Security**: All file operations require security validation
- **Performance**: Document benchmarks for performance-critical paths
- **Documentation**: Keep aligned with actual implementation (recently reorganized)