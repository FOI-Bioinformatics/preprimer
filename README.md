# PrePrimer

A comprehensive, extensible primer scheme converter for tiled amplicon sequencing applications with support for linear and circular genome architectures.

PrePrimer enables seamless interconversion between primer scheme formats used in genomic sequencing workflows, including VarVAMP, ARTIC, and Olivar formats. The software incorporates topology-aware processing for both linear and circular genomes, ensuring accurate coordinate handling for diverse biological targets including viral, bacterial, and organellar genomes.

## Version 0.2.0 Features

- **Topology-aware Processing**: Automatic detection and handling of linear and circular genome architectures
- **Ecosystem Integration**: Full compatibility with official primer design tools and repository standards
- **Multi-format Support**: Bidirectional conversion between VarVAMP, ARTIC, and Olivar formats
- **Standards Compliance**: adherence to primal-page specifications and articbedversion compatibility (v2.0, v3.0)
- **Degenerate Primer Support**: Complete IUPAC nucleotide code handling for variant-aware designs
- **Modular Architecture**: Plugin-based parser and writer system enabling extensibility
- **Security Implementation**: Comprehensive input validation, path sanitization, and secure file operations
- **Real-world Validation**: Tested with official schemes from PrimerSchemes Labs repository
- **Command-line Interface**: Intuitive commands with automatic format detection and validation
- **Comprehensive Testing**: 250+ tests including external validation and property-based testing
- **Performance Optimization**: Efficient processing validated with datasets up to 2,500+ amplicons

## Supported Formats

### Input Formats
- **VarVAMP** (`.tsv`) - Complete 13-column specification with IUPAC degenerate nucleotide support
- **ARTIC** (`.bed`) - Compatible with articbedversion v2.0 and v3.0 following primal-page specifications  
- **Olivar** (`.csv`) - Native Olivar-generated CSV format with comprehensive amplicon metadata
- **STS** (`.sts.tsv`) - Simple primer format for basic conversion workflows

### Output Formats  
- **ARTIC** (`.bed`) - Official primerscheme structure (primer.bed + reference.fasta + info.json)
- **VarVAMP** (`.tsv`) - Complete 13-column format compatible with VarVAMP SADDLE algorithm
- **Olivar** (`.csv`) - Row-based amplicon format with forward/reverse primer pairs
- **FASTA** (`.fasta`) - Multi-FASTA primer sequences with standardized headers
- **STS** (`.sts.tsv`) - Simple primer validation format for in-silico PCR tools

### Ecosystem Compatibility
- **PrimerSchemes Labs**: Validated compatibility with official repository schemes
- **Topology Support**: Automatic handling of circular genomes (mitochondria, plasmids, viral episomes)
- **Standards Compliance**: Full adherence to primal-page specifications and ecosystem standards
- **Coordinate Systems**: Proper conversion between 0-based BED and 1-based coordinate systems

The software maintains complete bidirectional conversion fidelity across all implemented formats, preserving data integrity and biological accuracy throughout the conversion process.

## Installation

PrePrimer requires Python 3.8 or later and is supported on **Linux** and **macOS** only.

> ⚠️ **Note**: Windows is not currently supported due to Unicode character encoding limitations.

```bash
# Clone the repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install the package
pip install -e .

# For development (includes testing framework)
pip install -e ".[dev]"

# Verify installation with test suite
python -m pytest
```

### Security Implementation

PrePrimer incorporates security measures for safe file processing:
- Path validation to prevent directory traversal vulnerabilities
- Input sanitization with configurable file size limitations  
- Secure file operations with automatic resource cleanup
- Comprehensive logging for security event monitoring

### Performance Characteristics

- Validated processing capabilities for datasets up to 2,500+ amplicons (Yale TB whole genome)
- Linear computational complexity O(n) scaling with dataset size  
- Memory utilization: approximately 50MB baseline, scaling efficiently for large datasets
- Sub-second processing for typical viral genome schemes (≤500 amplicons)
- Topology detection and coordinate conversion with minimal computational overhead

## Quick Start

```bash
# List supported formats
preprimer list

# Get info about a file
preprimer info your_primers.tsv

# Convert VarVAMP to ARTIC format
preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic

# Convert to multiple formats (including bidirectional)
preprimer convert --input primers.tsv --output-dir schemes/ \
                 --output-formats artic fasta sts varvamp olivar --prefix MyVirus
```

## Documentation

Complete documentation is available in the [`docs/`](docs/) directory:

### Getting Started
- **[Quick Start Guide](docs/user-guide/quick-start.md)** - Basic usage and first conversion
- **[Installation Guide](docs/user-guide/installation.md)** - Installation instructions and requirements
- **[Basic Usage](docs/user-guide/basic-usage.md)** - Core commands and workflows

### User Guides
- **[CLI Reference](docs/user-guide/cli-reference.md)** - Command-line interface documentation
- **[Configuration Guide](docs/user-guide/configuration.md)** - Configuration options and customization
- **[Supported Formats](docs/user-guide/supported-formats.md)** - Input and output format specifications
- **[Security Guide](docs/SECURITY.md)** - Security features and best practices
- **[Testing Guide](docs/TESTING.md)** - Testing framework and validation approaches

