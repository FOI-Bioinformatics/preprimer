# PrePrimer

A modern, extensible primer scheme converter for tiled amplicon sequencing applications.

PrePrimer facilitates interconversion between primer scheme formats commonly used in viral genome sequencing workflows, including VarVAMP, ARTIC, and Olivar formats through a plugin-based architecture.

## Version 0.2.0 Features

- **Modular Architecture**: Plugin-based parser and writer system enabling extensibility
- **Multi-format Support**: Bidirectional conversion between VarVAMP, ARTIC, and Olivar formats
- **Security Implementation**: Input validation, path sanitization, and secure file operations
- **Command-line Interface**: Intuitive commands with automatic format detection
- **Comprehensive Testing**: 226 tests across multiple methodologies including property-based testing
- **Performance Optimization**: Efficient processing of large primer datasets
- **Configuration Management**: Flexible configuration system with environment variable support

## Supported Formats

### Input Formats
- **VarVAMP** (`.tsv`, `.txt`) - Tiled primer schemes from varVAMP primer design tool
- **ARTIC** (`.bed`, `.scheme.bed`) - ARTIC primer scheme BED format for tiled amplicon sequencing
- **Olivar** (`.csv`) - Olivar primer design output format

### Output Formats  
- **ARTIC** (`.scheme.bed`) - Compatible with ARTIC minion workflows
- **FASTA** (`.fasta`) - Multi-FASTA format for primer sequences
- **STS** (`.sts.tsv`) - Sequence Tagged Site format for in-silico PCR validation
- **VarVAMP** (`.tsv`) - VarVAMP-compatible primer scheme format
- **Olivar** (`.csv`) - Olivar primer design format

The software supports bidirectional conversion between all implemented formats, maintaining data integrity and biological relevance throughout the conversion process.

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

- Efficient processing capabilities for datasets containing up to 500 amplicons
- Linear computational complexity O(n) scaling with dataset size
- Memory utilization: approximately 50MB baseline, scaling to ~200MB for large datasets
- Performance optimization through benchmarked parser implementations

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
├── core/                    # Core abstractions and interfaces
│   ├── interfaces.py        # Abstract base classes
│   ├── config.py           # Configuration management  
│   ├── converter.py        # Main conversion logic
│   ├── registry.py         # Plugin registration system
│   └── exceptions.py       # Custom exceptions
├── parsers/                 # Input format parsers
│   ├── varvamp_parser.py   # VarVAMP format
│   ├── artic_parser.py     # ARTIC BED format
│   └── olivar_parser.py    # Olivar CSV format
├── writers/                 # Output format writers  
│   ├── artic_writer.py     # ARTIC BED output
│   ├── fasta_writer.py     # FASTA output
│   └── sts_writer.py       # STS output for me-pcr
└── cli.py                  # Modern command-line interface
```

### **Key Features**

- **🔌 Plugin Architecture**: Easy to add new parsers and writers
- **🛡️ Robust Validation**: Comprehensive error handling and data validation  
- **⚙️ Flexible Configuration**: JSON-based configuration system
- **🔍 Auto-detection**: Automatic format detection based on content
- **📊 Data Structures**: Standardized primer and amplicon data models
- **🧪 Extensible**: Clean interfaces for adding new functionality

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

- Original PrePrimer codebase
- [VarVAMP](https://github.com/jonas-fuchs/varVAMP) primer design tool
- [ARTIC](https://github.com/artic-network/artic-tools) tiled amplicon sequencing  
- [Olivar](https://github.com/treangenlab/Olivar) variant-aware primer design
- Contributors and users of the bioinformatics community

---

**PrePrimer 0.2.0 - Modern primer scheme conversion made easy! 🧬✨**
