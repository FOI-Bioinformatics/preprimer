# PyPI Publishing Guide

Automated publishing workflow for PrePrimer releases using GitHub Actions and PyPI Trusted Publishing.

## Overview

PrePrimer uses an automated GitHub Actions workflow to publish releases to PyPI. The workflow uses PyPI's "Trusted Publishing" feature (OIDC), which is more secure than API tokens and doesn't require storing secrets.

## Workflow Triggers

The publishing workflow (`.github/workflows/publish.yml`) triggers on:

1. **GitHub Release Published**: Recommended for production releases
   ```bash
   gh release create v1.0.0 --title "PrePrimer v1.0.0" --notes "Release notes..."
   ```

2. **Version Tag Pushed**: Alternative trigger
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

## Initial Setup (One-Time Configuration)

### 1. Configure PyPI Trusted Publishing

**For Production PyPI:**

1. Go to https://pypi.org/manage/account/publishing/
2. Scroll to "Pending publishers"
3. Add a new pending publisher with:
   - **PyPI Project Name**: `preprimer`
   - **Owner**: `FOI-Bioinformatics`
   - **Repository name**: `preprimer`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

4. Click "Add"

**For Test PyPI (Optional):**

1. Go to https://test.pypi.org/manage/account/publishing/
2. Add pending publisher with:
   - **PyPI Project Name**: `preprimer`
   - **Owner**: `FOI-Bioinformatics`
   - **Repository name**: `preprimer`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `testpypi`

### 2. Configure GitHub Environments

**Create PyPI Production Environment:**

1. Go to repository Settings → Environments
2. Click "New environment"
3. Name: `pypi`
4. Add protection rules (recommended):
   - ✅ Required reviewers (optional but recommended)
   - ✅ Wait timer: 0 minutes
   - ✅ Deployment branches: Only protected branches and tags matching `v*.*.*`

**Create Test PyPI Environment (Optional):**

1. Name: `testpypi`
2. Same protection rules as production (optional)

### 3. Verify Workflow Permissions

Ensure the repository has the following permissions enabled:

1. Settings → Actions → General
2. Workflow permissions:
   - ✅ Read and write permissions
3. Allow GitHub Actions to create and approve pull requests (if needed)

## Release Process

### Standard Release (Recommended)

Follow the comprehensive checklist in `RELEASE_CHECKLIST.md`. Quick summary:

```bash
# 1. Update version and CHANGELOG
#    - Update version in preprimer/__init__.py
#    - Update CHANGELOG.md with [1.0.0] - 2024-10-14
#    - Commit changes

git add .
git commit -m "chore: Prepare release v1.0.0"

# 2. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0

Major features:
- Feature 1
- Feature 2
- Feature 3

See CHANGELOG.md for full details."

git push origin v1.0.0

# 3. Create GitHub Release
gh release create v1.0.0 \
  --title "PrePrimer v1.0.0 - Stable Release" \
  --notes-file RELEASE_NOTES.md

# 4. Monitor workflow
# Go to Actions tab and watch the publish workflow
# Verify all jobs pass: validate → build → publish → verify

# 5. Verify installation
pip install --upgrade preprimer
python -c "import preprimer; print(preprimer.__version__)"
```

### Emergency Patch Release

For critical bug fixes requiring quick release:

```bash
# 1. Create hotfix branch from tag
git checkout -b hotfix/v1.0.1 v1.0.0

# 2. Make fixes and test thoroughly
# ... fix code ...
python -m pytest

# 3. Update version and CHANGELOG
# Update to 1.0.1 in __init__.py and CHANGELOG.md

# 4. Commit and tag
git commit -am "fix: Critical bug fix"
git tag -a v1.0.1 -m "Hotfix release v1.0.1"
git push origin v1.0.1

# 5. Create release
gh release create v1.0.1 --title "PrePrimer v1.0.1 - Hotfix"
```

## Workflow Stages

### 1. Validate Release (Pre-checks)

**What it does:**
- Validates version tag format (v0.0.0)
- Runs full test suite with coverage check (≥95%)
- Runs security scans (bandit, safety)
- Verifies documentation files exist
- Confirms CHANGELOG entry for version

**Failure handling:**
- Workflow stops if any validation fails
- Fix issues and push new tag

### 2. Build Package

**What it does:**
- Cleans previous builds
- Builds source distribution (.tar.gz) and wheel (.whl)
- Verifies package contents and metadata
- Tests package installation in clean environment
- Calculates SHA256 checksums

**Outputs:**
- `dist/preprimer-X.Y.Z.tar.gz` - Source distribution
- `dist/preprimer-X.Y.Z-py3-none-any.whl` - Universal wheel
- `dist/SHA256SUMS` - Checksum file

### 3. Publish to Test PyPI (Optional)

