# CLAUDE.md - PrePrimer Technical Guide

Technical guidance for Claude Code when working with the PrePrimer codebase.

## Current State (v0.2.0)

**Codebase Metrics:**
- 19,985 total lines of Python code across 59 files
- 581 tests with 96.90% comprehensive coverage including external scheme validation
- Plugin-based architecture with security and performance focus
- Documentation: 16 organized files in 3-tier structure

**Key Strengths:**
- Comprehensive security implementation with path validation
- Performance benchmarks showing sub-second processing for 500+ amplicons
- Property-based testing with Hypothesis for robust validation
- Clean plugin architecture enabling format extensibility
- Circular genome topology detection and coordinate wrapping support
- Real-world validation with official PrimerSchemes Labs repository data
- Complete articbedversion compatibility (v2.0, v3.0) following primal-page specifications

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
# Run all tests (581 total with 96.90% comprehensive coverage)
python -m pytest

# Run comprehensive test suites (new coverage-focused tests)
python -m pytest tests/test_security_comprehensive.py -v         # Security validation (38 tests)
python -m pytest tests/test_main_api_comprehensive.py -v          # Main API testing (12 tests)
python -m pytest tests/test_converter_comprehensive_gaps.py -v    # Core converter (9 tests)
python -m pytest tests/test_exceptions_comprehensive.py -v        # Exception system (25 tests)
python -m pytest tests/test_registry_comprehensive.py -v          # Registry system (16 tests)
python -m pytest tests/test_artic_parser_comprehensive.py -v      # ARTIC parser (22 tests)
python -m pytest tests/test_sts_writer_comprehensive.py -v        # STS writer (12 tests)

# Run specific categories
python -m pytest tests/test_benchmarks.py -v            # Performance benchmarks
python -m pytest tests/test_property_based.py -v        # Property-based testing
python -m pytest tests/test_integration.py -v           # End-to-end testing
python -m pytest tests/test_topology.py -v              # Circular genome testing
python -m pytest tests/test_all_parsers.py -v           # Parser consistency validation
python -m pytest tests/test_olivar_parser.py -v         # Olivar format testing

# Coverage and analysis
python -m pytest --cov=preprimer --cov-report=html
python scripts/run_mutation_tests.py                    # Test quality assessment
```

**Test Categories:**
- **Comprehensive Coverage Tests (134)**: Security (38), Main API (12), Converter (9), Exceptions (25), Registry (16), Parser edge cases (22), Writer coverage (12)
- **Property-based (12)**: Automated input generation with Hypothesis
- **Benchmarks (23)**: Performance validation and regression detection  
- **Integration (12+)**: End-to-end workflow testing
- **Topology (20)**: Circular genome coordinate handling and detection
- **External validation**: Real-world schemes from PrimerSchemes Labs repository
- **Unit tests**: Core functionality across all components
- **Total: 581 tests with 96.90% coverage**

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
├── core/                          # Framework and abstractions
│   ├── interfaces.py              # Abstract base classes (PrimerData, AmpliconData)
│   ├── registry.py                # Plugin auto-registration system
│   ├── converter.py               # Main conversion orchestration
│   ├── config.py                  # Configuration management
│   ├── security.py                # Input validation and path sanitization
│   ├── topology.py                # Genome topology detection and circular coordinate handling
│   ├── standardized_parser.py     # Base parser with topology integration
│   └── primerscheme_info.py       # Primal-page info.json schema implementation
├── parsers/                       # Input format handlers
│   ├── varvamp_parser.py          # VarVAMP TSV format with IUPAC degenerate support
│   ├── artic_parser.py            # ARTIC BED format (v2.0/v3.0 articbedversion)
│   ├── olivar_parser.py           # Olivar CSV format with enhanced validation
│   └── sts_parser.py              # STS TSV format
└── writers/                       # Output format generators
    ├── artic_writer.py            # Official primerscheme structure (primer.bed + info.json)
    ├── fasta_writer.py            # Multi-FASTA sequences
    ├── sts_writer.py              # STS validation files
    ├── varvamp_writer.py          # VarVAMP TSV format (full column specification)
    └── olivar_writer.py           # Olivar CSV format
```

### Format Support

