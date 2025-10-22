# Test Reorganization Plan

## Current State Analysis

### Test File Statistics
- **Total test files**: 32
- **Total lines of test code**: ~15,000
- **Largest files** (>600 lines):
  - test_cli.py (807 lines, 7 classes)
  - test_olivar_writer.py (716 lines, 2 classes)
  - test_varvamp_parser_comprehensive.py (649 lines, 6 classes)
  - test_sts_writer_comprehensive.py (615 lines, 4 classes)
  - test_enhanced_config.py (614 lines, 7 classes)
  - test_converter_comprehensive.py (610 lines, 2 classes)
  - test_real_data_comprehensive.py (600 lines, 4 classes)
  - test_varvamp_writer.py (598 lines, 2 classes)
  - test_benchmarks.py (596 lines, 6 classes)
  - test_security_comprehensive.py (584 lines, 6 classes)

### Identified Issues

1. **Duplicate Test Suites** (need merging):
   - `test_security.py` (404 lines) + `test_security_comprehensive.py` (584 lines)
   - `test_topology.py` (357 lines) + `test_topology_comprehensive.py` (321 lines)
   - `test_converter_comprehensive.py` (610) + `test_converter_comprehensive_gaps.py` (526)
   - `test_registry_comprehensive.py` (438) + `test_registry_performance.py` (320)

2. **No Clear Test Layering**:
   - Unit tests mixed with integration tests
   - No markers for test speed/type
   - No separation by test purpose

3. **Fixture Management Issues**:
   - conftest.py is 462 lines
   - conftest_legacy.py still exists (legacy fixtures)
   - Fixtures not organized by domain

---

## New Directory Structure

```
tests/
├── conftest.py                    # Minimal root conftest
├── pytest.ini                     # Test configuration
├── __init__.py
│
├── unit/                          # Fast, isolated unit tests (<50ms each)
│   ├── conftest.py               # Unit test fixtures
│   ├── core/
│   │   ├── test_interfaces.py
│   │   ├── test_exceptions.py
│   │   ├── test_registry.py
│   │   ├── test_config.py
│   │   └── test_security_validators.py
│   ├── parsers/
│   │   ├── test_varvamp_parser.py
│   │   ├── test_artic_parser.py
│   │   ├── test_olivar_parser.py
│   │   ├── test_sts_parser.py
│   │   └── test_standardized_parser.py
│   ├── writers/
│   │   ├── test_artic_writer.py
│   │   ├── test_varvamp_writer.py
│   │   ├── test_olivar_writer.py
│   │   ├── test_sts_writer.py
│   │   └── test_fasta_writer.py
│   ├── alignment/
│   │   ├── test_providers.py
│   │   └── test_registry.py
│   └── utils/
│       └── test_topology.py
│
├── integration/                   # Component interaction tests (<500ms)
│   ├── conftest.py
│   ├── test_converter.py         # Full conversion workflows
│   ├── test_parser_writer_integration.py
│   ├── test_config_integration.py
│   ├── test_alignment_integration.py
│   └── test_circular_genome.py
│
├── e2e/                          # End-to-end system tests (>500ms)
│   ├── conftest.py
│   ├── test_cli.py              # CLI end-to-end tests
│   ├── test_real_data.py        # Real world data validation
│   ├── test_cross_format.py     # All format combinations
│   └── test_workflows.py        # Complete user workflows
│
├── performance/                  # Performance & benchmark tests
│   ├── conftest.py
│   ├── test_benchmarks.py
│   ├── test_parser_performance.py
│   └── test_converter_performance.py
│
├── property/                     # Property-based tests (Hypothesis)
│   ├── conftest.py
│   ├── test_parsers_property.py
│   ├── test_validation_property.py
│   └── test_conversion_property.py
│
├── fixtures/                     # Shared test fixtures & data
│   ├── __init__.py
│   ├── conftest.py              # Fixture definitions
│   ├── parser_fixtures.py       # Parser test fixtures
│   ├── writer_fixtures.py       # Writer test fixtures
│   ├── dataset_fixtures.py      # Test dataset fixtures
│   └── config_fixtures.py       # Config test fixtures
│
├── utils/                        # Shared test utilities
│   ├── __init__.py
│   ├── assertions.py            # Custom assertion helpers
│   ├── builders.py              # Test data builders
│   ├── factories.py             # Test data factories
│   └── matchers.py              # Custom matchers
│
└── validation/                   # Validation framework (keep as is)
    ├── __init__.py
    ├── validator.py
    └── report_generator.py
```