**What it does:**
- Publishes to Test PyPI (https://test.pypi.org)
- Tests installation from Test PyPI
- Verifies package functionality

**When it runs:**
- Only on tag push (not GitHub releases)
- Useful for testing before production

**Skip if:**
- Package version already exists (uses `skip-existing: true`)

### 4. Publish to PyPI (Production)

**What it does:**
- Publishes to production PyPI (https://pypi.org)
- Creates release summary
- Uploads distribution files to GitHub release

**Security:**
- Uses OIDC Trusted Publishing (no API tokens)
- Requires GitHub environment approval (if configured)
- Only runs on protected tags/releases

### 5. Verify Publication

**What it does:**
- Waits for PyPI CDN propagation (2 minutes)
- Tests installation on Ubuntu and macOS
- Verifies with Python 3.11, 3.12, 3.13
- Runs smoke tests

**Success criteria:**
- Package installs successfully on all platforms
- All modules import correctly
- Core functionality works

### 6. Publication Summary

**What it does:**
- Generates comprehensive workflow summary
- Reports success/failure status
- Provides PyPI package URL

## Monitoring and Troubleshooting

### Check Workflow Status

```bash
# View recent workflow runs
gh run list --workflow=publish.yml

# Watch live workflow
gh run watch

# View logs for specific run
gh run view <run-id> --log
```

### Common Issues

#### Issue: "No CHANGELOG entry found"

**Cause:** CHANGELOG.md doesn't have entry for release version

**Fix:**
```bash
# Update CHANGELOG.md with [X.Y.Z] - YYYY-MM-DD section
git add CHANGELOG.md
git commit -m "docs: Update CHANGELOG for vX.Y.Z"
git tag -f vX.Y.Z  # Force update tag
git push origin vX.Y.Z --force
```

#### Issue: "Coverage below 95% threshold"

**Cause:** Test coverage dropped below required threshold

**Fix:**
```bash
# Run coverage locally
python -m pytest --cov=preprimer --cov-report=html

# Add missing tests
# ... add tests ...

# Verify coverage
python -m pytest --cov=preprimer
```

#### Issue: "PyPI publication failed - 403 Forbidden"

**Cause:** Trusted Publishing not configured or incorrect environment

**Fix:**
1. Verify PyPI Trusted Publishing configuration
2. Check GitHub environment name matches (`pypi`)
3. Ensure workflow filename matches (`publish.yml`)
4. Verify repository owner matches (`FOI-Bioinformatics`)

#### Issue: "Package already exists on PyPI"

**Cause:** Version number already published (PyPI doesn't allow overwrites)

**Fix:**
```bash
# Increment version number
# Edit preprimer/__init__.py: __version__ = "X.Y.Z+1"

# Create new tag
git tag -a vX.Y.Z+1 -m "Release vX.Y.Z+1"
git push origin vX.Y.Z+1
```

#### Issue: "Installation verification failed"

**Cause:** Package published but installation or imports failing

**Fix:**
1. Check package contents: `pip download preprimer && tar -tzf preprimer-*.tar.gz`
2. Verify MANIFEST.in includes all necessary files
3. Test local build: `python -m build && pip install dist/*.whl`
4. If critical: yank release and publish hotfix

### Yanking a Release

If a critical issue is discovered after publication:

```bash
# Yank release on PyPI (makes it unavailable but preserves record)
pip install twine
twine upload --repository pypi --skip-existing dist/*
# Then contact PyPI support or use web interface to yank

# Delete GitHub release
gh release delete vX.Y.Z

# Delete tag
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

## Testing the Workflow

### Test Locally Before Tag

```bash
# Run pre-release checks manually
python -m pytest tests/ --cov=preprimer --cov-report=term-missing -x

# Verify coverage
python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); print(f\"Coverage: {float(tree.getroot().attrib['line-rate']) * 100:.2f}%\")"

# Build package
python -m pip install build twine
python -m build

# Check package
python -m twine check dist/*

# Test installation
pip install dist/*.whl
python -c "import preprimer; print(preprimer.__version__)"
```

### Test with Test PyPI

```bash
# Create test tag
git tag -a v0.0.1-test -m "Test release"
git push origin v0.0.1-test

# Monitor workflow
gh run watch

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            preprimer

# Clean up test tag
git tag -d v0.0.1-test
git push origin :refs/tags/v0.0.1-test
```

## Manual Publication (Fallback)

If automated workflow fails, publish manually:

```bash
# 1. Build package
python -m build

# 2. Check package
python -m twine check dist/*

# 3. Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# 4. Test installation
pip install --index-url https://test.pypi.org/simple/ preprimer

# 5. Upload to PyPI
python -m twine upload dist/*
```

**Note:** Manual publication requires PyPI API token in `~/.pypirc`:

```ini
[pypi]
  username = __token__
  password = pypi-...your-token...

[testpypi]
  username = __token__
  password = pypi-...your-test-token...
```

## Best Practices

1. **Always use CHANGELOG**: Keep CHANGELOG.md updated before tagging
2. **Test before release**: Run full test suite locally
3. **Use semantic versioning**: Follow MAJOR.MINOR.PATCH strictly
4. **Create GitHub Release**: Use releases for better visibility and release notes
5. **Monitor workflow**: Watch the Actions tab during publication
6. **Verify installation**: Test installation on clean environment after publication
7. **Tag annotations**: Use `git tag -a` with descriptive messages
8. **Never force-push**: Don't force-push tags to main/release branches
9. **Document breaking changes**: Clearly mark breaking changes in CHANGELOG
10. **Security scans**: Review bandit and safety reports before release

## Automation Opportunities

Future improvements to consider:

- [ ] Automated version bumping based on commit messages
- [ ] Automated CHANGELOG generation from commits
- [ ] Automatic pre-release (beta, rc) publication
- [ ] Performance regression detection in CI
- [ ] Automated documentation deployment to Read the Docs
- [ ] Slack/Discord notifications for releases
- [ ] Automated dependency updates with Dependabot
- [ ] Release candidate testing period (e.g., 24-hour wait)

## Security Considerations

1. **Trusted Publishing**: More secure than API tokens
2. **OIDC Authentication**: No secrets stored in repository
3. **Environment protection**: Use protected environments for production
4. **Required reviews**: Consider requiring approval for releases
5. **Branch protection**: Protect main branch from direct pushes
6. **Tag protection**: Consider protecting version tags
7. **Security scans**: Automated bandit and safety checks
8. **Checksum verification**: SHA256SUMS for distribution integrity

## References

- [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

---

**Last Updated**: 2024-10-14
**Workflow Version**: publish.yml v1.0
