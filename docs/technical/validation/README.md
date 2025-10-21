# PrePrimer Validation Documentation

This directory contains comprehensive validation reports and testing documentation for PrePrimer.

## Validation Reports

### [Real Data Testing](real-data-testing.md)
Comprehensive validation report using real-world primer scheme datasets. Documents:
- Test methodology and infrastructure
- Format conversion validation (all 5 output formats)
- Real alignment tool testing (BLAST, Exonerate, merPCR)
- Edge case handling (circular genomes, degenerate primers)
- Performance benchmarking

**Key Results**:
- 23 comprehensive tests, 100% pass rate
- All 5 output formats validated
- Real tool execution (not mocked)
- Performance targets exceeded (2-8x faster than expected)

### [v0.2.0 Validation Report](v0.2.0-validation.md)
Success report for v0.2.0 release validation, documenting:
- STS format enhancement (critical bug fix)
- 100% test success achievement
- Production readiness assessment
- Impact analysis and recommendations

## Test Framework

The comprehensive validation framework is located in `tests/validation/`:

```
tests/validation/
├── __init__.py           # Module exports
├── validator.py          # Validation framework (430 lines)
├── report_generator.py   # Multi-format reporting
└── README.md             # Developer guide
```

### Quick Start

Run comprehensive real data validation:

```bash
# All real data tests
pytest tests/test_real_data_comprehensive.py -m real_data -v

# Quick tests only (CI-friendly)
pytest tests/test_real_data_comprehensive.py -m quick -v

# Standard validation tests
pytest tests/test_real_data_comprehensive.py -m standard -v
```

## Test Categories

The comprehensive test suite includes:

1. **Format Conversions** (13 tests)
   - Small dataset → all 5 formats
   - Medium dataset (80 amplicons) → all 5 formats
   - Multi-format simultaneous output
   - Round-trip conversions

2. **Real Alignment Tests** (5 tests)
   - BLAST integration
   - Exonerate integration
   - merPCR integration

3. **Edge Cases** (3 tests)
   - Circular genome handling
   - Minimal datasets
   - Degenerate IUPAC primers

4. **Integration Workflows** (2 tests)
   - End-to-end pipelines

## Validation Results Summary

```
╔═══════════════════════════════════════╗
║  PrePrimer v0.2.0 - Validation      ║
╠═══════════════════════════════════════╣
║  Total Tests:        23              ║
║  Passed:             23 ✅            ║
║  Failed:             0               ║
║  Success Rate:       100%            ║
║  Execution Time:     3.31 seconds    ║
╚═══════════════════════════════════════╝
```

## Documentation

For detailed testing documentation, see:
- [Testing Framework](../testing.md) - Overall test suite (611+ tests)
- [Test Suite README](../../../tests/validation/README.md) - Developer guide for validation framework
- [Contributing Guide](../../developer/contributing.md) - How to add new tests

## External Datasets

PrePrimer has been validated with external datasets from PrimerSchemes Labs:
- Yale TB (M. tuberculosis, 2,564 amplicons)
- Yale West Nile Virus (38 amplicons)
- VarVAMP HAV (Hepatitis A with degenerate primers)
- ARTIC nCoV-2019 V5.3.2 (96 amplicons)
- Olivar mitochondrial designs (15 amplicons)

---

**Status**: Production-ready for v0.2.0 release
**Last Updated**: 2025-10-21
