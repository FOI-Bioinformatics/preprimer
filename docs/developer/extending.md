# Extending PrePrimer

Guide for extending PrePrimer with new formats, features, and functionality.

## Architecture Overview

PrePrimer's plugin-based architecture enables straightforward extension through:
- **Parser Registry**: Automatic discovery of new input format parsers
- **Writer Registry**: Automatic discovery of new output format writers  
- **Standardized Interfaces**: Consistent patterns for implementation
- **Configuration System**: Flexible configuration for new features

## Adding New Input Formats

### Step 1: Implement Parser Class

Create a new parser in `preprimer/parsers/your_format_parser.py`:

```python
"""Parser for YourFormat primer scheme format."""

import logging
from pathlib import Path
from typing import Dict, List, Union

from ..core.exceptions import ParserError, InvalidFormatError
from ..core.interfaces import AmpliconData, PrimerData
from ..core.standardized_parser import StandardizedParser

logger = logging.getLogger(__name__)


class YourFormatParser(StandardizedParser):
    """Parser for YourFormat primer scheme files."""

    @classmethod
    def format_name(cls) -> str:
        """Return unique format identifier."""
        return "your_format"

    @classmethod
    def file_extensions(cls) -> List[str]:
        """Return supported file extensions."""
        return [".yf", ".yourformat"]

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate file format without full parsing."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Check file header or format markers
                header = f.readline().strip()
                return header.startswith("# YourFormat v")
        except Exception:
            return False

    def _parse_file_content(self, file_path: Path, prefix: str) -> Dict[str, AmpliconData]:
        """Parse YourFormat file content."""
        amplicons = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip header
                while True:
                    line = f.readline()
                    if not line.startswith('#'):
                        break
                
                # Parse data lines
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse line according to YourFormat specification
                    fields = line.split('\t')
                    if len(fields) < 6:  # Minimum required fields
                        logger.warning(f"Insufficient fields in line {line_num}")
                        continue
                    
                    # Extract required fields
                    amplicon_name = self._sanitize_string_field(fields[0], "amplicon_name", line_num, 100)
                    primer_name = self._sanitize_string_field(fields[1], "primer_name", line_num, 100) 
                    sequence = self._sanitize_string_field(fields[2], "sequence", line_num, 1000)
                    start_pos = self._validate_numeric_field(fields[3], "start", line_num, int, min_value=0)
                    stop_pos = self._validate_numeric_field(fields[4], "stop", line_num, int, min_value=0)
                    pool_num = self._validate_numeric_field(fields[5], "pool", line_num, int, min_value=1)
                    
                    # Determine primer direction
                    direction = "forward" if primer_name.endswith("_F") else "reverse"
                    strand = "+" if direction == "forward" else "-"
                    
                    # Create primer data
                    primer = self._create_primer_data(
                        name=primer_name,
                        sequence=sequence,
                        start=start_pos,
                        stop=stop_pos,
                        strand=strand,
                        direction=direction,
                        pool=pool_num,
                        amplicon_id=amplicon_name,
                        reference_id=prefix or "unknown"
                    )
                    
                    # Group primers by amplicon
                    if amplicon_name not in amplicons:
                        amplicons[amplicon_name] = AmpliconData(
                            amplicon_id=amplicon_name,
                            primers=[],
                            length=0,  # Will be calculated
                            reference_id=prefix or "unknown"
                        )
                    
                    amplicons[amplicon_name].primers.append(primer)
                
                # Calculate amplicon lengths
                for amplicon in amplicons.values():
                    if amplicon.primers:
                        starts = [p.start for p in amplicon.primers]
                        stops = [p.stop for p in amplicon.primers]
                        amplicon.length = max(stops) - min(starts)
                        
        except Exception as e:
            raise ParserError(f"Failed to parse YourFormat file {file_path}: {e}")
        
        if not amplicons:
            raise InvalidFormatError(
                str(file_path),
                expected_format="YourFormat",
                user_message="No valid primer data found in file."
            )
        
        return amplicons
```

