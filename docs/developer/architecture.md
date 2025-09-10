# Architecture Overview

PrePrimer implements a plugin-based architecture designed for extensibility, maintainability, and performance in primer scheme format conversion.

## System Architecture

### High-Level Design
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Files   │───▶│  Format Parser   │───▶│ Standardized    │
│ (VarVAMP/ARTIC/ │    │    Registry      │    │ Data Model      │
│    Olivar)      │    └──────────────────┘    └─────────────────┘
└─────────────────┘                                      │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Output Files   │◀───│  Format Writer   │◀───│   Converter     │
│ (Multiple       │    │    Registry      │    │    Engine       │
│  Formats)       │    └──────────────────┘    └─────────────────┘
└─────────────────┘
```

### Core Components

#### 1. Plugin Registry System
**File**: `preprimer/core/registry.py`

The registry system enables dynamic parser and writer discovery:

```python
from preprimer.core.registry import parser_registry, writer_registry

# Automatic registration on import
class VarVAMPParser(PrimerParser):
    @classmethod
    def format_name(cls) -> str:
        return "varvamp"

# Registry automatically discovers and registers parsers
parser = parser_registry.get("varvamp")
```

**Features:**
- Automatic plugin discovery and registration
- O(1) lookup performance for parsers and writers
- Runtime plugin loading capability
- Type safety through abstract base classes

#### 2. Standardized Data Model
**File**: `preprimer/core/interfaces.py`

Common data structures ensure consistency across formats:

```python
@dataclass
class PrimerData:
    name: str
    sequence: str
    start: int
    stop: int
    strand: str
    direction: str
    pool: int
    amplicon_id: str
    reference_id: str
    gc_content: Optional[float] = None
    tm: Optional[float] = None
    score: Optional[float] = None

@dataclass  
class AmpliconData:
    amplicon_id: str
    primers: List[PrimerData]
    length: int
    reference_id: str
```

#### 3. Security Layer
**File**: `preprimer/core/security.py`

Comprehensive security validation for all file operations:

```python
# Path validation and sanitization
safe_path = PathValidator.sanitize_path(user_input)

# Input validation with size limits  
validated_content = InputValidator.validate_file_content(content, max_size_mb=10)

# Safe file operations with automatic cleanup
with SecurityUtils.create_temp_file() as tmp_file:
    process_data(tmp_file)
```

#### 4. Configuration Management
**File**: `preprimer/core/enhanced_config.py`

Flexible configuration supporting multiple sources:

```python
# Configuration from multiple sources
config = EnhancedConfigManager.from_file("config.yaml")
config.update_from_env()  # Environment variables
config.merge_with_dict({"custom": "values"})
```

## Parser Architecture

### Abstract Base Class
**File**: `preprimer/core/interfaces.py`

```python
class PrimerParser(ABC):
    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Return format identifier (e.g., 'varvamp')."""
        
    @classmethod  
    @abstractmethod
    def file_extensions(cls) -> List[str]:
        """Return supported file extensions."""
        
    @abstractmethod
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate file format without parsing."""
        
    @abstractmethod
    def parse(self, file_path: Union[str, Path], prefix: str = "") -> List[AmpliconData]:
        """Parse file and return amplicon data."""
```

### Parser Implementation Pattern
Each parser inherits from `StandardizedParser` for common functionality:

```python
class VarVAMPParser(StandardizedParser):
    @classmethod
    def format_name(cls) -> str:
        return "varvamp"
        
    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".tsv", ".txt"]
        
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        # Format-specific validation logic
        
    def _parse_file_content(self, file_path: Path, prefix: str) -> Dict[str, AmpliconData]:
        # Format-specific parsing logic
```

### Standardized Parser Base
**File**: `preprimer/core/standardized_parser.py`

Provides common functionality:
- Security validation (path sanitization, input validation)
- Error handling with context
- Logging and monitoring
- Performance optimization utilities

## Writer Architecture

### Writer Implementation Pattern
```python
class ARTICWriter(OutputWriter):
    @classmethod
    def format_name(cls) -> str:
        return "artic"
        
    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".scheme.bed"]
        
    def write(self, amplicons: List[AmpliconData], output_path: Path, **kwargs) -> Path:
        # Format-specific writing logic
