# PrePrimer

Primer scheme converter for tiled amplicon sequencing supporting linear and circular genomes.

[![CI Status](https://github.com/FOI-Bioinformatics/preprimer/workflows/CI/badge.svg)](https://github.com/FOI-Bioinformatics/preprimer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FOI-Bioinformatics/preprimer)

PrePrimer provides bidirectional conversion between primer design formats used in tiled amplicon sequencing workflows. The tool handles VarVAMP, ARTIC, Olivar, STS, and FASTA formats with automatic topology detection for circular genomes.

## Current Version: v0.3.0

### Recent Changes

- **Comprehensive Writer Testing**: All 5 output writers now have complete test coverage (110/113 tests, 97.3%)
- **BaseWriterTest Pattern**: Reusable test infrastructure with automatic contract enforcement
- **Performance Baselines**: Established benchmarks for all writers (51-591µs write times)

See [CHANGELOG.md](CHANGELOG.md) for complete release history.

## Features

PrePrimer provides format conversion with the following capabilities:

- **Format Support**: 4 input parsers (VarVAMP, ARTIC, Olivar, STS) and 5 output writers (VarVAMP, ARTIC, Olivar, STS, FASTA) supporting 20 conversion pathways
- **Topology Detection**: Automatic identification of circular genome architectures (mitochondrial DNA, plasmids, viral episomes)
- **Standards Compliance**: Implementation of primal-page info.json schema and articbedversion specifications (v2.0/v3.0)
- **IUPAC Support**: Handling of degenerate nucleotide codes for variant-aware primer designs
- **Alignment Integration**: BLAST, Exonerate, merPCR, and me-PCR providers for primer-to-reference alignment
- **Input Validation**: Path sanitization, size limits, and format verification for security

## Codebase Statistics

- **Source Code**: ~6,900 lines of Python across 59 modules
- **Test Suite**: ~22,300 lines implementing 998 tests
- **Test Coverage**: 96.90% with 100% pass rate
- **Performance**: Sub-second processing for datasets containing 500 amplicons

## Installation

### Requirements

- Python 3.11 or higher
- Linux or macOS operating system

### Setup

```bash
# Clone repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install package
pip install -e .

# Verify installation
preprimer --version
```

## Quick Start

### Command Line Interface

```bash
# List supported formats
preprimer list

# Inspect input file
preprimer info primers.tsv

# Convert single format
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic

# Convert to multiple formats
preprimer convert --input primers.tsv --output-dir output/ \
                  --output-formats artic fasta sts --prefix MyVirus
```

### Python API

```python
from preprimer.core.converter import PrimerConverter
from preprimer.core.enhanced_config import EnhancedConfig

# Initialize converter
config = EnhancedConfig()
converter = PrimerConverter(config)

# Perform conversion
result = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic", "fasta"],
    prefix="SARS-CoV-2"
)

print(f"Converted {len(result)} amplicons")
```

## Supported Formats

| Format | Input | Output | Specification |
|--------|-------|--------|---------------|
| **VarVAMP** | ✅ `.tsv` | ✅ | 13-column TSV with IUPAC degenerate nucleotide support |
| **ARTIC** | ✅ `.bed` | ✅ | BED6 format following articbedversion v2.0/v3.0 |
| **Olivar** | ✅ `.csv` | ✅ | CSV format with amplicon metadata and circular genome support |
| **STS** | ✅ `.sts.tsv` | ✅ | 3/4-column TSV with automatic header detection |
| **FASTA** | ❌ | ✅ | Multi-FASTA with metadata in sequence headers |

Full format specifications available in [docs/user-guide/supported-formats.md](docs/user-guide/supported-formats.md).

## Documentation

### User Documentation
- [Installation Guide](docs/user-guide/installation.md)
- [Quick Start Guide](docs/user-guide/quick-start.md)
- [Basic Usage](docs/user-guide/basic-usage.md)
- [CLI Reference](docs/user-guide/cli-reference.md)
- [Supported Formats](docs/user-guide/supported-formats.md)
- [Configuration](docs/user-guide/configuration.md)

### Developer Documentation
- [Architecture Overview](docs/developer/architecture.md)
- [Adding Parsers](docs/developer/adding-parsers.md)
- [Contributing Guidelines](docs/developer/contributing.md)
- [Release Checklist](docs/developer/release-checklist.md)

### Technical Documentation
- [Testing Strategy](docs/technical/testing.md)
- [Security Validation](docs/technical/security.md)
- [Windows Compatibility](docs/technical/windows-compatibility.md)
- [Validation Reports](docs/technical/validation/)

### Development Documentation
- [Test Patterns](docs/development/patterns/)
- [Migration History](docs/development/migrations/)

## Alignment Integration

PrePrimer integrates multiple alignment providers for primer-to-reference validation:

```bash
# Align primers using merPCR (recommended)
preprimer align --primers primers.bed --reference genome.fasta --aligner merpcr

# Use BLAST for alignment
preprimer align --primers primers.tsv --reference genome.fasta \
                --aligner blast --output alignment.tsv
```

Available providers: `blast`, `exonerate`, `merpcr`, `mepcr`

## Testing

```bash
# Run complete test suite
python -m pytest

# Run with coverage report
python -m pytest --cov=preprimer --cov-report=html

# Run specific test categories
python -m pytest -m unit          # Unit tests only
python -m pytest -m integration   # Integration tests
python -m pytest -m security      # Security validation
```

## Development

### Code Quality Tools

```bash
# Format code
black preprimer/ tests/
isort preprimer/ tests/

# Static analysis
flake8 preprimer/ tests/ --max-line-length=88 --extend-ignore=E203,W503
mypy preprimer/ --ignore-missing-imports

# Security scanning
bandit -r preprimer/ -ll
```

## Citation

If you use PrePrimer in your research, please cite:

```bibtex
@software{preprimer2025,
  title = {PrePrimer: Primer Scheme Converter for Tiled Amplicon Sequencing},
  author = {PrePrimer Contributors},
  year = {2025},
  url = {https://github.com/FOI-Bioinformatics/preprimer},
  version = {0.3.0}
}
```

See [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Security

For security concerns, please review [SECURITY.md](SECURITY.md) for reporting procedures.

## Support

- **Issues**: [GitHub Issues](https://github.com/FOI-Bioinformatics/preprimer/issues)
- **Documentation**: [docs/](docs/)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## Acknowledgments

PrePrimer implements specifications from:
- [ARTIC Network](https://artic.network/) - articbedversion standards
- [Primal Scheme](https://github.com/aresti/primal-scheme) - primal-page schema
- [PrimerSchemes Labs](https://github.com/quick-lab/primerschemes) - validation datasets