### Developer Documentation
- **[Python API Guide](docs/api/python-api.md)** - Programmatic interface usage
- **[Architecture Overview](docs/developer/architecture.md)** - System design and components
- **[Adding Parsers](docs/developer/adding-parsers.md)** - Extending format support
- **[Contributing Guide](docs/developer/contributing.md)** - Development guidelines and procedures

### Examples and Use Cases
- **[Use Cases](docs/tutorials/use-cases.md)** - Practical applications in research workflows
- **[Format Conversion Examples](docs/tutorials/format-conversion.md)** - Conversion procedures and examples
- **[Integration Examples](docs/tutorials/integration.md)** - Integration with bioinformatics pipelines

**Quick Reference:**
```bash
# Get help
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

## 🧬 **Use Cases**

### **Viral Genome Sequencing Workflows**

**1. VarVAMP → ARTIC Pipeline:**
```bash
# Design primers with VarVAMP
# Then convert to ARTIC format
preprimer convert --input varvamp_output.tsv --output-dir schemes/ --output-formats artic --prefix MPXV

# Use with ARTIC workflow
artic minion MPXV nanopore_data/ --scheme-directory schemes/artic/
```

**2. Cross-platform Compatibility:**
```bash  
# Convert Olivar design to all formats (full bidirectional support)
preprimer convert --input olivar-design.csv \
                 --output-dir multi_format/ \
                 --output-formats artic fasta sts varvamp olivar \
                 --prefix MultiVirus

# Or convert ARTIC to VarVAMP and Olivar
preprimer convert --input existing.scheme.bed \
                 --output-dir converted/ \
                 --output-formats varvamp olivar \
                 --prefix ARTIC_Converted
```

**3. Primer Validation:**
```bash
# Validate primer design files
preprimer info suspicious_primers.tsv
preprimer convert --input primers.tsv --output-dir /tmp --validate-only
```

## 🏗️ **Architecture**

PrePrimer 0.2.0 features a completely refactored, extensible architecture:

```
preprimer/
├── core/                          # Framework and abstractions
│   ├── interfaces.py              # Abstract base classes (PrimerData, AmpliconData)
│   ├── converter.py               # Main conversion orchestration
│   ├── registry.py                # Plugin auto-registration system
│   ├── topology.py                # Genome topology detection and circular coordinate handling
│   ├── standardized_parser.py     # Base parser with topology integration
│   ├── primerscheme_info.py       # Primal-page info.json schema implementation
│   └── security.py                # Input validation and path sanitization
├── parsers/                       # Input format handlers
│   ├── varvamp_parser.py          # VarVAMP TSV format with IUPAC degenerate support
│   ├── artic_parser.py            # ARTIC BED format (v2.0/v3.0 articbedversion)
│   ├── olivar_parser.py           # Olivar CSV format with enhanced validation
│   └── sts_parser.py              # STS TSV format
├── writers/                       # Output format generators
│   ├── artic_writer.py            # Official primerscheme structure (primer.bed + info.json)
│   ├── varvamp_writer.py          # VarVAMP TSV format (full column specification)
│   ├── olivar_writer.py           # Olivar CSV format
│   ├── fasta_writer.py            # Multi-FASTA sequences
│   └── sts_writer.py              # STS validation files
└── cli.py                         # Modern command-line interface
```

### **Key Features**

- **🧬 Topology-aware**: Automatic detection and handling of circular genome architectures
- **🔌 Plugin Architecture**: Extensible parser and writer system with auto-registration
- **🛡️ Standards Compliance**: Full adherence to primal-page specifications and ecosystem standards
- **🧪 IUPAC Support**: Complete degenerate nucleotide handling for variant-aware primer designs
- **🔍 Auto-detection**: Intelligent format detection based on content analysis and metadata
- **📊 Data Integrity**: Standardized data models preserving biological accuracy across conversions
- **⚙️ Flexible Configuration**: JSON-based configuration with primal-page info.json support
- **🔐 Security-first**: Comprehensive input validation and secure file operations

## 🤝 **Contributing**

We welcome contributions! PrePrimer is designed to be easily extensible.

### **Adding New Formats**

1. **Create a Parser** (for input formats):
   ```python
   class MyParser(PrimerParser):
       # Implement required methods
   ```

2. **Create a Writer** (for output formats):  
   ```python
   class MyWriter(OutputWriter):
       # Implement required methods
   ```

3. **Register Your Components**:
   ```python
   from preprimer.core.registry import parser_registry, writer_registry
   parser_registry.register(MyParser)
   writer_registry.register(MyWriter)
   ```

### **Development Setup**
```bash
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run specific tests
python -m pytest tests/test_refactored_system.py -v
```

## 📄 **License**

PrePrimer is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Original PrePrimer codebase foundation
- [VarVAMP](https://github.com/jonas-fuchs/varVAMP) - SADDLE algorithm for variant-aware primer design
- [ARTIC Network](https://github.com/artic-network) - Tiled amplicon sequencing protocols and tools
- [Olivar](https://github.com/treangenlab/Olivar) - Advanced variant-aware primer design platform
- [Primal-page](https://github.com/artic-network/primal-page) - Primer scheme metadata standards
- [PrimerSchemes Labs](https://labs.primalscheme.com/) - Official primer scheme repository
- Yale Grubaugh Laboratory - Real-world validation schemes (TB, West Nile Virus)
- Contributors and users of the computational biology community

---

**PrePrimer 0.2.0 - Modern primer scheme conversion made easy! 🧬✨**
