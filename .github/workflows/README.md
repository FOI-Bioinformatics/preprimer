# GitHub Actions Workflows

Simplified CI/CD for PrePrimer.

## Active Workflows

### `ci.yml` - Continuous Integration

**Triggers:** Push to main/develop/v0.2.0, Pull requests

**What it does:**
- **Test**: Runs full test suite on Ubuntu and macOS with Python 3.11, 3.12, 3.13
- **Lint**: Checks code formatting, imports, linting, type checking, security

**Matrix:**
- 2 operating systems × 3 Python versions = 6 test combinations
- Parallel execution for speed

**Typical run time:** ~3-5 minutes

### `release.yml` - Release Build

**Triggers:** Version tags (v*.*.*)

**What it does:**
1. Run full test suite
2. Build wheel and source distribution
3. Validate package with twine
4. Calculate SHA256 checksums
5. Create GitHub release with build artifacts

**Output:**
- `preprimer-X.Y.Z.tar.gz` (source distribution)
- `preprimer-X.Y.Z-py3-none-any.whl` (wheel)
- `SHA256SUMS` (checksums)

**Typical run time:** ~2-3 minutes

## Usage

### Running CI

CI runs automatically on push/PR. Nothing to do!

### Creating a Release

```bash
# 1. Tag the release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 2. Workflow runs automatically
# 3. Check Actions tab for progress
# 4. Release appears in GitHub Releases
```

### Manual Test Run

```bash
# Trigger CI manually from Actions tab
# Click "CI" → "Run workflow" → Select branch
```

## What Was Removed

Previous workflows had 10+ separate jobs:
- ❌ Separate smoke tests (now: single test job)
- ❌ Property-based testing job (now: included in tests)
- ❌ Security testing job (now: included in lint)
- ❌ Performance benchmarks (now: run manually with pytest-benchmark)
- ❌ Integration testing job (now: included in tests)
- ❌ Mutation testing (now: run manually, too slow for CI)
- ❌ Deployment checks (now: simplified)
- ❌ Test summary job (redundant)

**Result:** 2 simple workflows instead of 3 complex ones

## Archived Workflows

Old workflows are kept as `.old` files for reference:
- `test.yml.old` - Legacy quick tests
- `comprehensive-testing.yml.old` - Over-engineered testing (13 jobs!)
- `publish.yml.old` - Complex PyPI publishing with 6 stages

## Local Testing

Run the same checks locally before pushing:

```bash
# Run tests
python -m pytest tests/ --cov=preprimer -v

# Check formatting
black --check preprimer/ tests/

# Check imports
isort --check-only preprimer/ tests/

# Lint
flake8 preprimer/ tests/ --max-line-length=88 --extend-ignore=E203,W503

# Type check
mypy preprimer/ --ignore-missing-imports

# Security
bandit -r preprimer/ -ll
```

## Troubleshooting

### CI fails on "Check formatting"

```bash
# Fix locally
black preprimer/ tests/
git add .
git commit -m "style: Format code"
```

### CI fails on "Check imports"

```bash
# Fix locally
isort preprimer/ tests/
git add .
git commit -m "style: Sort imports"
```

### Release workflow doesn't trigger

- Ensure tag follows pattern: `v*.*.*` (e.g., `v1.0.0`)
- Tag must be pushed: `git push origin v1.0.0`
- Check Actions tab for workflow run

### Tests pass locally but fail in CI

- Check Python version (CI tests 3.11, 3.12, 3.13)
- Check OS differences (CI tests Ubuntu + macOS)
- Review CI logs in Actions tab

## Performance

**Before simplification:**
- 10 jobs, many running sequentially
- ~15-20 minutes for full run
- Redundant test execution

**After simplification:**
- 2 jobs, running in parallel
- ~3-5 minutes for full run
- Single test execution per configuration

**60-75% faster! 🚀**

---

**Last Updated:** 2024-10-14
