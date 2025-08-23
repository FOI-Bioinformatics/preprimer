# PrePrimer

**Modern, extensible primer scheme converter for tiled amplicon sequencing.**

PrePrimer converts between different primer scheme formats used in viral genome sequencing workflows. It supports VarVAMP, ARTIC, and Olivar formats with an extensible plugin-based architecture.

## ✨ **Version 0.2.0 - Complete Refactor**

- 🏗️ **Modern Architecture**: Plugin-based parser and writer system
- 🔧 **Extensible Design**: Easy to add new formats and tools  
- 🎯 **Multi-format Support**: VarVAMP, ARTIC, Olivar, and more
- 🛡️ **Robust Validation**: Comprehensive error handling and validation
- 🚀 **Enhanced CLI**: Intuitive commands with auto-detection
- 🧪 **Well-tested**: Comprehensive test suite with modern Python patterns

## 🎯 **Supported Formats**

### **Input Formats**
- **VarVAMP** (`.tsv`, `.txt`) - Tiled primer schemes from varVAMP
- **ARTIC** (`.bed`, `.scheme.bed`) - ARTIC primer scheme BED format
- **Olivar** (`.csv`) - Olivar primer design output

### **Output Formats**  
- **ARTIC** (`.scheme.bed`) - Ready for `artic minion` workflows
- **FASTA** (`.fasta`) - All primers in multi-FASTA format
- **STS** (`.sts.tsv`) - For me-pcr in-silico validation
- **VarVAMP** (`.tsv`) - VarVAMP-compatible primer schemes  
- **Olivar** (`.csv`) - Olivar primer design format

**🔄 Complete bidirectional conversion between all formats!**

## Installation

PrePrimer requires Python 3.8 or later.

```bash
# Clone the repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"
```

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

## 📚 **Documentation**

**Complete documentation is available in the [`docs/`](docs/) directory:**

### **🚀 Getting Started**
- **[Quick Start Guide](docs/user-guide/quick-start.md)** - Get up and running in 5 minutes
- **[Installation Guide](docs/user-guide/installation.md)** - Detailed installation instructions
- **[Basic Usage](docs/user-guide/basic-usage.md)** - Essential commands and workflows

### **📖 User Guides**
- **[CLI Reference](docs/user-guide/cli-reference.md)** - Complete command-line documentation
- **[Configuration Guide](docs/user-guide/configuration.md)** - Customize PrePrimer behavior
- **[Supported Formats](docs/user-guide/supported-formats.md)** - All input and output formats
- **[User Guide Index](docs/user-guide/README.md)** - Complete user documentation

### **🐍 For Developers**
- **[Python API Guide](docs/api/python-api.md)** - Programmatic usage
- **[Architecture Overview](docs/developer/architecture.md)** - System design
- **[Adding Parsers](docs/developer/adding-parsers.md)** - Extending PrePrimer
- **[Contributing Guide](docs/developer/contributing.md)** - Development guidelines

### **🎯 Examples & Tutorials**
- **[Use Cases](docs/tutorials/use-cases.md)** - Real-world workflows
- **[Format Conversion](docs/tutorials/format-conversion.md)** - Converting between formats
- **[Integration Examples](docs/tutorials/integration.md)** - Using with other tools

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