### Step 2: Register Parser

Add import to `preprimer/parsers/__init__.py`:

```python
# Existing imports...
from .your_format_parser import YourFormatParser

# Parser will be automatically registered on import
```

### Step 3: Add Comprehensive Tests

Create `tests/test_your_format_parser.py`:

```python
"""Tests for YourFormat parser."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from preprimer.parsers.your_format_parser import YourFormatParser
from preprimer.core.exceptions import ParserError, InvalidFormatError


class TestYourFormatParser:
    """Test YourFormat parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = YourFormatParser()
    
    def test_format_identification(self):
        """Test format name and extensions."""
        assert self.parser.format_name() == "your_format"
        assert ".yf" in self.parser.file_extensions()
        assert ".yourformat" in self.parser.file_extensions()
    
    def test_valid_file_parsing(self, tmp_path):
        """Test parsing valid YourFormat file."""
        test_data = """# YourFormat v1.0
amplicon_1\tprimer_1_F\tATCGATCGATCGATCG\t100\t116\t1
amplicon_1\tprimer_1_R\tCGATCGATCGATCGAT\t300\t316\t1
"""
        test_file = tmp_path / "test.yf"
        test_file.write_text(test_data)
        
        amplicons = self.parser.parse(test_file, prefix="test")
        
        assert len(amplicons) == 1
        assert "amplicon_1" in amplicons
        assert len(amplicons["amplicon_1"].primers) == 2
    
    def test_file_validation(self, tmp_path):
        """Test file format validation."""
        # Valid file
        valid_file = tmp_path / "valid.yf"
        valid_file.write_text("# YourFormat v1.0\ndata...")
        assert self.parser.validate_file(valid_file)
        
        # Invalid file
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("Not a YourFormat file")
        assert not self.parser.validate_file(invalid_file)
    
    def test_error_handling(self, tmp_path):
        """Test error handling for malformed files."""
        malformed_file = tmp_path / "malformed.yf" 
        malformed_file.write_text("# YourFormat v1.0\nincomplete_data")
        
        with pytest.raises(InvalidFormatError):
            self.parser.parse(malformed_file)
    
    def test_security_validation(self, tmp_path):
        """Test security validation."""
        # Test oversized content
        large_content = "# YourFormat v1.0\n" + "x" * 10000000
        large_file = tmp_path / "large.yf"
        large_file.write_text(large_content)
        
        # Should handle large files appropriately
        with pytest.raises(ParserError):
            self.parser.parse(large_file)
```

## Adding New Output Formats

### Step 1: Implement Writer Class

Create `preprimer/writers/your_format_writer.py`:

```python
"""Writer for YourFormat output."""

import logging
from pathlib import Path
from typing import List, Optional

from ..core.interfaces import AmpliconData, OutputWriter

logger = logging.getLogger(__name__)


class YourFormatWriter(OutputWriter):
    """Writer for YourFormat output files."""

    @classmethod
    def format_name(cls) -> str:
        """Return format identifier."""
        return "your_format"

    @classmethod
    def file_extensions(cls) -> List[str]:
        """Return output file extensions."""
        return [".yf"]

    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Path,
        reference_id: Optional[str] = None,
        **kwargs
    ) -> Path:
        """Write amplicon data to YourFormat file."""
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# YourFormat v1.0\n")
                f.write(f"# Reference: {reference_id or 'unknown'}\n")
                f.write("# Amplicon\tPrimer\tSequence\tStart\tStop\tPool\n")
                
                # Write primer data
                for amplicon in sorted(amplicons, key=lambda a: a.amplicon_id):
                    for primer in sorted(amplicon.primers, key=lambda p: p.start):
                        fields = [
                            amplicon.amplicon_id,
                            primer.name,
                            primer.sequence,
                            str(primer.start),
                            str(primer.stop),
                            str(primer.pool)
                        ]
                        f.write('\t'.join(fields) + '\n')
                        
        except Exception as e:
            logger.error(f"Failed to write YourFormat file {output_path}: {e}")
            raise
        
        logger.info(f"Successfully wrote YourFormat file: {output_path}")
        return output_path

    def validate_output(self, output_path: Path) -> bool:
        """Validate generated output file."""
        if not output_path.exists():
            return False
            
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line.startswith("# YourFormat")
        except Exception:
            return False
```

