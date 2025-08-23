# 👥 PrePrimer User Guide

Complete documentation for PrePrimer users, from installation to advanced workflows.

## 🚀 **Getting Started**

### **New to PrePrimer?**
1. **[Installation Guide](installation.md)** - Install PrePrimer on your system
2. **[Quick Start](quick-start.md)** - Convert your first primer scheme in 5 minutes
3. **[Basic Usage](basic-usage.md)** - Essential commands and workflows

### **Core Concepts**
- **[Supported Formats](supported-formats.md)** - Input and output format overview
- **[Configuration](configuration.md)** - Customizing PrePrimer behavior
- **[Validation](validation.md)** - Quality control and primer validation

## 📖 **User Documentation**

### **Interface Guides**
- **[CLI Reference](cli-reference.md)** - Complete command-line interface guide
- **[Python API Basics](python-api-basics.md)** - Using PrePrimer in Python scripts
- **[Configuration Files](configuration-files.md)** - JSON configuration and settings

### **Format Documentation**
- **[VarVAMP Format](formats/varvamp.md)** - VarVAMP primer scheme format
- **[ARTIC Format](formats/artic.md)** - ARTIC BED format specification
- **[Olivar Format](formats/olivar.md)** - Olivar primer design format
- **[Output Formats](formats/output-formats.md)** - ARTIC, FASTA, and STS outputs

### **Workflows & Use Cases**
- **[Format Conversion](workflows/format-conversion.md)** - Converting between formats
- **[Quality Control](workflows/quality-control.md)** - Validating primer schemes
- **[Batch Processing](workflows/batch-processing.md)** - Processing multiple files
- **[Integration](workflows/integration.md)** - Using with other bioinformatics tools

## 🎯 **Common Tasks**

### **Quick Reference**

| Task | Command | Documentation |
|------|---------|---------------|
| **Convert VarVAMP to ARTIC** | `preprimer convert --input primers.tsv --output-formats artic` | [Guide](workflows/varvamp-to-artic.md) |
| **Validate primer file** | `preprimer info primers.csv` | [Guide](workflows/validation.md) |
| **Multiple output formats** | `preprimer convert --output-formats artic fasta sts` | [Guide](workflows/multi-format.md) |
| **Custom configuration** | `preprimer convert --config my-config.json` | [Guide](configuration.md) |

### **Typical Workflows**

#### **1. Viral Genome Sequencing**
```bash
# Convert VarVAMP primers for ARTIC workflow
preprimer convert --input varvamp_primers.tsv \
                 --output-dir artic_schemes/ \
                 --output-formats artic \
                 --prefix SARS_CoV_2

# Use with ARTIC
artic minion SARS_CoV_2 data/ --scheme-directory artic_schemes/artic/
```

#### **2. Cross-Platform Compatibility**
```bash
# Convert Olivar design to multiple formats
preprimer convert --input olivar-design.csv \
                 --output-dir multi_format/ \
                 --output-formats artic fasta sts \
                 --prefix Influenza
```

#### **3. Quality Control Pipeline**
```bash
# Validate primer schemes
for file in *.tsv *.csv *.bed; do
    preprimer info "$file"
done

# Convert with validation
preprimer convert --input primers.tsv \
                 --output-dir validated/ \
                 --validate-only
```

## ⚙️ **Advanced Features**

### **Configuration**
- **[JSON Configuration](configuration-files.md)** - Advanced settings and customization
- **[Environment Variables](environment-variables.md)** - System-wide configuration
- **[Preset Configurations](preset-configurations.md)** - Ready-made settings for common use cases

### **Customization**
- **[Custom Naming](custom-naming.md)** - Primer and amplicon naming schemes
- **[Output Filtering](output-filtering.md)** - Selecting specific primers or amplicons
- **[Quality Thresholds](quality-thresholds.md)** - Setting validation criteria

### **Integration**
- **[Workflow Integration](integration/README.md)** - Using PrePrimer in pipelines
- **[Nextflow Integration](integration/nextflow.md)** - Nextflow pipeline examples
- **[Snakemake Integration](integration/snakemake.md)** - Snakemake workflow examples

## 🔧 **Troubleshooting**

### **Common Issues**
- **[Installation Problems](troubleshooting/installation.md)** - Fixing installation issues
- **[Format Detection](troubleshooting/format-detection.md)** - When auto-detection fails
- **[Conversion Errors](troubleshooting/conversion-errors.md)** - Solving conversion problems
- **[Performance Issues](troubleshooting/performance.md)** - Optimizing for large files

### **Getting Help**
- **[FAQ](faq.md)** - Frequently asked questions
- **[Error Messages](error-messages.md)** - Understanding error messages
- **[Support Resources](support.md)** - Where to get help

## 📊 **Reference Materials**

### **Format Specifications**
- **[VarVAMP TSV Format](formats/varvamp-spec.md)** - Detailed format specification
- **[ARTIC BED Format](formats/artic-spec.md)** - BED format requirements
- **[Olivar CSV Format](formats/olivar-spec.md)** - CSV structure and fields

### **Command Reference**
- **[CLI Commands](cli-commands.md)** - All available commands
- **[Options Reference](cli-options.md)** - Command-line options and flags
- **[Exit Codes](exit-codes.md)** - Understanding exit codes

### **Configuration Reference**
- **[Configuration Schema](configuration-schema.md)** - All configuration options
- **[Default Values](default-values.md)** - Default configuration settings
- **[Validation Rules](validation-rules.md)** - Built-in validation criteria

## 🎓 **Learning Resources**

### **Step-by-Step Tutorials**
- **[Your First Conversion](tutorials/first-conversion.md)** - Beginner tutorial
- **[Working with Multiple Formats](tutorials/multiple-formats.md)** - Intermediate tutorial
- **[Advanced Workflows](tutorials/advanced-workflows.md)** - Expert-level usage

### **Best Practices**
- **[Primer Design Guidelines](best-practices/primer-design.md)** - Scientific best practices
- **[File Organization](best-practices/file-organization.md)** - Managing primer schemes
- **[Quality Control](best-practices/quality-control.md)** - Validation workflows

### **Real-World Examples**
- **[COVID-19 Primer Schemes](examples/covid19.md)** - SARS-CoV-2 workflows
- **[Influenza Surveillance](examples/influenza.md)** - Flu genome sequencing
- **[Custom Virus Studies](examples/custom-virus.md)** - Adapting for new viruses

---

## 📈 **User Guide Statistics**

- **📝 Pages**: 50+ comprehensive user guides
- **💡 Examples**: 100+ working examples
- **🎯 Workflows**: 15+ documented workflows
- **🔧 Troubleshooting**: Complete problem-solving guides
- **📚 Tutorials**: Progressive learning materials

---

**Need something specific? Check the [main documentation index](../README.md) or use the search functionality to find exactly what you need! 📚✨**