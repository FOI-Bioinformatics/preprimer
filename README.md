# PrePrimer

Primer scheme converter for tiled amplicon sequencing supporting linear and circular genomes.

[![CI Status](https://github.com/FOI-Bioinformatics/preprimer/workflows/CI/badge.svg)](https://github.com/FOI-Bioinformatics/preprimer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | macOS](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FOI-Bioinformatics/preprimer)

PrePrimer provides bidirectional conversion between primer design formats used in tiled amplicon sequencing workflows. The tool handles VarVAMP, ARTIC, Olivar, STS, Primer3, FASTA, and GFF3 formats with automatic topology detection for circular genomes.

## Current Version: v0.4.0

### Recent Changes

- **Canonical 6-column `primer.bed`**: read and write the legacy/primal-page form distributed by community scheme repos (`--bed-columns {6,7}`)
- **info.json import**: scheme metadata (species, version, authors) is read on input and preserved through conversion
- **New formats**: GFF3 output and Primer3 (Boulder-IO) input
- **More in-silico-PCR engines**: seqkit, EMBOSS primersearch, and mfeprimer join BLAST, Exonerate, me-PCR, and merPCR
- **Fixed** an ARTIC writer coordinate off-by-one that affected ARTIC-sourced conversions
- **Minimum Python is now 3.12**

See [CHANGELOG.md](CHANGELOG.md) for complete release history.

## Features

PrePrimer provides format conversion with the following capabilities:

- **Format Support**: 5 input parsers (VarVAMP, ARTIC, Olivar, STS, Primer3) and 6 output writers (VarVAMP, ARTIC, Olivar, STS, FASTA, GFF3) supporting 30 conversion pathways
- **Topology Detection**: Automatic identification of circular genome architectures (mitochondrial DNA, plasmids, viral episomes)
- **Standards Compliance**: 6- and 7-column `primer.bed`, primal-page `info.json` (read and write), and articbedversion specifications
- **IUPAC Support**: Handling of degenerate nucleotide codes for variant-aware primer designs
- **In-silico PCR / alignment**: BLAST, Exonerate, me-PCR, merPCR, seqkit, EMBOSS primersearch, and mfeprimer providers
- **Input Validation**: Path sanitization, size limits, and format verification for security

## Codebase Statistics

- **Source Code**: ~7,600 lines of Python across 35 modules
- **Test Suite**: ~17,500 lines; 726 passing tests (8 skipped)
- **Test Coverage**: ~94% line / ~92% branch coverage
- **Performance**: Sub-second processing for datasets containing 500 amplicons

## Installation

### Requirements

- Python 3.12 or higher
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

# Perform conversion; returns a dict mapping each output format to its path
result = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic", "fasta"],
    prefix="SARS-CoV-2"
)

for output_format, output_path in result.items():
    print(f"{output_format}: {output_path}")
```

## Supported Formats

| Format | Input | Output | Specification |
|--------|-------|--------|---------------|
| **VarVAMP** | ✅ `.tsv` | ✅ | 13-column TSV with IUPAC degenerate nucleotide support |
| **ARTIC** | ✅ `.bed` | ✅ | 6- or 7-column `primer.bed` + `reference.fasta` + `info.json` (primal-page) |
| **Olivar** | ✅ `.csv` | ✅ | CSV format with amplicon metadata and circular genome support |
| **STS** | ✅ `.sts.tsv` | ✅ | 3/4-column TSV with automatic header detection |
| **Primer3** | ✅ `.p3` | ❌ | Primer3 Boulder-IO output (`KEY=value`) |
| **FASTA** | ❌ | ✅ | Multi-FASTA with metadata in sequence headers |
| **GFF3** | ❌ | ✅ | Primer binding-site features for genome browsers |

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
- [Extending PrePrimer (adding parsers/writers)](docs/developer/extending.md)
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

PrePrimer integrates multiple in-silico-PCR and alignment providers for primer-to-reference validation. The `align` command reads primers in STS format:

```bash
# In-silico PCR with merPCR (recommended)
preprimer align --sts-file primers.sts.tsv --reference genome.fasta \
                --output-dir results/ --output-formats merpcr

# Per-primer alignment with BLAST
preprimer align --sts-file primers.sts.tsv --reference genome.fasta \
                --output-dir results/ --output-formats primers --aligner blast
```

- In-silico-PCR engines (`--output-formats`): `me-pcr`, `merpcr`, `seqkit`, `primersearch`, `mfeprimer`
- Per-primer alignment (`--output-formats primers`) uses `--aligner {blast,exonerate}`

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
@software{preprimer2026,
  title = {PrePrimer: Primer Scheme Converter for Tiled Amplicon Sequencing},
  author = {PrePrimer Contributors},
  year = {2026},
  url = {https://github.com/FOI-Bioinformatics/preprimer},
  version = {0.4.0}
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
- [PrimalScheme](https://github.com/aresti/primalscheme) - primal-page schema
- [PrimerSchemes Labs](https://github.com/quick-lab/primerschemes) - validation datasets
