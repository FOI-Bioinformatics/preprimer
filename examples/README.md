# PrePrimer Examples

Practical, runnable code examples demonstrating common PrePrimer use cases.

## Quick Start

```bash
# Navigate to examples directory
cd examples/

# Run any example
python basic_conversion.py
python batch_processing.py
python topology_handling.py
python quality_filtering.py
python error_handling.py
```

## Available Examples

### 1. Basic Conversion (`basic_conversion.py`)

**What it does:**
- Simple format conversion from VarVAMP to ARTIC
- Shows minimal code required for conversion
- Demonstrates output structure

**Best for:**
- First-time users
- Simple one-off conversions
- Understanding basic workflow

**Usage:**
```bash
python basic_conversion.py
```

**Key concepts:**
- `Converter` class usage
- Input/output specification
- Format detection

---

### 2. Batch Processing (`batch_processing.py`)

**What it does:**
- Process multiple primer scheme files
- Convert to multiple output formats simultaneously
- Progress tracking and error handling
- Summary statistics

**Best for:**
- Large-scale conversions
- Processing entire directories
- Production workflows

**Usage:**
```bash
# Create input directory with primer files
mkdir input_schemes
cp your_files/*.tsv input_schemes/

# Run batch processing
python batch_processing.py
```

**Key concepts:**
- Batch file processing
- Error handling in loops
- Success/failure tracking
- Directory management

---

### 3. Topology Handling (`topology_handling.py`)

**What it does:**
- Detect circular vs. linear genome topology
- Handle cross-origin amplicons (circular genomes)
- Calculate accurate amplicon lengths for wrapping coordinates
- Analyze mitochondrial/plasmid primer schemes

**Best for:**
- Mitochondrial DNA primers
- Plasmid designs
- Viral episomes
- Any circular genome

**Usage:**
```bash
python topology_handling.py
```

**Key concepts:**
- Topology detection
- Circular coordinate wrapping
- Cross-origin amplicon analysis
- Length calculations for circular genomes

**Example output:**
```
Cross-Origin Amplicons (2):

NC_012920.1_1:
  Coordinates:      16,400 → 200
  Wraps origin:     YES ⟲
  Reported length:  370 bp
  Actual length:    370 bp
  Calculation:      (16569 - 16400) + 200 + 1 = 370
```

---

### 4. Quality Filtering (`quality_filtering.py`)

**What it does:**
- Filter primers by GC content
- Filter by melting temperature (Tm)
- Filter by primer length
- Detect degenerate primers
- Generate quality statistics
- Save filtered results

**Best for:**
- Quality control
- Primer optimization
- Removing problematic primers
- Pre-processing for downstream analysis

**Usage:**
```bash
python quality_filtering.py
```

**Quality criteria (customizable):**
- GC content: 35-65%
- Tm: 57-63°C
- Length: 20-28 bp

**Key concepts:**
- Primer filtering
- Quality metrics
- Statistical analysis
- Degenerate nucleotide detection

---

### 5. Error Handling (`error_handling.py`)

**What it does:**
- Demonstrate comprehensive error handling
- Show all error types and their handling
- Provide detailed error reports
- Suggest recovery actions

**Best for:**
- Building robust applications
- Understanding error types
- Implementing error recovery
- Production-grade code

**Usage:**
```bash
python error_handling.py
```

**Error categories covered:**
- Security errors (path traversal, file size)
- Format validation errors
- Data corruption errors
- Parsing errors
- System errors (file not found, permissions)

**Key concepts:**
- Exception hierarchy
- Error categorization
- Detailed error reporting
- Recovery suggestions
- Graceful degradation

---

## Common Patterns

### Pattern 1: Simple Conversion

```python
from preprimer.core.converter import Converter

converter = Converter()
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic", "fasta"],
    prefix="MyScheme"
)
```

### Pattern 2: Parse and Manipulate

```python
from preprimer.parsers import VarVAMPParser

parser = VarVAMPParser()
amplicons = parser.parse("primers.tsv", prefix="ref")

# Filter, modify, or analyze amplicons
filtered = [a for a in amplicons if a.length >= 350 and a.length <= 450]
```

### Pattern 3: Write Custom Output

```python
from preprimer.writers import ARTICWriter

writer = ARTICWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/",
    prefix="scheme",
    metadata={"schemeversion": "v1.0.0"}
)
```

### Pattern 4: Robust Error Handling

```python
from preprimer.core.exceptions import PrePrimerError

try:
    amplicons = converter.convert(...)
except PrePrimerError as e:
    print(f"Error: {e.user_message}")
    for suggestion in e.suggestions:
        print(f"  - {suggestion}")
```