---

## File-by-File Reorganization Mapping

### Files to Merge

#### 1. Security Tests → `unit/core/test_security.py`
**Merge**:
- test_security.py (404 lines, 6 classes)
- test_security_comprehensive.py (584 lines, 6 classes)

**Result**:
- `unit/core/test_security.py` (unit tests for validators)
- `integration/test_security_integration.py` (integration security tests)

**Actions**:
- Extract pure unit tests → unit/core/test_security.py
- Move integration tests → integration/test_security_integration.py
- Remove duplicate tests
- Add @pytest.mark.unit / @pytest.mark.integration

---

#### 2. Topology Tests → `unit/utils/test_topology.py` + `integration/test_circular_genome.py`
**Merge**:
- test_topology.py (357 lines, 5 classes)
- test_topology_comprehensive.py (321 lines, 4 classes)
- test_circular_genome.py (315 lines, 2 classes)

**Result**:
- `unit/utils/test_topology.py` (topology detection logic)
- `integration/test_circular_genome.py` (full circular genome workflows)

**Actions**:
- Extract TopologyDetector tests → unit/utils/test_topology.py
- Keep circular genome integration tests → integration/test_circular_genome.py
- Remove duplicates

---

#### 3. Converter Tests → `unit/core/test_converter.py` + `integration/test_converter.py`
**Merge**:
- test_converter_comprehensive.py (610 lines, 2 classes)
- test_converter_comprehensive_gaps.py (526 lines, 5 classes)

**Result**:
- `unit/core/test_converter.py` (converter logic unit tests)
- `integration/test_converter.py` (end-to-end conversion workflows)

**Actions**:
- Extract PrimerConverter unit tests → unit/core/test_converter.py
- Move full workflow tests → integration/test_converter.py
- Consolidate edge case tests

---

#### 4. Registry Tests → `unit/core/test_registry.py` + `performance/test_registry_performance.py`
**Merge**:
- test_registry_comprehensive.py (438 lines, 6 classes)
- test_registry_performance.py (320 lines, 2 classes)

**Result**:
- `unit/core/test_registry.py` (registry logic tests)
- `performance/test_registry_performance.py` (keep separate)

**Actions**:
- Move all functional tests → unit/core/test_registry.py
- Keep performance tests separate

---

### Files to Split (>400 lines)

#### 5. test_cli.py (807 lines) → Split into 3 files
**Split into**:
- `unit/test_cli_parsing.py` - Argument parsing tests
- `e2e/test_cli_commands.py` - Full command execution
- `e2e/test_cli_workflows.py` - Multi-command workflows

---

#### 6. test_olivar_writer.py (716 lines) → `unit/writers/test_olivar_writer.py`
**Actions**:
- Split into logical test classes
- Keep as unit tests (most are unit tests already)

---

#### 7. test_varvamp_parser_comprehensive.py (649 lines) → `unit/parsers/test_varvamp_parser.py`
**Actions**:
- Consolidate into single well-organized file
- Group by: validation, parsing, edge cases, error handling

---

#### 8. test_sts_writer_comprehensive.py (615 lines) → `unit/writers/test_sts_writer.py`
**Actions**:
- Reorganize into logical sections
- Single focused file

---

#### 9. test_enhanced_config.py (614 lines) → Split into 2 files
**Split into**:
- `unit/core/test_config.py` - Config validation & settings
- `integration/test_config_integration.py` - Config manager, watchers

---

#### 10. test_varvamp_writer.py (598 lines) → `unit/writers/test_varvamp_writer.py`
**Actions**:
- Keep as single file, reorganize sections

---

#### 11. test_benchmarks.py (596 lines) → `performance/test_benchmarks.py`
**Actions**:
- Move to performance directory
- Keep structure mostly intact

---

#### 12. test_security_comprehensive.py (584 lines) → (Already covered in merge #1)

---

### Files to Relocate (no changes needed)

#### Move to appropriate directories:
- test_alignment.py → `unit/alignment/test_alignment.py`
- test_all_parsers.py → `integration/test_all_parsers.py` (cross-parser tests)
- test_core_interfaces.py → `unit/core/test_interfaces.py`
- test_error_handling.py → `unit/core/test_exceptions.py`
- test_integration.py → `integration/test_parser_writer_integration.py`
- test_main_api_comprehensive.py → `integration/test_main_api.py`
- test_property_based.py → `property/test_parsers_property.py`
- test_real_data_comprehensive.py → `e2e/test_real_data.py`
- test_standardized_parser.py → `unit/parsers/test_standardized_parser.py`