### Step 2: Register Writer

Add import to `preprimer/writers/__init__.py`:

```python
# Existing imports...
from .your_format_writer import YourFormatWriter

# Writer will be automatically registered on import
```

### Step 3: Add Writer Tests

Add tests to existing writer test suite or create dedicated test file:

```python
"""Tests for YourFormat writer."""

import pytest
from pathlib import Path

from preprimer.writers.your_format_writer import YourFormatWriter
from preprimer.core.interfaces import AmpliconData, PrimerData


class TestYourFormatWriter:
    """Test YourFormat writer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.writer = YourFormatWriter()
    
    def test_write_amplicon_data(self, tmp_path):
        """Test writing amplicon data to YourFormat."""
        # Create test data
        primer1 = PrimerData(
            name="test_primer_F",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
            reference_id="test_ref"
        )
        
        amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[primer1],
            length=200,
            reference_id="test_ref"
        )
        
        # Write to file
        output_file = tmp_path / "output.yf"
        result_path = self.writer.write([amplicon], output_file)
        
        # Verify output
        assert result_path.exists()
        content = result_path.read_text()
        assert "# YourFormat v1.0" in content
        assert "test_amplicon" in content
        assert "test_primer_F" in content
        
    def test_output_validation(self, tmp_path):
        """Test output file validation."""
        # Valid output
        valid_file = tmp_path / "valid.yf"
        valid_file.write_text("# YourFormat v1.0\ndata...")
        assert self.writer.validate_output(valid_file)
        
        # Invalid output  
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("Not YourFormat")
        assert not self.writer.validate_output(invalid_file)
```

## Adding Configuration Options

### Step 1: Define Configuration Schema

Add configuration options in `preprimer/core/enhanced_config.py`:

```python
# Add to configuration schema
YOUR_FORMAT_CONFIG_SCHEMA = {
    "your_format": {
        "include_metadata": True,
        "coordinate_system": "1-based",  # or "0-based"
        "precision": 2,
        "custom_headers": []
    }
}

# Merge with main configuration schema
CONFIG_SCHEMA.update(YOUR_FORMAT_CONFIG_SCHEMA)
```

### Step 2: Use Configuration in Implementation

```python
class YourFormatWriter(OutputWriter):
    def write(self, amplicons: List[AmpliconData], output_path: Path, **kwargs) -> Path:
        # Get configuration
        config = kwargs.get('config', {})
        your_format_config = config.get('your_format', {})
        
        include_metadata = your_format_config.get('include_metadata', True)
        coordinate_system = your_format_config.get('coordinate_system', '1-based')
        
        # Use configuration in implementation
        if coordinate_system == "0-based":
            # Convert coordinates to 0-based
            pass
```

### Step 3: Document Configuration

Update configuration documentation with new options:

```markdown
## YourFormat Configuration

Configure YourFormat-specific options:

```yaml
your_format:
  include_metadata: true      # Include metadata in output
  coordinate_system: "1-based"  # Coordinate system (1-based or 0-based)  
  precision: 2               # Decimal precision for scores
  custom_headers:            # Additional header lines
    - "# Custom header 1"
    - "# Custom header 2"
```
```

## Adding New Features

### Step 1: Feature Design
1. **Requirements Analysis**: Define feature requirements and constraints
2. **Interface Design**: Design clean, consistent interfaces
3. **Implementation Plan**: Plan implementation approach and testing strategy

