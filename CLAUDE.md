# CLAUDE.md - PrePrimer Technical Guide

This file provides comprehensive technical guidance to Claude Code (claude.ai/code) when working with the PrePrimer codebase.

## Current State Analysis (v0.2.0)

**Codebase Metrics:**
- 12,363 total lines of Python code across 47 files
- 226 tests (225 passing, 1 skipped) representing comprehensive coverage  
- Modern plugin-based architecture with 9 core files, 6 parsers, 8 writers
- Performance characteristics: sub-second processing for datasets up to 500 amplicons

**Architecture Status:**
The codebase implements a complete refactor with:
- Security utilities providing input validation and path sanitization
- Enhanced configuration system with multi-format support
- Comprehensive testing framework across multiple methodologies
- Unified test data structure enabling cross-format validation
- Performance optimizations with documented benchmarks

**Development Priorities:**
1. Maintain comprehensive test coverage across all modules
2. Ensure security validation for all file operations
3. Document performance characteristics and limitations
4. Update documentation with evidence-based claims

## Development Commands

### Installation and Setup
```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Testing Framework
```bash
# Run complete test suite (226 total tests)
python -m pytest

# Run specific test categories
python -m pytest tests/test_property_based.py -v      # Property-based testing with Hypothesis
python -m pytest tests/test_benchmarks.py -v         # Performance benchmarking
python -m pytest tests/test_integration.py -v        # End-to-end integration testing
python -m pytest tests/test_security.py -v           # Security validation testing

# Generate coverage reports
python -m pytest --cov=preprimer --cov-report=html --cov-report=term-missing

# Run performance benchmarks
python -m pytest tests/test_benchmarks.py --benchmark-only

# Property-based testing with statistical output
python -m pytest tests/test_property_based.py -v --hypothesis-show-statistics

# Execute mutation testing for test quality assessment
python scripts/run_mutation_tests.py
```

**Testing Architecture:**
- **Property-based**: 12 tests with automated input generation via Hypothesis
- **Performance benchmarks**: 23 tests with statistical analysis and regression detection
- **Integration testing**: 12 end-to-end workflow validation tests
- **Security validation**: 18 tests for input validation and vulnerability prevention
- **Unit testing**: Core functionality validation across parsers, writers, and components

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

## Architecture Overview

PrePrimer is a modern, extensible primer scheme converter built around a plugin-based architecture:

### Core Components

**`preprimer/core/`** - Central abstractions and framework:
- `interfaces.py`: Abstract base classes for parsers, writers, and alignment providers
- `registry.py`: Plugin registration system for parsers and writers
- `converter.py`: Main conversion orchestration logic
- `config.py`: Configuration management system
- `exceptions.py`: Custom exception hierarchy

**`preprimer/parsers/`** - Input format parsers:
- `varvamp_parser.py`: Handles VarVAMP TSV format
- `artic_parser.py`: Handles ARTIC BED format
- `olivar_parser.py`: Handles Olivar CSV format

**`preprimer/writers/`** - Output format writers:
- `artic_writer.py`: Generates ARTIC BED files
- `fasta_writer.py`: Generates FASTA primer files
- `sts_writer.py`: Generates STS files for me-pcr validation
- `varvamp_writer.py`: Generates VarVAMP TSV format
- `olivar_writer.py`: Generates Olivar CSV format

### Data Structures

The system uses standardized data classes defined in `core/interfaces.py`:

- **`PrimerData`**: Represents individual primers with sequence, coordinates, direction, pool information, and quality metrics
- **`AmpliconData`**: Groups primers into amplicons with helper methods for primer pair generation

### Plugin System

New parsers and writers are automatically registered through the registry system:
```python
from preprimer.core.registry import parser_registry, writer_registry

# Parsers and writers self-register when imported
# Registration happens automatically during module import
```

### Format Support

**Supported Input Formats:**
- VarVAMP (`.tsv`, `.txt`)
- ARTIC (`.bed`, `.scheme.bed`) 
- Olivar (`.csv`)

**Supported Output Formats:**
- ARTIC (`.scheme.bed`) - For `artic minion` workflows
- FASTA (`.fasta`) - Multi-FASTA primer sequences
- STS (`.sts.tsv`) - For me-pcr in-silico validation
- VarVAMP (`.tsv`) - VarVAMP-compatible format
- Olivar (`.csv`) - Olivar primer design format

## Development Guidelines

### Adding New Formats

1. **Create a Parser** (for input formats):
   - Inherit from `PrimerParser` in `core/interfaces.py`
   - Implement required abstract methods
   - Add to `parsers/` directory
   - Import in appropriate `__init__.py` for auto-registration

2. **Create a Writer** (for output formats):
   - Inherit from `OutputWriter` in `core/interfaces.py` 
   - Implement required abstract methods
   - Add to `writers/` directory
   - Import in appropriate `__init__.py` for auto-registration

### Testing Strategy

- **Unit tests** for individual parsers and writers in `tests/`
- **Integration tests** for complete conversion workflows
- **Test data** located in `tests/test_data/`
- Use `conftest.py` for shared test fixtures

### Key Constraints & Technical Specifications

- **Platform Support**: Linux and macOS only (no Windows due to Unicode limitations)
- **Python Requirements**: Python 3.8+ required (tested up to 3.13)
- **Core Dependencies**: Pydantic (>=2.0), PyYAML (>=6.0), Click (>=8.0)
- **Performance**: Sub-second processing for datasets up to 500 amplicons
- **Memory Usage**: ~50MB baseline, ~200MB for large datasets (2000+ amplicons)
- **Security**: Input validation, path sanitization, safe file operations

### 🔒 Security Architecture

**Enhanced Security Features:**
```python
from preprimer.core.security import PathValidator, SecurityError

