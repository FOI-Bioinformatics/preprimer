# PrePrimer

**Primer scheme converter for tiled amplicon sequencing supporting linear and circular genomes.**

[![CI Status](https://github.com/FOI-Bioinformatics/preprimer/workflows/CI/badge.svg)](https://github.com/FOI-Bioinformatics/preprimer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FOI-Bioinformatics/preprimer)

PrePrimer converts between primer design formats used in genomic sequencing workflows. Supports VarVAMP, ARTIC, Olivar, and STS formats with full bidirectional conversion.

## What's New in v0.2.0

- **Primer-to-Reference Alignment**: Integrated BLAST, Exonerate, merPCR, and me-PCR providers
- **Enhanced STS Format**: Auto-detection of 3/4-column formats, header/headerless files
- **Comprehensive Validation**: 23 real-data tests with 100% pass rate, 611 total tests
- **Improved Documentation**: Reorganized structure with technical validation reports

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## Features

- **🔄 Multi-format Support**: 4 input formats × 5 output formats = 20 conversion pathways
- **🌍 Topology-Aware**: Automatic detection of circular genomes (mitochondrial, plasmids)
- **✅ Standards Compliant**: Full primal-page specifications and articbedversion compatibility
- **🧬 IUPAC Support**: Degenerate nucleotide codes for variant-aware designs
- **🔒 Security Hardened**: Input validation, path sanitization, secure file operations
- **⚡ Performance**: Sub-second processing for 500+ amplicons
- **📊 Well-Tested**: 611 tests with 96.90% coverage

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install
pip install -e .

# Verify
preprimer --version
```

**Requirements:** Python 3.11+ on Linux or macOS

### Basic Usage

```bash
# List supported formats
preprimer list

# Get file information
preprimer info primers.tsv

# Convert VarVAMP to ARTIC
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic

# Convert to multiple formats
preprimer convert --input primers.tsv --output-dir output/ \
                  --output-formats artic fasta sts --prefix MyVirus
```

### Python API

```python
from preprimer.core.converter import Converter

# Simple conversion
converter = Converter()
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic", "fasta"],
    prefix="SARS-CoV-2"
)

print(f"Converted {len(amplicons)} amplicons")
```

## Supported Formats

| Format | Input | Output | Description |
|--------|-------|--------|-------------|
| **VarVAMP** | ✅ `.tsv` | ✅ | 13-column TSV with IUPAC degenerate support |
| **ARTIC** | ✅ `.bed` | ✅ | BED format (v2.0/v3.0) with primal-page compliance |
| **Olivar** | ✅ `.csv` | ✅ | CSV with amplicon metadata and circular genome support |
| **STS** | ✅ `.sts.tsv` | ✅ | 3/4-column TSV for in-silico PCR (auto-detection) |
| **FASTA** | ❌ | ✅ | Multi-FASTA sequences with metadata headers |

**Full bidirectional conversion** between all readable formats. See [format details](docs/user-guide/supported-formats.md).

## Common Use Cases

```bash
# Design with VarVAMP, use with ARTIC pipeline
preprimer convert --input varvamp_output.tsv --output-formats artic --prefix SARS-CoV-2

# Multi-format output for cross-platform compatibility
preprimer convert --input primers.bed --output-formats artic fasta sts varvamp --prefix MyVirus

# STS format for in-silico PCR validation
preprimer convert --input primers.tsv --output-formats sts --prefix validation
```

## Documentation

📚 **Complete documentation in [`docs/`](docs/)**

**Getting Started**: [Installation](docs/user-guide/installation.md) · [Quick Start](docs/user-guide/quick-start.md) · [Basic Usage](docs/user-guide/basic-usage.md) · [CLI Reference](docs/user-guide/cli-reference.md)

**User Guides**: [Supported Formats](docs/user-guide/supported-formats.md) · [Configuration](docs/user-guide/configuration.md) · [Python API](docs/api/python-api.md)

**Developer**: [Architecture](docs/developer/architecture.md) · [Adding Parsers](docs/developer/adding-parsers.md) · [Contributing](docs/developer/contributing.md)

**Examples**: See [`examples/`](examples/) for 5 runnable examples (basic conversion, batch processing, topology handling, quality filtering, error handling)

## Platform Support

**Supported**: Linux and macOS with Python 3.11+
**Windows**: Not supported (use WSL2) - [See compatibility details](docs/technical/windows-compatibility.md)

## For Developers

**Technical Documentation**:
- [Architecture Overview](docs/developer/architecture.md) - Plugin-based design, registry system
- [Testing Guide](docs/technical/testing.md) - 611 tests, 96.90% coverage
- [Validation Reports](docs/technical/validation/) - Real data testing, v0.2.0 validation
- [CLAUDE.md](CLAUDE.md) - Technical guide for Claude Code and AI-assisted development

**Contributing**:
- [Contributing Guide](docs/developer/contributing.md) - Setup, code style, workflow
- [Adding Parsers](docs/developer/adding-parsers.md) - Extend with new formats
- [Security Policy](SECURITY.md) - Security hardening, path validation, best practices

## Citation

If you use PrePrimer in your research, please cite:

```bibtex
@software{preprimer2024,
  title = {PrePrimer: Primer Scheme Converter for Tiled Amplicon Sequencing},
  author = {Sjödin, Andreas},
  year = {2024},
  version = {0.2.0},
  url = {https://github.com/FOI-Bioinformatics/preprimer}
}
```

See [CITATION.cff](CITATION.cff) for complete metadata.

## License

[MIT License](LICENSE) - See LICENSE file for details.

## Acknowledgments

Built with [VarVAMP](https://github.com/jonas-fuchs/varVAMP), [ARTIC Network](https://github.com/artic-network), [Olivar](https://github.com/treangenlab/Olivar), [Primal-page](https://github.com/artic-network/primal-page), and [PrimerSchemes Labs](https://labs.primalscheme.com/) specifications.

## Links

[Repository](https://github.com/FOI-Bioinformatics/preprimer) · [Documentation](docs/) · [Issues](https://github.com/FOI-Bioinformatics/preprimer/issues) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

---

**Maintained by:** Swedish Defence Research Agency (FOI) Bioinformatics

**Version:** 0.2.0 | **Python:** 3.11+ | **Platforms:** Linux, macOS
