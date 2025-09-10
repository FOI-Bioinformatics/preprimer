# CI/CD Pipeline

Continuous Integration and Deployment configuration for PrePrimer development and release processes.

## Pipeline Overview

PrePrimer uses a multi-tier CI/CD pipeline with GitHub Actions to ensure code quality, security, and performance.

### Pipeline Structure
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Smoke Tests   │───▶│ Comprehensive    │───▶│  Deployment     │
│  (Fast Checks)  │    │    Testing       │    │   Readiness     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Code Quality   │    │  Security &      │    │   Performance   │
│   Validation    │    │  Integration     │    │   Monitoring    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Workflows

### 1. Quick Tests (test.yml)
**Purpose**: Fast feedback for development
**Triggers**: Push to main/develop/v0.2.0, Pull requests

```yaml
jobs:
  quick-tests:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.8", "3.10", "3.12", "3.13"]
    
    steps:
      - name: Run core tests with coverage
        run: |
          python -m pytest tests/test_all_parsers.py tests/test_core_interfaces.py \
            -v --cov=preprimer --cov-report=xml --tb=short
```

**Features:**
- **Fast execution**: ~3-5 minutes for core test validation
- **Multi-platform**: Ubuntu and macOS testing
- **Coverage reporting**: Integrated with Codecov
- **Fail-fast disabled**: Complete matrix execution

### 2. Comprehensive Testing (comprehensive-testing.yml)
**Purpose**: Full validation across all testing methodologies
**Triggers**: Push to main branches, PR, scheduled runs, manual triggers

#### Job Categories

##### Smoke Tests
```yaml
smoke-tests:
  strategy:
    matrix:
      python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]
  
  steps:
    - name: Validate installation
      run: |
        python -c "import preprimer; print('PrePrimer imported successfully')"
```

##### Comprehensive Tests
```yaml
comprehensive-tests:
  strategy:
    matrix:
      os: [ubuntu-latest, macos-latest]
      python-version: ["3.8", "3.10", "3.12", "3.13"]
  
  steps:
    - name: Run comprehensive test suite
      run: |
        python -m pytest tests/ \
          --cov=preprimer \
          --cov-report=xml \
          --tb=short \
          -x
```

##### Specialized Testing Jobs
- **Property Testing**: Hypothesis-based testing with 1000 examples
- **Security Testing**: Bandit, Safety, and custom security validation
- **Performance Benchmarking**: Automated with historical comparison
- **Integration Testing**: End-to-end workflow validation
- **Mutation Testing**: Test quality assessment (scheduled only)

## Testing Configuration

### Test Matrix
| Platform | Python Versions | Test Types |
|----------|----------------|------------|
| Ubuntu Latest | 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 | All tests |
| macOS Latest | 3.8, 3.10, 3.12, 3.13 | Core + Integration |

### Performance Benchmarking
```yaml
performance-benchmarks:
  if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[benchmark]')
  
  steps:
    - name: Run performance benchmarks
      run: |
        python -m pytest tests/test_benchmarks.py -v \
          --benchmark-only \
          --benchmark-json=benchmark-results.json \
          --benchmark-save=benchmark-$(date +%Y%m%d-%H%M%S)
```

**Features:**
- **Conditional execution**: Only on schedule or manual trigger
- **Historical tracking**: Benchmark result storage
- **Statistical analysis**: Performance regression detection
- **PR comments**: Automatic benchmark result reporting

### Security Integration
```yaml
security-testing:
  steps:
    - name: Run security validation tests
      run: python -m pytest tests/test_security.py -v --tb=short
    
    - name: Run bandit security linter
      run: bandit -r preprimer/ -f json -o bandit-report.json
    
    - name: Check dependencies for vulnerabilities
      run: safety check --json --output safety-report.json
```

## Code Quality Enforcement

### Pre-commit Integration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
```

### Quality Gates
```yaml
code-quality:
  steps:
    - name: Run code formatting check
      run: black --check --diff preprimer/ tests/ examples/ scripts/
    
    - name: Run import sorting check  
      run: isort --check-only --diff preprimer/ tests/ examples/ scripts/
    
    - name: Run linting
      run: flake8 preprimer/ tests/ examples/ scripts/
    
    - name: Run type checking
      run: mypy preprimer/ --ignore-missing-imports