# Safe path operations
safe_path = PathValidator.sanitize_path(user_input)
PathValidator.validate_output_directory(output_dir)

# Input validation with size limits
validated_content = InputValidator.validate_file_content(content, max_size_mb=10)
```

**Security Measures:**
- Path traversal prevention (`../`, `~`, absolute path validation)
- File size limits (configurable, default 50MB)
- Input sanitization for all user-provided data
- Safe temporary file handling with automatic cleanup
- Comprehensive logging of security events

### ⚡ Performance Characteristics

**Benchmark Results (Operations Per Second):**
- **Parser Creation**: 4,244,769 ops/sec (217ns mean)
- **Data Structure Creation**: 3,211,140 ops/sec (311ns mean) 
- **Format Detection**: 44,564 ops/sec (22.4μs mean)
- **VarVAMP Parsing**: 2,896 ops/sec (345μs mean, small datasets)
- **ARTIC Parsing**: 3,021 ops/sec (331μs mean)
- **Large Dataset Processing**: 37 ops/sec (26.6ms mean, 2000+ amplicons)

**Scalability Limits:**
- **Small datasets** (<50 amplicons): ~300μs processing time
- **Medium datasets** (50-500 amplicons): ~2.5ms processing time  
- **Large datasets** (500+ amplicons): ~26ms processing time
- **Memory scaling**: Linear O(n) with amplicon count

### 🏗️ Advanced Architecture

**Enhanced Configuration System:**
```python
from preprimer.core.enhanced_config import EnhancedConfigManager

# Multi-format configuration support
config = EnhancedConfigManager.from_file("config.yaml")
config = EnhancedConfigManager.from_dict(config_dict)
config = EnhancedConfigManager.from_env()  # Environment variables

# Dynamic configuration updates
config.update_section("parsing", {"strict_validation": True})
config.merge_with_file("additional_config.json")
```

**Registry System Deep Dive:**
```python
from preprimer.core.registry import parser_registry, writer_registry

# Automatic discovery and registration
parser_registry.auto_discover("preprimer.parsers")
writer_registry.auto_discover("preprimer.writers") 

# Runtime plugin loading
parser_registry.register_from_module("custom_parsers.my_format")

# Performance-optimized lookups O(1)
parser = parser_registry.get("varvamp")
writer = writer_registry.get("artic")
```

**Data Validation Pipeline:**
- **Level 1**: File format detection (extension + content analysis)
- **Level 2**: Schema validation (Pydantic models)  
- **Level 3**: Biological constraint validation (primer lengths, coordinates)
- **Level 4**: Cross-format consistency checks
- **Level 5**: Security validation (path safety, content sanitization)

### 🧪 Test Data Architecture

**Unified Test Dataset Structure:**
```
tests/test_data/
├── datasets/
│   ├── small/                   # COVID-19: 5 amplicons, 10 primers
│   │   ├── reference.fasta      # NC_045512.2 (29,903 bp)
│   │   ├── varvamp.tsv         # 13-field format with quality metrics
│   │   ├── artic.scheme.bed    # 7-field format with sequences
│   │   ├── olivar.csv          # CSV design format
│   │   └── metadata.yaml       # Dataset documentation
│   └── medium/                  # ASFV: 80 amplicons, 160 primers
│       └── [same format structure]
├── fixtures/                    # Malformed data for error testing
└── legacy/                      # Original test files (preserved)
```

**Test Data Characteristics:**
- **Small dataset**: 5 amplicons, ~1.5kb coverage, COVID-19
- **Medium dataset**: 80 amplicons, 191kb coverage, ASFV  
- **Cross-format consistency**: Same biological data across all formats
- **Quality metrics**: Realistic primer scores, GC content, secondary structure
- **Edge cases**: Overlapping amplicons, primer dimers, extreme coordinates

## Implementation Guidelines

### Development Workflow
1. **Testing**: Maintain comprehensive test coverage for all new functionality
2. **Security**: Validate all file operations and user inputs
3. **Performance**: Document performance characteristics with benchmarks
4. **Documentation**: Update relevant documentation with implementation changes

### Architecture Considerations
- **Plugin system**: New parsers and writers should follow established interfaces
- **Error handling**: Implement comprehensive error handling with informative messages
- **Configuration**: Support flexible configuration through multiple sources
- **Cross-platform**: Ensure compatibility with Linux and macOS platforms

### Quality Assurance
- **Test coverage**: Maintain >95% test coverage across all modules
- **Security validation**: All file operations must use security utilities
- **Performance monitoring**: Benchmark performance-critical operations
- **Documentation accuracy**: Ensure documentation reflects actual implementation

## Important Notes

- **All format conversions are bidirectional** with data integrity preservation
- **Automatic format detection** based on content analysis + file extensions  
- **Quality metrics preservation** across all conversion workflows
- **Reference sequence association** maintained for alignment-dependent formats
- **Comprehensive error recovery** with detailed validation messages
- **Plugin extensibility** for custom formats without core code changes