# Contributing Guide

Guidelines and procedures for contributing to PrePrimer development.

## Development Environment Setup

### Prerequisites
- Python 3.11 or later
- Git version control
- Virtual environment support

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Create virtual environment
python3 -m venv preprimer-dev
source preprimer-dev/bin/activate  # Linux/macOS
# preprimer-dev\Scripts\activate  # Windows (WSL recommended)

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Verify Installation
```bash
# Run test suite
python -m pytest

# Check code formatting
pre-commit run --all-files

# Verify package installation
python -c "import preprimer; print('Installation successful')"
```

## Development Workflow

### Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch for features  
- **feature/**: Individual feature development
- **bugfix/**: Bug fix branches

### Feature Development Process
1. **Create Branch**: `git checkout -b feature/your-feature-name`
2. **Develop**: Implement feature with tests
3. **Test**: Ensure all tests pass
4. **Document**: Update relevant documentation
5. **Review**: Submit pull request for review
6. **Merge**: Merge after approval and CI success

### Commit Guidelines
Follow conventional commit format:
```
type(scope): description

feat(parser): add new format parser for Format X
fix(security): resolve path traversal vulnerability  
docs(api): update API documentation for new methods
test(integration): add end-to-end workflow tests
```

**Commit Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements

## Code Standards

### Code Quality Requirements
All code must pass:
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **mypy**: Type checking
- **pytest**: Test suite (>95% coverage)

### Pre-commit Validation
```bash
# Run all pre-commit checks
pre-commit run --all-files

# Individual checks
black --check preprimer/ tests/
isort --check-only preprimer/ tests/  
flake8 preprimer/ tests/
mypy preprimer/ --ignore-missing-imports
```

### Code Structure Standards
```python
"""Module docstring describing purpose and functionality."""

import standard_library
import third_party_library

from preprimer.core import interfaces
from preprimer.core.security import PathValidator

logger = logging.getLogger(__name__)


class ExampleClass(interfaces.BaseInterface):
    """Class docstring describing purpose and usage.
    
    Args:
        param: Parameter description with type information
        
    Returns:
        Return value description with type information
        
    Raises:
        SpecificError: Description of when this error occurs
    """
    
    def __init__(self, param: str) -> None:
        """Initialize with proper type hints."""
        self._param = param
    
    def public_method(self, input_data: str) -> bool:
        """Public method with comprehensive documentation."""
        # Implementation with proper error handling
        try:
            result = self._private_method(input_data)
            return result
        except Exception as e:
            logger.error(f"Error in public_method: {e}")
            raise
    
    def _private_method(self, data: str) -> bool:
        """Private method for internal operations."""
        return bool(data)
```

## Testing Requirements

### Test Coverage Standards
- **Minimum Coverage**: 95% line coverage
- **Test Types**: Unit, integration, property-based, security
- **Error Handling**: All exception paths tested
- **Edge Cases**: Boundary conditions validated

### Test Structure
```python
"""Test module following naming convention test_<module>.py"""

import pytest
from hypothesis import given, strategies as st

from preprimer.module import ClassUnderTest
from preprimer.core.exceptions import ExpectedError


class TestClassUnderTest:
    """Test class mirroring production class structure."""
    
    def test_normal_operation(self):
        """Test normal operation with valid inputs."""
        instance = ClassUnderTest("valid_input")
        result = instance.process()
        assert result.is_valid()
    
    def test_error_handling(self):
        """Test proper error handling for invalid inputs."""
        instance = ClassUnderTest("invalid_input")
        with pytest.raises(ExpectedError, match="Expected error message"):
            instance.process()
    
    @given(st.text(min_size=1, max_size=100))
    def test_property_based(self, random_text):
        """Property-based test with random inputs."""
        instance = ClassUnderTest(random_text)
        # Test invariant properties that should always hold
        assert len(instance.get_processed()) >= 0
    
    def test_integration_workflow(self, tmp_path):
        """Integration test with temporary files."""
        test_file = tmp_path / "test_data.txt" 
        test_file.write_text("test content")
        
        instance = ClassUnderTest(str(test_file))
        result = instance.process_file()
        assert result.success
```

### Running Tests
```bash
# Complete test suite
python -m pytest

# Specific test categories  
python -m pytest tests/test_security.py -v
python -m pytest tests/test_integration.py -v

# Coverage report
python -m pytest --cov=preprimer --cov-report=html

# Performance benchmarks
python -m pytest tests/test_benchmarks.py --benchmark-only
```

## Adding New Functionality

### Adding New Parsers
1. **Create Parser File**: `preprimer/parsers/new_format_parser.py`
2. **Implement Interface**:
```python
from preprimer.core.standardized_parser import StandardizedParser

class NewFormatParser(StandardizedParser):
    @classmethod
    def format_name(cls) -> str:
        return "new_format"
    
    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".new", ".nfmt"]
    
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        # Format validation logic
        
    def _parse_file_content(self, file_path: Path, prefix: str) -> Dict[str, AmpliconData]:
        # Parsing implementation
```

3. **Register Parser**: Import in `preprimer/parsers/__init__.py`
4. **Add Tests**: Create `tests/test_new_format_parser.py`
5. **Add Documentation**: Update format documentation

### Adding New Writers
1. **Create Writer File**: `preprimer/writers/new_format_writer.py`
2. **Implement Interface**:
```python
from preprimer.core.interfaces import OutputWriter

class NewFormatWriter(OutputWriter):
    @classmethod
    def format_name(cls) -> str:
        return "new_format"
    
    def write(self, amplicons: List[AmpliconData], output_path: Path, **kwargs) -> Path:
        # Writing implementation
```

3. **Register Writer**: Import in `preprimer/writers/__init__.py`
4. **Add Tests**: Include in writer test suite
5. **Update Documentation**: Document output format

## Security Considerations

### Security Requirements
All file operations must use security utilities:

```python
from preprimer.core.security import PathValidator, InputValidator

# Always validate paths
safe_path = PathValidator.sanitize_path(user_input)

# Validate file content
validated_content = InputValidator.validate_file_content(content)

# Use secure file operations
with SecurityUtils.create_temp_file() as tmp_file:
    # File operations
```

### Security Testing
Add security tests for new functionality:

```python
def test_security_validation(self):
    """Test security validation for new functionality."""
    # Test path traversal prevention
    with pytest.raises(SecurityError):
        NewClass.process_path("../../../etc/passwd")
    
    # Test input size limits
    with pytest.raises(SecurityError):
        NewClass.process_content("x" * 1000000)  # Too large
```

## Documentation Standards

### Code Documentation
- **Module docstrings**: Purpose and functionality
- **Class docstrings**: Usage and behavior  
- **Method docstrings**: Parameters, returns, exceptions
- **Type hints**: All public interfaces

### External Documentation
When adding new features, update:
- **README.md**: If user-facing changes
- **User guides**: For new CLI options or workflows
- **API documentation**: For new programmatic interfaces
- **Architecture documentation**: For structural changes

## Pull Request Process

### Before Submitting
1. **Tests Pass**: All 226 tests must pass
2. **Coverage Maintained**: >95% coverage requirement
3. **Code Quality**: All pre-commit checks pass
4. **Documentation**: Relevant docs updated
5. **Performance**: No significant performance regressions

### Pull Request Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Coverage maintained >95%

## Documentation  
- [ ] Updated relevant documentation
- [ ] Added docstrings for new code
- [ ] Updated API documentation if needed

## Performance
- [ ] No performance regressions
- [ ] Added benchmarks if relevant
```

### Review Process
1. **Automated Checks**: CI/CD pipeline validation
2. **Code Review**: Maintainer review for quality and design
3. **Testing**: Comprehensive test validation
4. **Documentation Review**: Documentation accuracy and completeness
5. **Approval**: Maintainer approval required for merge

## Release Process

### Version Management
- **Semantic Versioning**: MAJOR.MINOR.PATCH format
- **Version Updates**: Update in `__init__.py` and `pyproject.toml`
- **Changelog**: Maintain detailed changelog

### Release Checklist
1. **Version Bump**: Update version numbers
2. **Changelog**: Update with new features and fixes
3. **Tests**: Full test suite validation
4. **Documentation**: Update version-specific documentation
5. **Tag**: Create git tag for release
6. **Build**: Generate distribution packages
7. **Deploy**: Release to package repositories

## Getting Help

### Communication Channels
- **Issues**: GitHub issues for bugs and feature requests
- **Discussions**: GitHub discussions for questions
- **Email**: Project maintainers for security issues

### Documentation Resources
- **Architecture Guide**: Understanding system design
- **API Documentation**: Programmatic interface reference
- **User Guides**: End-user functionality
- **Testing Guide**: Comprehensive testing information

### Common Issues
- **Environment Setup**: Virtual environment configuration
- **Dependency Conflicts**: Package version management
- **Test Failures**: Debugging test issues
- **Performance**: Optimization strategies

## Code of Conduct

### Expected Behavior
- **Respectful Communication**: Professional and courteous interaction
- **Constructive Feedback**: Focus on code improvement, not personal criticism
- **Collaboration**: Willingness to help and learn from others
- **Quality Focus**: Commitment to high-quality code and documentation

### Unacceptable Behavior
- Personal attacks or harassment
- Discriminatory language or behavior
- Spam or off-topic contributions
- Violation of project guidelines

### Reporting Issues
Report code of conduct violations to project maintainers through private communication channels.

---

Thank you for contributing to PrePrimer! Your contributions help improve primer scheme conversion for the scientific community.