### Step 2: Implementation Pattern
```python
# Follow established patterns
class NewFeature:
    """New feature with comprehensive documentation."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration validation."""
        self._config = self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration."""
        # Configuration validation logic
        return config
    
    def process(self, data: Any) -> Any:
        """Process data with proper error handling."""
        try:
            # Feature implementation
            return self._process_internal(data)
        except Exception as e:
            logger.error(f"Feature processing failed: {e}")
            raise
    
    def _process_internal(self, data: Any) -> Any:
        """Internal processing logic."""
        # Implementation details
        pass
```

### Step 3: Testing Strategy
```python
class TestNewFeature:
    """Comprehensive test suite for new feature."""
    
    def test_normal_operation(self):
        """Test normal operation."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        pass
    
    def test_error_handling(self):
        """Test error handling."""
        pass
    
    def test_configuration(self):
        """Test configuration validation."""
        pass
    
    def test_integration(self):
        """Test integration with existing components."""
        pass
```

## Performance Considerations

### Optimization Guidelines
1. **Profile First**: Use profiling to identify bottlenecks
2. **Cache Appropriately**: Cache expensive computations
3. **Batch Operations**: Process data in batches when possible
4. **Memory Management**: Clean up resources explicitly

### Performance Testing
```python
def test_performance_benchmark(benchmark):
    """Benchmark new functionality."""
    result = benchmark(new_feature.process, test_data)
    assert result.is_valid()
    
    # Performance assertions
    assert benchmark.stats.mean < 0.001  # Sub-millisecond performance
```

## Documentation Requirements

### Code Documentation
- **Module docstrings**: Purpose and functionality
- **Class docstrings**: Usage patterns and behavior
- **Method docstrings**: Parameters, returns, exceptions, examples

### User Documentation
- **Feature descriptions**: Clear explanation of functionality
- **Usage examples**: Practical usage scenarios
- **Configuration options**: Available settings and defaults
- **Migration guides**: For breaking changes

### Developer Documentation
- **Architecture impact**: How feature fits into system
- **Extension points**: How others can extend the feature
- **Testing approach**: Testing strategy and validation

## Integration Testing

### End-to-End Testing
```python
def test_new_format_integration(tmp_path):
    """Test complete workflow with new format."""
    # Create test input
    input_file = create_test_file(tmp_path, "your_format")
    
    # Test conversion workflow
    converter = PrimerConverter()
    results = converter.convert(
        input_file=input_file,
        output_dir=tmp_path / "output",
        output_formats=["artic", "fasta", "your_format"],
        prefix="test"
    )
    
    # Validate all outputs
    assert "your_format" in results
    assert results["your_format"].exists()
    
    # Test round-trip conversion
    round_trip = converter.convert(
        input_file=results["your_format"],
        output_dir=tmp_path / "round_trip",
        output_formats=["your_format"],
        prefix="test"
    )
    
    # Validate data integrity
    validate_data_integrity(input_file, round_trip["your_format"])
```

### CI/CD Integration
Ensure new functionality works in CI/CD pipeline:
- **Automated Testing**: All tests pass in CI environment
- **Performance Validation**: No significant regressions
- **Security Scanning**: Security tools validate new code
- **Documentation Building**: Documentation builds successfully

## Best Practices Summary

1. **Follow Established Patterns**: Use existing interfaces and patterns
2. **Comprehensive Testing**: Include unit, integration, and property-based tests
3. **Security First**: Use security utilities for all file operations
4. **Performance Aware**: Profile and benchmark performance-critical code
5. **Document Thoroughly**: Provide complete documentation for users and developers
6. **Error Handling**: Implement robust error handling with informative messages
7. **Configuration Support**: Make behavior configurable where appropriate
8. **Backward Compatibility**: Maintain compatibility with existing functionality

By following these guidelines, you can successfully extend PrePrimer while maintaining its high standards for quality, security, and performance.