```

## Conversion Engine

### Main Converter
**File**: `preprimer/core/converter.py`

Orchestrates the conversion process:

```python
class PrimerConverter:
    def convert(
        self,
        input_file: Path,
        output_dir: Path,
        output_formats: List[str],
        prefix: str = "",
        force: bool = False
    ) -> Dict[str, Path]:
        # 1. Auto-detect input format
        # 2. Parse input file  
        # 3. Convert to requested formats
        # 4. Validate outputs
        # 5. Return output file paths
```

**Process Flow:**
1. **Format Detection**: Automatic input format identification
2. **Security Validation**: Path and content security checks
3. **Parsing**: Format-specific parsing to standardized data model
4. **Conversion**: Data model to output format transformation
5. **Validation**: Output format and data integrity validation
6. **Cleanup**: Temporary resource cleanup

## Error Handling Architecture

### Exception Hierarchy
**File**: `preprimer/core/exceptions.py`

```python
class PrePrimerError(Exception):
    """Base exception for all PrePrimer errors."""

class ParserError(PrePrimerError):
    """Errors during file parsing."""
    
class SecurityError(PrePrimerError):
    """Security validation failures."""
    
class InvalidFormatError(ParserError):
    """Invalid or unsupported file format."""
```

### Error Context
Comprehensive error context for debugging:

```python
with ErrorContext("parsing VarVAMP file"):
    try:
        # File parsing operations
    except Exception as e:
        # Automatic context enrichment
        raise ParserError(f"Failed parsing: {e}") from e
```

## Performance Architecture

### Optimization Strategies
1. **Lazy Loading**: Parsers and writers loaded on demand
2. **Caching**: LRU caching for repeated operations  
3. **Batch Processing**: Efficient handling of large datasets
4. **Memory Management**: Automatic cleanup and resource management

### Performance Monitoring
**File**: `preprimer/core/optimized_parser.py`

```python
class OptimizedParser(StandardizedParser):
    def get_performance_stats(self) -> Dict[str, Any]:
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses)
        }
```

## Testing Architecture Integration

### Test Structure Alignment
```python
# Tests mirror architecture components
tests/
├── test_core_interfaces.py      # Data model validation
├── test_core_registry.py        # Plugin system testing  
├── test_security.py            # Security layer validation
├── test_parsers/               # Parser-specific tests
├── test_writers/              # Writer-specific tests
└── test_integration.py        # End-to-end workflow testing
```

### Architecture Validation
- **Interface compliance**: All parsers implement required methods
- **Plugin registration**: Automatic discovery and registration testing
- **Data model consistency**: Cross-format data integrity validation
- **Security integration**: All file operations use security layer

## Extension Points

### Adding New Parsers
1. Inherit from `StandardizedParser`
2. Implement required abstract methods
3. Import in `__init__.py` for automatic registration
4. Add comprehensive tests

### Adding New Writers  
1. Inherit from `OutputWriter`
2. Implement format-specific writing logic
3. Register through import system
4. Validate output format compliance

### Configuration Extensions
1. Add configuration schema definitions
2. Update environment variable mapping
3. Implement validation logic
4. Document configuration options

## Design Principles

### 1. Separation of Concerns
- **Parsing**: Format-specific input handling
- **Conversion**: Data model transformation
- **Writing**: Format-specific output generation
- **Security**: Cross-cutting security validation

### 2. Extensibility
- **Plugin Architecture**: Easy addition of new formats
- **Abstract Interfaces**: Clear extension contracts
- **Configuration System**: Flexible behavior customization

### 3. Reliability
- **Comprehensive Testing**: 226 tests across all components
- **Error Handling**: Graceful failure with informative messages
- **Security**: Input validation and safe file operations
- **Performance**: Benchmarked and optimized critical paths

### 4. Maintainability
- **Clear Interfaces**: Well-defined component boundaries
- **Documentation**: Comprehensive code and architecture documentation
- **Testing**: High test coverage enables safe refactoring
- **Modular Design**: Independent components with minimal coupling

This architecture enables PrePrimer to serve as a robust, extensible platform for primer scheme format conversion while maintaining high performance and security standards.