```

## Deployment Pipeline

### Build Validation
```yaml
deployment-check:
  needs: [comprehensive-tests, security-testing, code-quality]
  if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/v0.2.0'
  
  steps:
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: python -m twine check dist/*
    
    - name: Test package installation
      run: |
        pip install dist/*.whl
        python -c "import preprimer; print('Package installation successful')"
```

### Artifact Management
```yaml
artifacts:
  coverage-reports:
    retention-days: 7
    path: |
      coverage.xml
      htmlcov/
  
  benchmark-results:
    retention-days: 30
    path: |
      benchmark-results.json
      .benchmarks/
  
  security-reports:
    retention-days: 30
    path: |
      bandit-report.json
      safety-report.json
```

## Development Workflow Integration

### Branch Protection Rules
Required status checks for merging:
- **Quick Tests**: Must pass for all Python versions
- **Code Quality**: All quality checks must pass
- **Security**: No high-severity vulnerabilities
- **Coverage**: Maintain >95% coverage threshold

### Trigger Mechanisms

#### Automatic Triggers
- **Push to main/develop**: Full pipeline execution
- **Pull Request**: Quick tests + code quality
- **Scheduled (nightly)**: Performance benchmarks + mutation testing

#### Manual Triggers
- **Commit message `[benchmark]`**: Force benchmark execution
- **Commit message `[mutation]`**: Trigger mutation testing
- **Manual workflow dispatch**: Full pipeline on demand

## Environment Configuration

### Secrets and Variables
```yaml
env:
  PYTHONUNBUFFERED: 1
  PYTEST_ADDOPTS: --color=yes

secrets:
  CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
  
variables:
  PYTHON_VERSION_MATRIX: '["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]'
```

### Caching Strategy
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'
    cache-dependency-path: 'pyproject.toml'
```

**Benefits:**
- **70% faster** dependency installation
- **Consistent** environment setup
- **Reduced** network usage and failures

## Monitoring and Reporting

### Test Result Aggregation
```yaml
test-summary:
  needs: [comprehensive-tests, property-testing, security-testing, integration-testing]
  if: always()
  
  steps:
    - name: Generate test summary
      run: |
        echo "## Test Summary" >> $GITHUB_STEP_SUMMARY
        echo "- Comprehensive Tests: ${{ needs.comprehensive-tests.result }}" >> $GITHUB_STEP_SUMMARY
        echo "- Property Testing: ${{ needs.property-testing.result }}" >> $GITHUB_STEP_SUMMARY
```

### Performance Monitoring
Automated performance tracking with:
- **Baseline comparison**: Compare against historical performance
- **Regression alerts**: Notify on >10% performance degradation
- **Trend analysis**: Long-term performance monitoring

### Security Monitoring
Continuous security validation:
- **Dependency scanning**: Automated vulnerability detection
- **Code analysis**: Static security analysis with Bandit
- **Input validation testing**: Custom security test suite

## CI/CD Best Practices

### Pipeline Optimization
1. **Parallel Execution**: Run independent jobs concurrently
2. **Caching**: Cache dependencies and build artifacts
3. **Fail Fast**: Stop on critical failures to save resources
4. **Conditional Execution**: Run expensive operations only when needed

### Resource Management
```yaml
timeout-minutes: 30  # Prevent runaway jobs
strategy:
  fail-fast: false   # Complete matrix even if some fail
```

### Error Handling
```yaml
- name: Upload logs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: failure-logs
    path: |
      pytest-logs/
      benchmark-failures/
```

## Local Development Integration

### Running CI Locally
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run CI equivalent tests locally
python -m pytest                           # Full test suite
python -m pytest --tb=short -q            # CI-style output
python -m pytest tests/test_security.py   # Security subset

# Code quality checks
black --check preprimer/ tests/
isort --check-only preprimer/ tests/
flake8 preprimer/ tests/
mypy preprimer/
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run all hooks
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Troubleshooting CI/CD

### Common Issues

#### Test Failures
1. **Check logs**: Review detailed test output
2. **Reproduce locally**: Run same commands locally
3. **Environment differences**: Verify Python/OS matrix
4. **Dependency conflicts**: Check for version mismatches

#### Performance Regressions
1. **Compare benchmarks**: Use historical comparison
2. **Profile locally**: Identify performance bottlenecks
3. **Check test data**: Verify test data consistency
4. **Resource constraints**: Monitor CI resource usage

#### Security Alerts
1. **Review reports**: Check Bandit and Safety outputs
2. **Update dependencies**: Resolve known vulnerabilities
3. **False positives**: Configure tool exclusions if needed
4. **Security tests**: Ensure custom security tests pass

This CI/CD pipeline ensures PrePrimer maintains high quality standards while enabling efficient development workflows and reliable releases.