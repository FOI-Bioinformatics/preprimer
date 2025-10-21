# PrePrimer User Guide

Complete documentation for PrePrimer users, from installation to advanced workflows.

## Getting Started

### New to PrePrimer?
1. **[Installation Guide](installation.md)** - Install PrePrimer on your system
2. **[Quick Start](quick-start.md)** - Convert your first primer scheme in 5 minutes  
3. **[Basic Usage](basic-usage.md)** - Essential commands and workflows

### Documentation
- **[CLI Reference](cli-reference.md)** - Complete command-line interface documentation
- **[Configuration](configuration.md)** - Customizing PrePrimer behavior
- **[Supported Formats](supported-formats.md)** - Input and output format specifications

## Common Tasks

### Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| **Convert VarVAMP to ARTIC** | `preprimer convert --input primers.tsv --output-formats artic` | Standard workflow |
| **Show file information** | `preprimer info primers.csv` | Format detection and validation |
| **Multiple output formats** | `preprimer convert --output-formats artic fasta sts` | Generate multiple formats |
| **Custom configuration** | `preprimer convert --config config.json` | Use custom settings |

### Typical Workflows

#### Viral Genome Sequencing
```bash
# Convert VarVAMP primers for ARTIC workflow
preprimer convert --input varvamp_primers.tsv \
                 --output-dir artic_schemes/ \
                 --output-formats artic \
                 --prefix SARS_CoV_2

# Use with ARTIC pipeline
artic minion SARS_CoV_2 data/ --scheme-directory artic_schemes/artic/
```

#### Cross-Platform Compatibility
```bash
# Convert Olivar design to multiple formats
preprimer convert --input olivar-design.csv \
                 --output-dir multi_format/ \
                 --output-formats artic fasta sts \
                 --prefix Influenza
```

#### Quality Control Pipeline
```bash
# Validate primer schemes
for file in *.tsv *.csv *.bed; do
    preprimer info "$file"
done

# Convert with validation
preprimer convert --input primers.tsv \
                 --output-dir output/ \
                 --output-formats artic
```

## Additional Resources

For technical implementation details, see the [Technical Documentation](../technical/).

For development and contribution information, see the [Developer Documentation](../developer/).

For the complete documentation index, see the [main README](../README.md).

---

**Ready to get started? Begin with the [Installation Guide](installation.md)!**