# 📚 PrePrimer Documentation

Welcome to the comprehensive documentation for **PrePrimer** - the modern, extensible primer scheme converter for tiled amplicon sequencing.

## 🎯 **Quick Navigation**

### **👥 For Users**
- **[Quick Start Guide](user-guide/quick-start.md)** - Get up and running in 5 minutes
- **[Installation Guide](user-guide/installation.md)** - Detailed installation instructions
- **[User Guide](user-guide/README.md)** - Complete user documentation
- **[Format Support](user-guide/supported-formats.md)** - All supported input/output formats
- **[CLI Reference](user-guide/cli-reference.md)** - Command-line interface guide
- **[Configuration Guide](user-guide/configuration.md)** - Customizing PrePrimer behavior

### **🔬 For Researchers**
- **[Use Cases](tutorials/use-cases.md)** - Real-world viral genomics workflows
- **[Format Conversion Guide](tutorials/format-conversion.md)** - Converting between primer formats
- **[Primer Validation](tutorials/primer-validation.md)** - Quality control and validation
- **[Integration Workflows](tutorials/integration.md)** - Using PrePrimer with other tools

### **🐍 For Developers**
- **[Python API Guide](api/python-api.md)** - Programmatic access to PrePrimer
- **[Architecture Overview](developer/architecture.md)** - System design and components
- **[Adding New Parsers](developer/adding-parsers.md)** - Extending PrePrimer
- **[Contributing Guide](developer/contributing.md)** - Development guidelines
- **[Testing Guide](developer/testing.md)** - Test suite and validation

### **💡 Examples & Tutorials**
- **[Tutorial Collection](tutorials/README.md)** - Step-by-step tutorials
- **[Code Examples](examples/README.md)** - Ready-to-use examples
- **[Sample Data](examples/sample-data.md)** - Test data and datasets

## 📖 **Documentation Overview**

### **Getting Started**
New to PrePrimer? Start here:

1. **[Installation](user-guide/installation.md)** - Install PrePrimer on your system
2. **[Quick Start](user-guide/quick-start.md)** - Your first primer conversion
3. **[Basic Usage](user-guide/basic-usage.md)** - Essential commands and workflows

### **Core Features**
- **Multi-format Support**: Convert between VarVAMP, ARTIC, and Olivar formats
- **Quality Validation**: Comprehensive primer and amplicon validation
- **CLI & API**: Both command-line and Python interfaces
- **Extensible Design**: Easy to add new formats and tools

### **Supported Workflows**

| Workflow | Input | Output | Documentation |
|----------|-------|--------|---------------|
| **VarVAMP → ARTIC** | `.tsv` | `.scheme.bed` | [Guide](tutorials/varvamp-to-artic.md) |
| **Olivar → ARTIC** | `.csv` | `.scheme.bed` | [Guide](tutorials/olivar-to-artic.md) |
| **Cross-Platform** | Multiple | Multiple | [Guide](tutorials/cross-platform.md) |
| **Quality Control** | Any | Validation | [Guide](tutorials/validation.md) |

## 🔧 **Technical Documentation**

### **Architecture**
- **[System Overview](developer/architecture.md)** - High-level design
- **[Plugin System](developer/plugin-system.md)** - Parser and writer architecture
- **[Data Models](developer/data-models.md)** - Core data structures
- **[Configuration System](developer/configuration-system.md)** - Settings and customization

### **API Reference**
- **[Python API](api/python-api.md)** - Complete API documentation
- **[CLI Reference](api/cli-reference.md)** - Command-line interface
- **[Configuration Schema](api/configuration-schema.md)** - Configuration options
- **[Error Handling](api/error-handling.md)** - Exception types and handling

### **Development**
- **[Development Setup](developer/development-setup.md)** - Environment configuration
- **[Code Style Guide](developer/code-style.md)** - Coding standards
- **[Testing Guidelines](developer/testing-guidelines.md)** - Test writing and execution
- **[Release Process](developer/release-process.md)** - Version management

## 🧬 **Format Documentation**

### **Input Formats**

