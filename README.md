# PrePrimer

**Primer scheme converter for tiled amplicon sequencing supporting linear and circular genomes.**

[![CI Status](https://github.com/FOI-Bioinformatics/preprimer/workflows/CI/badge.svg)](https://github.com/FOI-Bioinformatics/preprimer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FOI-Bioinformatics/preprimer)

PrePrimer converts between primer design formats used in genomic sequencing workflows. Supports VarVAMP, ARTIC, Olivar, and STS formats with full bidirectional conversion.

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

### Input Formats (Parsers)

| Format | Extension | Description |
|--------|-----------|-------------|
| **VarVAMP** | `.tsv` | 13-column TSV with IUPAC degenerate support |
| **ARTIC** | `.bed` | BED format (v2.0/v3.0) with primal-page compliance |
| **Olivar** | `.csv` | CSV with amplicon metadata and circular genome support |
| **STS** | `.sts.tsv` | Simple 3-column TSV for in-silico PCR |

### Output Formats (Writers)

| Format | Description |
|--------|-------------|
| **ARTIC** | Official primerscheme structure (primer.bed + reference.fasta + info.json) |
| **VarVAMP** | 13-column TSV compatible with VarVAMP SADDLE algorithm |
| **Olivar** | CSV format with amplicon pairs |
| **FASTA** | Multi-FASTA sequences with metadata headers |
| **STS** | Simple TSV for e-PCR/me-pcr validation |

**Full bidirectional conversion supported between all formats.**

## Use Cases

### Viral Sequencing Workflows

```bash
# Design with VarVAMP, use with ARTIC pipeline
preprimer convert --input varvamp_output.tsv --output-formats artic --prefix SARS-CoV-2
artic minion SARS-CoV-2 nanopore_data/ --scheme-directory output/artic/
```

### Cross-Platform Compatibility

```bash
# Convert Olivar design to all formats
preprimer convert --input olivar-design.csv \
                  --output-dir multi_format/ \
                  --output-formats artic fasta sts varvamp olivar \
                  --prefix MultiVirus
```

### Primer Validation

```bash
# Convert to STS for in-silico PCR validation
preprimer convert --input primers.tsv --output-formats sts --prefix validation
e-PCR -S reference.fasta -N output/sts/validation.sts.tsv
```

## Documentation

📚 **Complete documentation in [`docs/`](docs/)**

### Getting Started
- [Installation Guide](docs/user-guide/installation.md)
- [Quick Start](docs/user-guide/quick-start.md)
- [Basic Usage](docs/user-guide/basic-usage.md)
- [CLI Reference](docs/user-guide/cli-reference.md)

### User Guides
- [Supported Formats](docs/user-guide/supported-formats.md) - Detailed format specifications
- [Configuration Guide](docs/user-guide/configuration.md)
- [Security Guide](docs/SECURITY.md)

### Developer Documentation
- [Python API Guide](docs/api/python-api.md) - Complete API reference
- [Architecture Overview](docs/developer/architecture.md)
- [Adding Parsers](docs/developer/adding-parsers.md)
- [Contributing Guide](docs/developer/contributing.md)
- [Release Checklist](docs/developer/release-checklist.md)

### Examples
- [Examples Directory](examples/) - 5 runnable code examples
- [Basic Conversion](examples/basic_conversion.py)
- [Batch Processing](examples/batch_processing.py)
- [Topology Handling](examples/topology_handling.py)
- [Quality Filtering](examples/quality_filtering.py)
- [Error Handling](examples/error_handling.py)

## Architecture

```
preprimer/
├── core/           # Framework (converter, registry, topology, security)
├── parsers/        # Input format handlers (VarVAMP, ARTIC, Olivar, STS)
└── writers/        # Output format generators (ARTIC, VarVAMP, Olivar, FASTA, STS)
```

**Plugin-based architecture** enables easy extension with custom formats.

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| **Linux** | ✅ Supported | All distributions with Python 3.11+ |
| **macOS** | ✅ Supported | macOS 10.14+ with Python 3.11+ |
| **Windows** | ❌ Not Supported | Use WSL2 - [See details](docs/technical/windows-compatibility.md) |

**Why not Windows?** Unicode console limitations. [Technical explanation →](docs/technical/windows-compatibility.md)

**Windows users:** Use WSL2 for full compatibility.

## Testing

```bash
# Run full test suite (611 tests)
python -m pytest

# Run with coverage
python -m pytest --cov=preprimer --cov-report=html

# Run specific test categories
python -m pytest tests/test_security.py -v
python -m pytest tests/test_topology.py -v
```

**Test Coverage:** 96.90% with comprehensive validation

## Performance

- **Processing Speed**: Sub-second for 500+ amplicons
- **Validated Scale**: Up to 2,564 amplicons (Yale TB whole genome)
- **Memory**: ~50MB baseline
- **Computational Complexity**: O(n) linear scaling

## Security

PrePrimer implements security best practices:
- Path traversal prevention
- Input sanitization with file size limits
- Secure temporary file handling
- Security event logging

[Read the security policy →](SECURITY.md)

## Contributing

Contributions welcome! PrePrimer uses:
- **Testing**: pytest with 96.90% coverage
- **Code Style**: black, isort, flake8
- **Type Checking**: mypy
- **CI/CD**: GitHub Actions

[Read the contributing guide →](docs/developer/contributing.md)

## Citation

If you use PrePrimer in your research, please cite:

```bibtex
@software{preprimer2024,
  title = {PrePrimer: Primer Scheme Converter for Tiled Amplicon Sequencing},
  author = {Sjödin, Andreas},
  year = {2024},
  version = {1.0.0},
  url = {https://github.com/FOI-Bioinformatics/preprimer}
}
```

See [CITATION.cff](CITATION.cff) for complete metadata.

## License

[MIT License](LICENSE) - See LICENSE file for details.

## Acknowledgments

- [VarVAMP](https://github.com/jonas-fuchs/varVAMP) - SADDLE algorithm for variant-aware primer design
- [ARTIC Network](https://github.com/artic-network) - Tiled amplicon sequencing protocols
- [Olivar](https://github.com/treangenlab/Olivar) - Advanced variant-aware primer design
- [Primal-page](https://github.com/artic-network/primal-page) - Primer scheme metadata standards
- [PrimerSchemes Labs](https://labs.primalscheme.com/) - Official primer scheme repository

## Links

- **Repository**: https://github.com/FOI-Bioinformatics/preprimer
- **Documentation**: [docs/](docs/)
- **Issues**: https://github.com/FOI-Bioinformatics/preprimer/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Security**: [SECURITY.md](SECURITY.md)

---

**Maintained by:** Swedish Defence Research Agency (FOI) Bioinformatics

**Version:** 1.0.0 | **Python:** 3.11+ | **Platforms:** Linux, macOS