## Customizing Examples

All examples use placeholder file paths that you can customize:

```python
# Update these paths in any example
input_file = "path/to/your/primers.tsv"
output_dir = "path/to/output/"
```

For testing, use the included test data:

```python
input_file = "tests/test_data/datasets/small/primers.tsv"  # Small COVID-19 dataset
input_file = "tests/test_data/datasets/medium/primers.tsv"  # Medium ASFV dataset
input_file = "tests/test_data/datasets/mitochondrial/primers.tsv"  # Circular genome
```

## Test Data

PrePrimer includes test datasets you can use with examples:

| Dataset | Type | Amplicons | Description |
|---------|------|-----------|-------------|
| `small/` | Linear | 5 | COVID-19 primers |
| `medium/` | Linear | 80 | ASFV whole genome |
| `mitochondrial/` | Circular | 8 | Human mtDNA (16,569 bp) |

## Requirements

All examples require PrePrimer to be installed:

```bash
# Install from source
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Output Structure

Examples typically create output in this structure:

```
output/
├── basic_conversion/
│   └── artic/
│       ├── primer.bed
│       ├── reference.fasta
│       └── info.json
├── batch_conversion/
│   ├── scheme1/
│   │   ├── artic/
│   │   ├── fasta/
│   │   └── sts/
│   └── scheme2/
│       ├── artic/
│       ├── fasta/
│       └── sts/
└── quality_filtered/
    └── artic/
        ├── primer.bed
        └── info.json
```

## Tips for Using Examples

1. **Start with `basic_conversion.py`**
   - Simplest example
   - Good for understanding basics
   - Minimal setup required

2. **Use test data for learning**
   ```python
   input_file = "tests/test_data/datasets/small/primers.tsv"
   ```

3. **Customize quality criteria**
   ```python
   quality_criteria = {
       "min_gc": 35.0,  # Adjust to your needs
       "max_gc": 65.0,
       "min_tm": 57.0,
       "max_tm": 63.0
   }
   ```

4. **Check output directories**
   - Examples create `output/` directory
   - Each example uses different subdirectories
   - Safe to delete after testing

5. **Handle errors gracefully**
   - All examples include error handling
   - See `error_handling.py` for comprehensive patterns
   - Always validate file paths before processing

## Advanced Usage

### Creating Custom Examples

Template for new examples:

```python
#!/usr/bin/env python3
"""
Your Example Name

Description of what this example demonstrates.
"""

from pathlib import Path
from preprimer.core.converter import Converter

def main():
    """Main example function."""
    print("=" * 70)
    print("Your Example Name")
    print("=" * 70)
    print()

    # Your code here

if __name__ == "__main__":
    main()
```

### Integration with Workflows

Examples can be adapted for use in workflows:

```python
# As a module
from examples.quality_filtering import filter_amplicons_by_quality

# In your code
filtered = filter_amplicons_by_quality(
    amplicons,
    min_gc=40.0,
    max_gc=60.0
)
```

## Troubleshooting

### Example won't run

**Problem:** File not found errors

**Solution:**
```python
# Check if file exists before running
from pathlib import Path

input_file = "your_file.tsv"
if not Path(input_file).exists():
    print(f"File not found: {input_file}")
    # Use test data instead
    input_file = "tests/test_data/datasets/small/primers.tsv"
```

### Import errors

**Problem:** Cannot import preprimer modules

**Solution:**
```bash
# Install PrePrimer first
pip install -e .

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Output directory errors

**Problem:** Permission denied or directory doesn't exist

**Solution:**
```python
from pathlib import Path

output_dir = Path("output/examples")
output_dir.mkdir(parents=True, exist_ok=True)
```

## Next Steps

After exploring the examples:

1. **Read API Documentation**
   - See `docs/api/python-api.md`
   - Comprehensive API reference
   - Advanced usage patterns

2. **Check User Guide**
   - `docs/user-guide/basic-usage.md`
   - `docs/user-guide/supported-formats.md`
   - `docs/user-guide/cli-reference.md`

3. **Explore Test Suite**
   - `tests/` directory
   - Real-world validation examples
   - Property-based testing patterns

4. **Build Your Application**
   - Adapt examples to your needs
   - Implement custom parsers/writers
   - Integrate with your workflows

## Support

- **Documentation**: https://github.com/FOI-Bioinformatics/preprimer/tree/main/docs
- **Issues**: https://github.com/FOI-Bioinformatics/preprimer/issues
- **Contributing**: See `CONTRIBUTING.md`

---

**Last Updated**: 2024-10-14
**PrePrimer Version**: 1.0.0