#### **VarVAMP Format**
- **Extension**: `.tsv`, `.txt`
- **Description**: Tiled primer schemes from varVAMP tool
- **[Format Specification](user-guide/formats/varvamp.md)**
- **[Example Data](examples/varvamp-examples.md)**

#### **ARTIC Format**
- **Extension**: `.bed`, `.scheme.bed`
- **Description**: ARTIC primer scheme BED format
- **[Format Specification](user-guide/formats/artic.md)**
- **[Example Data](examples/artic-examples.md)**

#### **Olivar Format**
- **Extension**: `.csv`
- **Description**: Olivar primer design output
- **[Format Specification](user-guide/formats/olivar.md)**
- **[Example Data](examples/olivar-examples.md)**

### **Output Formats**

#### **ARTIC BED Format**
- **Extension**: `.scheme.bed`
- **Use Case**: Ready for `artic minion` workflows
- **[Specification](user-guide/formats/artic-output.md)**

#### **FASTA Format**
- **Extension**: `.fasta`
- **Use Case**: Multi-FASTA with detailed headers
- **[Specification](user-guide/formats/fasta-output.md)**

#### **STS Format**
- **Extension**: `.sts.tsv`
- **Use Case**: For me-pcr in-silico validation
- **[Specification](user-guide/formats/sts-output.md)**

## 🚀 **Quick Examples**

### **Command Line**
```bash
# Auto-detect format and convert
preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic

# Multiple output formats
preprimer convert --input olivar-design.csv \
                 --output-dir output/ \
                 --output-formats artic fasta sts \
                 --prefix COVID19

# Get file information
preprimer info mysterious_primers.csv
```

### **Python API**
```python
from preprimer import convert_primers

# Simple conversion
output_files = convert_primers(
    input_file="primers.tsv",
    output_dir="schemes/",
    output_formats=["artic", "fasta"],
    prefix="MyVirus"
)

# Access results
artic_file = output_files["artic"]
fasta_file = output_files["fasta"]
```

## 📝 **Contributing to Documentation**

Help us improve the documentation:

1. **Report Issues**: Found something unclear? [Open an issue](https://github.com/FOI-Bioinformatics/preprimer/issues)
2. **Suggest Improvements**: Have ideas for better docs? We'd love to hear them
3. **Add Examples**: Share your workflows and use cases
4. **Fix Typos**: Small improvements make a big difference

### **Documentation Standards**
- Use clear, concise language
- Include working code examples
- Add cross-references between related topics
- Keep examples up-to-date with latest version

## 🔗 **External Resources**

### **Related Tools**
- **[VarVAMP](https://github.com/jonas-fuchs/varVAMP)** - Primer design for tiled amplicon sequencing
- **[ARTIC](https://github.com/artic-network/artic-tools)** - Real-time genomic surveillance toolkit
- **[Olivar](https://github.com/treangenlab/Olivar)** - Variant-aware primer design

### **Scientific Background**
- **[Tiled Amplicon Sequencing](tutorials/tiled-sequencing-background.md)** - Scientific background
- **[Primer Design Principles](tutorials/primer-design-principles.md)** - Best practices
- **[Viral Genomics Workflows](tutorials/viral-genomics.md)** - Application context

## 📊 **Documentation Statistics**

- **📄 Pages**: 40+ comprehensive documentation pages
- **💡 Examples**: 20+ working code examples
- **🎯 Tutorials**: 10+ step-by-step guides
- **🔧 References**: Complete API and CLI documentation
- **🧪 Test Coverage**: Documented test procedures and validation

---

## 🆘 **Need Help?**

Can't find what you're looking for?

- **[FAQ](user-guide/faq.md)** - Frequently asked questions
- **[Troubleshooting](user-guide/troubleshooting.md)** - Common issues and solutions
- **[Support](user-guide/support.md)** - How to get help
- **[GitHub Issues](https://github.com/FOI-Bioinformatics/preprimer/issues)** - Report bugs or request features

---

**📚 This documentation is continuously updated to reflect the latest PrePrimer features and best practices. Happy primer converting! 🧬✨**