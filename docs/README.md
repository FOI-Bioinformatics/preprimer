# PrePrimer Documentation

This directory contains the complete documentation for PrePrimer, a comprehensive primer scheme converter for tiled amplicon sequencing applications with support for linear and circular genome architectures.

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[User Guide](user-guide/)** | Installation, usage, and configuration | End users |
| **[Technical Documentation](#technical-documentation)** | Security, testing, and compatibility | Technical users |
| **[Developer Documentation](#developer-documentation)** | Architecture, contributing, and extending | Developers |
| **[API Reference](api/)** | Programming interfaces | Developers |
| **[Tutorials](tutorials/)** | Examples and use cases | All users |

## User Documentation

### Getting Started
- **[Installation Guide](user-guide/installation.md)** - System requirements and installation procedures
- **[Quick Start Guide](user-guide/quick-start.md)** - First conversion in 5 minutes
- **[Basic Usage](user-guide/basic-usage.md)** - Essential commands and workflows

### Reference
- **[CLI Reference](user-guide/cli-reference.md)** - Complete command-line documentation
- **[Configuration Guide](user-guide/configuration.md)** - Configuration options and customization
- **[Supported Formats](user-guide/supported-formats.md)** - Input and output format specifications

## Technical Documentation

### System Specifications
- **[Security Implementation](technical/security.md)** - Comprehensive security features and validation
- **[Testing Framework](technical/testing.md)** - Extensive testing methodology (581 tests with 96.90% coverage)
- **[Platform Compatibility](technical/compatibility.md)** - Platform support, topology handling, and ecosystem integration

## Developer Documentation

### Architecture and Design
- **[Architecture Overview](developer/architecture.md)** - Topology-aware system design and component structure
- **[Contributing Guide](developer/contributing.md)** - Development procedures and ecosystem standards
- **[Extending PrePrimer](developer/extending.md)** - Adding new formats with topology and standards support

### Development Resources
- **[Performance Guide](developer/performance.md)** - Performance characteristics and optimization
- **[CI/CD Pipeline](developer/ci-cd.md)** - Continuous integration and deployment

## Documentation Standards

This documentation follows scientific writing principles:

- **Objective Language**: Technical descriptions use precise, factual language
- **Evidence-Based**: Claims supported by benchmarks, tests, and measurements
- **Reproducible Instructions**: Sufficient detail for independent reproduction
- **Structured Content**: Clear organization for users with varying backgrounds

## Examples and Tutorials

### Practical Applications
- **[Use Cases](tutorials/use-cases.md)** - Real-world research applications
- **[Format Conversion Examples](tutorials/format-conversion.md)** - Step-by-step conversion procedures
- **[Pipeline Integration](tutorials/integration.md)** - Integration with bioinformatics workflows

### Code Examples
- **[API Examples](examples/)** - Programmatic usage examples
- **[Sample Workflows](examples/)** - Complete workflow implementations

## Contributing to Documentation

When contributing to documentation:

1. **Follow Structure**: Use established organization and naming conventions
2. **Scientific Language**: Use objective, evidence-based language
3. **Include Examples**: Provide practical code snippets and usage examples
4. **Cross-Reference**: Link to related documentation sections
5. **Test Instructions**: Verify all instructions work as documented

For detailed contribution guidelines, see the [Contributing Guide](developer/contributing.md).

## Quick Reference Commands

```bash
# Installation
pip install -e ".[dev]"

# Basic usage
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic

# Run tests
python -m pytest

# Check documentation
python -c "import preprimer; help(preprimer)"
```

## Support and Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and community support
- **Documentation Issues**: Improvements and corrections

---

For the most current documentation, refer to the version control repository. Documentation is maintained alongside code releases to ensure accuracy and relevance.