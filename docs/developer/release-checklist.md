# PrePrimer Release Checklist

Comprehensive checklist for preparing and executing PrePrimer releases following semantic versioning.

## Version Strategy

PrePrimer follows [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

## Pre-Release Phase (1-2 weeks before release)

### 1. Code Freeze Preparation

#### Code Quality Verification
- [ ] Run full test suite: `python -m pytest tests/ -v`
- [ ] Verify test coverage ≥95%: `python -m pytest --cov=preprimer --cov-report=html`
- [ ] Run code formatting check: `black --check preprimer/ tests/`
- [ ] Run import sorting check: `isort --check-only preprimer/ tests/`
- [ ] Run linting: `flake8 preprimer/ tests/ --max-line-length=88 --extend-ignore=E203,W503`
- [ ] Run type checking: `mypy preprimer/ --ignore-missing-imports`
- [ ] Review and fix all linting warnings

#### Security Audit
- [ ] Run security scanner: `bandit -r preprimer/ -f json -o security-report.json`
- [ ] Check dependencies: `safety check --json`
- [ ] Review all security test results: `python -m pytest tests/test_security*.py -v`
- [ ] No high/critical vulnerabilities present
- [ ] Update vulnerable dependencies if any

#### Performance Validation
- [ ] Run benchmarks: `python -m pytest tests/test_benchmarks.py -v --benchmark-only`
- [ ] Verify no performance regressions (>10% slowdown)
- [ ] Test with large datasets (Yale TB: 2,564 amplicons)
- [ ] Memory usage acceptable (<200MB for 2,500 amplicons)
- [ ] Document any performance changes in CHANGELOG

#### Functionality Testing
- [ ] Test all parsers: VarVAMP, ARTIC, Olivar, STS
- [ ] Test all writers: ARTIC, VarVAMP, Olivar, FASTA, STS
- [ ] Test bidirectional conversions for all format combinations
- [ ] Test with external validation schemes (PrimerSchemes Labs)
- [ ] Test circular genome topology detection
- [ ] Test coordinate system conversions
- [ ] Verify IUPAC degenerate nucleotide support

### 2. Documentation Review

#### User Documentation
- [ ] README.md is accurate and up-to-date
- [ ] All links work (internal and external)
- [ ] Installation instructions tested on clean system
- [ ] Quick start guide works end-to-end
- [ ] CLI reference matches actual commands: `preprimer --help`
- [ ] Configuration guide reflects current options
- [ ] Supported formats list is complete (including STS)

#### Developer Documentation
- [ ] Architecture diagrams are current
- [ ] API documentation has working examples
- [ ] Contributing guide is clear and actionable
- [ ] Code examples compile and run
- [ ] Extension guides are accurate

#### Technical Documentation
- [ ] Security documentation reflects current implementation
- [ ] Testing documentation describes all test categories
- [ ] Compatibility matrix is up-to-date
- [ ] Performance characteristics documented
- [ ] Known limitations clearly stated

### 3. CHANGELOG Preparation

- [ ] CHANGELOG.md follows [Keep a Changelog](https://keepachangelog.com/) format
- [ ] All changes since last release documented
- [ ] Changes categorized: Added, Changed, Deprecated, Removed, Fixed, Security
- [ ] Breaking changes clearly marked
- [ ] Upgrade instructions provided if needed
- [ ] Contributors acknowledged
- [ ] Release date placeholder present

### 4. Version Management

#### Update Version Numbers
- [ ] Update `__version__` in `preprimer/__init__.py`
- [ ] Update version in `pyproject.toml` (if not using setuptools-scm)
- [ ] Update version in CLI: `preprimer/cli.py` line 50
- [ ] Update version in documentation references
- [ ] Ensure setuptools-scm is properly configured

#### Dependency Management
- [ ] Review all dependency versions in `pyproject.toml`
- [ ] Update minimum Python version if needed
- [ ] Test with minimum supported Python version
- [ ] Test with latest Python version
- [ ] Document any dependency changes in CHANGELOG

### 5. Package Build Testing

#### Build Package
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# Verify build artifacts
ls -lh dist/
```

- [ ] Source distribution (`.tar.gz`) builds successfully
- [ ] Wheel (`.whl`) builds successfully
- [ ] Check package contents: `tar -tzf dist/preprimer-*.tar.gz | head -20`
- [ ] Verify MANIFEST.in includes all necessary files

#### Test Package Installation
```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/preprimer-*.whl

# Test basic functionality
python -c "import preprimer; print(preprimer.__version__)"
preprimer --version
preprimer list

# Test actual conversion
preprimer convert --input tests/test_data/datasets/small/*.tsv \
                   --output-dir /tmp/test_output \
                   --output-formats artic fasta sts

# Cleanup
deactivate
rm -rf test_env
```

- [ ] Package installs without errors
- [ ] Version number correct
- [ ] CLI commands work
- [ ] All parsers/writers accessible
- [ ] Dependencies installed correctly

#### Test on TestPyPI (Optional but Recommended)
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ preprimer

# Test installation
python -c "import preprimer; print('Success')"
```

- [ ] TestPyPI upload successful
- [ ] Installation from TestPyPI works
- [ ] Basic functionality verified

## Release Phase (Release Day)

### 1. Final Pre-Release Checks

- [ ] All CI/CD pipelines passing
- [ ] No open critical/blocker issues
- [ ] Code freeze in effect (no new commits)
- [ ] Team approval obtained (if applicable)
- [ ] Release notes reviewed and approved

### 2. Git Repository Preparation

#### Create Release Branch
```bash
# Create release branch
git checkout -b release/v1.0.0
git push origin release/v1.0.0
```

- [ ] Release branch created from main/develop
- [ ] All changes merged into release branch
- [ ] No pending pull requests

#### Update CHANGELOG
```bash
# Set release date in CHANGELOG.md
sed -i '' 's/\[Unreleased\]/[1.0.0] - 2024-10-14/' CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: Update CHANGELOG for v1.0.0 release"
```

- [ ] Release date set in CHANGELOG.md
- [ ] Version number confirmed
- [ ] Changes committed

#### Create Release Tag
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0

Major features:
- STS parser implementation (bidirectional support)
- Comprehensive security hardening
- 96.90% test coverage with 611 tests
- Topology-aware circular genome support
- Enhanced error handling and user messages

See CHANGELOG.md for full details."

# Push tag
git push origin v1.0.0
```

- [ ] Tag created with descriptive message
- [ ] Tag follows format: `v{MAJOR}.{MINOR}.{PATCH}`
- [ ] Tag pushed to remote

### 3. Build Final Release Package

```bash
# Ensure clean state
git clean -fdx
git reset --hard v1.0.0

# Build package
python -m build

# Verify checksums
sha256sum dist/*
```

- [ ] Clean build from tagged commit
- [ ] Source distribution created
- [ ] Wheel created
- [ ] Checksums recorded

### 4. PyPI Publication

#### Upload to PyPI
```bash
# Upload to PyPI (PRODUCTION)
python -m twine upload dist/*

# Verify at: https://pypi.org/project/preprimer/
```

- [ ] PyPI credentials configured
- [ ] Upload successful
- [ ] Package visible on PyPI
- [ ] Metadata displays correctly
- [ ] Download links work

#### Verify Installation from PyPI
```bash
# Test in fresh environment
python -m venv verify_env
source verify_env/bin/activate

# Install from PyPI
pip install preprimer

# Verify
python -c "import preprimer; print(f'Version: {preprimer.__version__}')"
preprimer --version

# Cleanup
deactivate
rm -rf verify_env
```

- [ ] Installation from PyPI successful
- [ ] Correct version installed
- [ ] All functionality works

### 5. GitHub Release

#### Create GitHub Release
```bash
# Create release via GitHub CLI
gh release create v1.0.0 \
  --title "PrePrimer v1.0.0 - Stable Release" \
  --notes-file RELEASE_NOTES.md \
  dist/*
```

Or via GitHub web interface:
1. Go to repository → Releases → Draft a new release
2. Choose tag: `v1.0.0`
3. Release title: "PrePrimer v1.0.0 - Stable Release"
4. Copy release notes from CHANGELOG.md
5. Attach distribution files from `dist/`
6. Mark as "Latest release"
7. Publish release

- [ ] GitHub release created
- [ ] Release notes comprehensive
- [ ] Distribution files attached
- [ ] Release marked as latest

### 6. Documentation Deployment

- [ ] Documentation site updated (if applicable)
- [ ] API documentation rebuilt
- [ ] Version selector updated (if applicable)
- [ ] Links to new version work

## Post-Release Phase

### 1. Verification (Within 24 hours)

#### Installation Testing
- [ ] Test installation on Ubuntu 22.04
- [ ] Test installation on Ubuntu 20.04
- [ ] Test installation on macOS 13 (Ventura)
- [ ] Test installation on macOS 14 (Sonoma)
- [ ] Test with Python 3.11
- [ ] Test with Python 3.12
- [ ] Test with Python 3.13

#### Smoke Testing
```bash
pip install preprimer

# Basic smoke tests
preprimer list
preprimer info tests/test_data/datasets/small/*.tsv
preprimer convert --input tests/test_data/datasets/small/*.tsv \
                   --output-dir /tmp/smoke \
                   --output-formats artic fasta sts varvamp
```

- [ ] All commands execute without errors
- [ ] Output files generated correctly
- [ ] No unexpected warnings/errors

### 2. Communication

#### Announce Release
- [ ] Update README badges (if applicable)
- [ ] Post release announcement (GitHub Discussions)
- [ ] Update project website (if applicable)
- [ ] Notify users/community (mailing list, social media)
- [ ] Update any dependent projects

#### Monitor Issues
- [ ] Watch for installation issues
- [ ] Monitor GitHub issues
- [ ] Respond to user questions
- [ ] Track bug reports

### 3. Repository Cleanup

```bash
# Merge release branch back to main
git checkout main
git merge release/v1.0.0
git push origin main

# Start next development cycle
git checkout develop
git merge main
git push origin develop

# Update CHANGELOG for next version
echo "\n## [Unreleased]\n\n### Added\n\n### Changed\n\n### Fixed\n" >> CHANGELOG.md
```

- [ ] Release branch merged to main
- [ ] Changes merged to develop branch
- [ ] CHANGELOG prepared for next release
- [ ] Version bumped to next development version (e.g., 1.1.0-dev)

### 4. Retrospective

#### Review Release Process
- [ ] Document what went well
- [ ] Document issues encountered
- [ ] Update release checklist if needed
- [ ] Note time taken for each phase
- [ ] Identify process improvements

#### Metrics Collection
- [ ] Record test coverage percentage
- [ ] Record number of tests
- [ ] Record build time
- [ ] Record package size
- [ ] Record download statistics (after 1 week)

## Emergency Rollback Procedure

If critical issues are discovered post-release:

### 1. Assess Severity
- [ ] Determine if rollback necessary (security, data loss, crashes)
- [ ] Document the issue thoroughly
- [ ] Communicate to users immediately

### 2. Quick Patch Release
If issue can be fixed quickly (< 4 hours):
```bash
# Create hotfix branch
git checkout -b hotfix/v1.0.1 v1.0.0

# Fix the issue
# ... make changes ...

# Test thoroughly
python -m pytest

# Update CHANGELOG
# Increment PATCH version
# Follow release process for v1.0.1
```

### 3. Yank Release (Last Resort)
If issue is severe and cannot be fixed quickly:
```bash
# Yank from PyPI (makes it unavailable but preserves record)
python -m twine upload --repository pypi --skip-existing dist/*
# Contact PyPI support to yank release
```

- [ ] Issue documented in GitHub
- [ ] Users notified of problem
- [ ] Workaround provided if possible
- [ ] Fix timeline communicated

## Release Types

### Patch Release (1.0.1)
- Bug fixes only
- No new features
- No breaking changes
- Fast-tracked process (2-3 days)
- Minimal testing required

### Minor Release (1.1.0)
- New features
- Backward compatible
- Full testing required
- Standard process (1-2 weeks)

### Major Release (2.0.0)
- Breaking changes
- API modifications
- Extensive testing required
- Migration guide mandatory
- Extended testing period (2-4 weeks)
- Beta release recommended

## Automation Opportunities

Future improvements to automate:
- [ ] Automated version bumping
- [ ] Automated CHANGELOG generation from commit messages
- [ ] Automated test execution on release branches
- [ ] Automated PyPI upload via CI/CD
- [ ] Automated GitHub release creation
- [ ] Automated documentation deployment

## References

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Release Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [PyPI Documentation](https://pypi.org/help/)

---

**Last Updated**: 2024-10-14
**Current Version**: 0.2.0
**Next Planned Release**: 1.0.0