#### Parser Tests → `unit/parsers/`:
- test_artic_parser_comprehensive.py → `unit/parsers/test_artic_parser.py`
- test_olivar_parser_comprehensive.py → `unit/parsers/test_olivar_parser.py`
- test_sts_parser_comprehensive.py → `unit/parsers/test_sts_parser.py`

#### Other Tests:
- test_primerscheme_info_comprehensive.py → `unit/core/test_primerscheme_info.py`
- test_exceptions_comprehensive.py → merge into `unit/core/test_exceptions.py`
- test_refactored_system.py → split into appropriate unit/integration tests

---

## Fixture Reorganization

### Current conftest.py (462 lines) → Split into:

1. **Root conftest.py** (minimal, ~50 lines):
   - Session-level configuration
   - Plugin configuration
   - Test environment verification

2. **fixtures/conftest.py** (~150 lines):
   - All fixture definitions
   - Import from domain-specific fixture modules

3. **fixtures/dataset_fixtures.py** (~100 lines):
   - small_dataset, medium_dataset
   - unified_datasets_dir
   - cross_format_test_data

4. **fixtures/parser_fixtures.py** (~80 lines):
   - Parser-specific fixtures
   - parser_test_data

5. **fixtures/writer_fixtures.py** (~50 lines):
   - Writer-specific fixtures

6. **fixtures/config_fixtures.py** (~50 lines):
   - test_config
   - Various config combinations

### Remove:
- conftest_legacy.py (deprecate completely)

---

## Implementation Order

### Phase 1: Setup Infrastructure (Day 1)
1. Create new directory structure
2. Create utils/ with assertions.py, builders.py, factories.py
3. Update pyproject.toml with new test markers

### Phase 2: Merge Duplicate Tests (Days 2-3)
1. Merge security tests
2. Merge topology tests
3. Merge converter tests
4. Merge registry tests

### Phase 3: Split Large Files (Days 4-6)
1. Split test_cli.py
2. Split test_enhanced_config.py
3. Reorganize other large files

### Phase 4: Relocate Files (Days 7-8)
1. Move parser tests to unit/parsers/
2. Move writer tests to unit/writers/
3. Move core tests to unit/core/
4. Move integration tests
5. Move e2e tests
6. Move performance tests

### Phase 5: Fixture Reorganization (Days 9-10)
1. Create domain-specific fixture files
2. Update root conftest.py
3. Remove conftest_legacy.py
4. Update all test imports

### Phase 6: Add Test Markers (Day 11)
1. Add @pytest.mark.unit to all unit tests
2. Add @pytest.mark.integration to integration tests
3. Add @pytest.mark.e2e to e2e tests
4. Add @pytest.mark.performance to benchmarks

### Phase 7: CI Configuration (Day 12)
1. Update CI to run test layers
2. Configure timeouts
3. Add flaky test handling

### Phase 8: Validation & Cleanup (Days 13-14)
1. Run full test suite
2. Verify all tests pass
3. Check coverage maintained
4. Update documentation
5. Clean up any remaining issues

---

## Success Criteria

- [ ] All 636 tests still pass
- [ ] Test coverage maintained at ≥96%
- [ ] No test file >400 lines
- [ ] Clear separation: unit / integration / e2e
- [ ] All tests properly marked
- [ ] conftest.py <100 lines
- [ ] conftest_legacy.py removed
- [ ] CI runs test layers in sequence
- [ ] Documentation updated

---

## Risks & Mitigation

**Risk**: Breaking existing tests during reorganization
**Mitigation**:
- Work in feature branch
- Run tests after each change
- Keep git history clean for easy rollback

**Risk**: Import path issues
**Mitigation**:
- Update all imports systematically
- Use IDE refactoring tools
- Add __init__.py files

**Risk**: Fixture import cycles
**Mitigation**:
- Plan fixture dependencies carefully
- Use pytest fixture scoping correctly
- Test fixture imports independently

**Risk**: CI breakage
**Mitigation**:
- Test CI changes locally with act
- Update CI incrementally
- Keep backwards compatibility during transition