**Input Formats:**
- **VarVAMP** (.tsv): Full 13-column specification with IUPAC degenerate nucleotide support
- **ARTIC** (.bed): Compatible with articbedversion v2.0 and v3.0 following primal-page specifications
- **Olivar** (.csv): Native Olivar-generated CSV format with comprehensive metadata
- **STS** (.sts.tsv): Simple primer format for basic conversion workflows

**Output Formats:**
- **ARTIC** (.bed): Official primerscheme structure (primer.bed + reference.fasta + info.json)
- **VarVAMP** (.tsv): Complete 13-column format compatible with VarVAMP SADDLE algorithm
- **Olivar** (.csv): Row-based amplicon format with forward/reverse primer pairs
- **FASTA** (.fasta): Multi-FASTA primer sequences with metadata
- **STS** (.sts.tsv): Simple primer validation format

**Ecosystem Integration:**
- **PrimerSchemes Labs**: Validated with official repository schemes (Yale TB, Yale WNV, VarVAMP HAV)
- **Primal-page**: Full info.json schema compliance with MD5 validation
- **Topology Awareness**: Automatic detection and handling of circular genomes (mitochondrial, plasmids)
- **Real-world Testing**: Verified with ARTIC nCoV-2019 V5.3.2, Olivar mitochondrial designs

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
- **Performance**: Sub-second processing for 500+ amplicons, validated with 2,500+ amplicon schemes
- **Security**: All file operations use path validation and input sanitization
- **Genome Types**: Linear and circular genome topology with automatic detection
- **Coordinate Systems**: Handles 0-based BED and 1-based coordinate systems with proper conversion
- **Standards Compliance**: Follows primal-page specifications and articbedversion standards

### Topology Detection and Circular Genome Support

```python
from preprimer.core.topology import TopologyDetector, GenomeTopology

# Automatic topology detection
detector = TopologyDetector()
topology = detector.detect_topology(amplicons, reference_length=16569)

# Topology-aware amplicon length calculation
if topology == GenomeTopology.CIRCULAR:
    length = detector.calculate_amplicon_length(start, end, reference_length, is_circular=True)
```

**Topology Features:**
- Automatic detection of linear vs. circular genome architecture
- Coordinate wrapping support for circular genomes (mitochondria, plasmids, viral episomes)
- Topology-aware amplicon length calculation with multiple detection methods
- Cross-origin amplicon handling (e.g., start=16400, end=200 in 16569bp genome)
- Integration with all parsers through standardized base class

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

### Primal-page Integration and Metadata Support

```python
from preprimer.core.primerscheme_info import PrimerschemeInfo, generate_info_json

# Create official info.json metadata
info = generate_info_json(
    schemename="my-scheme",
    schemeversion="v1.0.0", 
    ampliconsize=400,
    species="SARS-CoV-2",
    primer_bed_path="primer.bed",
    reference_fasta_path="reference.fasta"
)
info.save("info.json")
```

**Metadata Features:**
- Full primal-page info.json schema implementation with validation
- MD5 hash generation and verification for scheme integrity
- articbedversion compatibility (v2.0, v3.0) with format-specific features
- JSON configuration parsing for Olivar and other tools
- Official primerscheme directory structure generation (primer.bed + reference.fasta + info.json)

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
- Maintain exceptional test coverage (currently 581 tests with 96.90% coverage)
- **Completed**: Comprehensive security hardening with 100% security module coverage
- **Completed**: Main API entry point testing achieving 100% coverage
- **Completed**: Core infrastructure testing (converter, registry, exceptions) with 95-100% coverage
- Performance monitoring with large-scale datasets (validated up to 2,500+ amplicons)
- Documentation maintenance following comprehensive testing improvements

**Medium-term (v0.3.x):**
- Windows support investigation (Unicode encoding challenges)
- Additional format support for emerging primer design tools
- Web API/service implementation for remote conversion
- Enhanced biological constraint validation (Tm, GC content, primer-dimer analysis)
- Advanced circular genome coordinate algorithms for complex topologies

**Long-term:**
- Integration with popular sequencing pipelines (Nextflow, Snakemake)
- Real-time format validation and conversion services
- Machine learning-based primer quality assessment
- Support for multi-reference and pan-genome primer schemes

### Key Implementation Notes

**Essential Principles:**
- All format conversions preserve data integrity bidirectionally
- Automatic format detection using content analysis + file extensions
- Topology-aware processing: automatic detection of linear vs. circular genomes
- Coordinate system handling: proper conversion between 0-based BED and 1-based systems
- Standards compliance: follows primal-page specifications and articbedversion standards
- IUPAC degenerate nucleotide support for variant-aware primer designs
- Security-first approach: all file operations use validation utilities
- Plugin architecture enables custom formats without core changes
- Comprehensive error handling with informative validation messages
- JSON metadata support: Olivar configurations and primal-page info.json schema

**Test Suite Structure:**
```
tests/
├── test_*_comprehensive.py           # Comprehensive coverage test suites (134 tests)
│   ├── test_security_comprehensive.py         # Security validation (38 tests, 100% coverage)
│   ├── test_main_api_comprehensive.py         # Main API entry point (12 tests, 100% coverage)
│   ├── test_converter_comprehensive_gaps.py   # Core converter edge cases (9 tests, 99.34% coverage)
│   ├── test_exceptions_comprehensive.py       # Exception system (25 tests, 95.67% coverage)
│   ├── test_registry_comprehensive.py         # Registry system (16 tests, 96.97% coverage)
│   ├── test_artic_parser_comprehensive.py     # ARTIC parser edge cases (22 tests, 97.22% coverage)
│   └── test_sts_writer_comprehensive.py       # STS writer complete coverage (12 tests, 100% coverage)
├── test_data/                         # Test datasets
│   ├── datasets/                      # Internal test datasets
│   │   ├── small/                     # COVID-19: 5 amplicons (fast testing)
│   │   ├── medium/                    # ASFV: 80 amplicons (performance testing)
│   │   └── mitochondrial/             # Human mito: 8 amplicons (circular genome testing)
│   └── external_schemes/              # Real-world validation schemes
│       ├── yale-tb/                   # Mycobacterium tuberculosis: 2,564 amplicons
│       ├── yale-west-nile-virus/      # West Nile Virus: 38 amplicons
│       ├── varvamp-hav/               # Hepatitis A with degenerate primers
│       ├── nCoV-2019-V532/            # ARTIC SARS-CoV-2 V5.3.2: 96 amplicons
│       └── olivar-mitochondrial/      # Olivar-generated: 15 amplicons
└── [other test categories...]         # 447 additional tests across all other categories
```
Each dataset includes cross-format consistency with realistic biological data. The mitochondrial datasets specifically test circular genome coordinate wrapping, while external schemes validate real-world compatibility with official primer design tools and repositories.

### Quality Standards

- **Test Coverage**: **Achieved 96.90% across 581 comprehensive tests**
  - Security Module: 100% coverage with comprehensive edge case testing
  - Main API: 100% coverage of primary user-facing functions
  - Core Infrastructure: 95-100% coverage (converter 99.34%, registry 96.97%, exceptions 95.67%)
  - Parser/Writer System: 95-100% coverage with comprehensive error path testing
- **Security**: All file operations require security validation (100% security module coverage)
- **Performance**: Document benchmarks for performance-critical paths
- **Documentation**: Keep aligned with actual implementation (recently reorganized)
- **Real-world Validation**: Continuous testing with official schemes from PrimerSchemes Labs repository
- **Standards Compliance**: Adherence to primal-page specifications and ecosystem compatibility

### External Validation and Real-world Testing

**Validated Schemes:**
- **Yale TB**: Mycobacterium tuberculosis whole genome (2,564 amplicons, articbedversion v2.0)
- **Yale WNV**: West Nile Virus complete genome (38 amplicons, articbedversion v3.0) 
- **VarVAMP HAV**: Hepatitis A with degenerate primers (16 IUPAC primers)
- **ARTIC nCoV-2019 V5.3.2**: SARS-CoV-2 reference scheme (96 amplicons)
- **Olivar Mitochondrial**: Human mtDNA circular tiling (15 amplicons, 1200-1500bp)

**Validation Results:**
- Complete round-trip conversion fidelity across all format combinations
- Successful parsing of both Olivar-generated CSV and BED formats
- Proper handling of degenerate nucleotides and complex naming schemes
- Accurate coordinate system conversion and topology detection
- Full compatibility with official tool outputs and repository standards