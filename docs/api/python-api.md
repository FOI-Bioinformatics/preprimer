# PrePrimer Python API Documentation

Comprehensive guide to using PrePrimer as a Python library for programmatic primer scheme conversion and manipulation.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Parsers](#parsers)
- [Writers](#writers)
- [Converter](#converter)
- [Configuration](#configuration)
- [Advanced Usage](#advanced-usage)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Installation

```bash
# Install from source
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Basic Format Conversion

```python
from preprimer.core.converter import Converter

# Create converter instance
converter = Converter()

# Convert VarVAMP to ARTIC format
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic"],
    prefix="SARS-CoV-2"
)

print(f"Converted {len(amplicons)} amplicons")
```

### Parse and Manipulate Primer Data

```python
from preprimer.parsers import VarVAMPParser
from preprimer.core.interfaces import AmpliconData

# Parse VarVAMP file
parser = VarVAMPParser()
amplicons = parser.parse("primers.tsv", prefix="ref")

# Access primer information
for amplicon in amplicons:
    print(f"Amplicon: {amplicon.amplicon_id}")
    print(f"  Length: {amplicon.length} bp")
    print(f"  Primers: {len(amplicon.primers)}")

    for primer in amplicon.primers:
        print(f"    {primer.name}: {primer.sequence} ({primer.direction})")
```

## Core Components

### Data Models

PrePrimer uses Pydantic models for type-safe data handling.

#### PrimerData

Represents a single primer with all associated metadata.

```python
from preprimer.core.interfaces import PrimerData

primer = PrimerData(
    name="SARS-CoV-2_1_LEFT",
    sequence="ACCAACCAACTTTCGATCTCTTGT",
    start=30,
    stop=54,
    strand="+",
    length=24,
    direction="forward",
    pool=1,
    gc_content=41.67,
    tm=59.5,
    amplicon_id="SARS-CoV-2_1",
    reference_id="MN908947.3"
)

# Access properties
print(f"Primer: {primer.name}")
print(f"Sequence: {primer.sequence}")
print(f"Tm: {primer.tm}°C")
print(f"GC%: {primer.gc_content:.1f}%")
```

**PrimerData Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Unique primer identifier |
| `sequence` | str | Primer sequence (5' to 3') with IUPAC support |
| `start` | int | Start coordinate (coordinate system varies by format) |
| `stop` | int | End coordinate |
| `strand` | str | '+' for forward, '-' for reverse |
| `length` | int | Primer length in base pairs |
| `direction` | str | 'forward' or 'reverse' |
| `pool` | int | Pool assignment number |
| `gc_content` | float | GC content percentage (0-100) |
| `tm` | float | Melting temperature in Celsius |
| `amplicon_id` | str | Parent amplicon identifier |
| `reference_id` | str | Reference sequence identifier |
| `metadata` | dict | Additional custom metadata |

#### AmpliconData

Represents an amplicon with its associated primers.

```python
from preprimer.core.interfaces import AmpliconData, PrimerData

amplicon = AmpliconData(
    amplicon_id="SARS-CoV-2_1",
    primers=[forward_primer, reverse_primer],
    length=400,
    reference_id="MN908947.3",
    start=30,
    end=430,
    pool=1,
    metadata={"coverage": 1.5}
)

# Calculate statistics
num_primers = len(amplicon.primers)
forward_primers = [p for p in amplicon.primers if p.direction == "forward"]
reverse_primers = [p for p in amplicon.primers if p.direction == "reverse"]

print(f"Amplicon {amplicon.amplicon_id}:")
print(f"  Length: {amplicon.length} bp")
print(f"  Forward primers: {len(forward_primers)}")
print(f"  Reverse primers: {len(reverse_primers)}")
```

**AmpliconData Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `amplicon_id` | str | Unique amplicon identifier |
| `primers` | List[PrimerData] | List of primer objects |
| `length` | int | Expected amplicon length |
| `reference_id` | str | Reference sequence identifier |
| `start` | int | Amplicon start coordinate (optional) |
| `end` | int | Amplicon end coordinate (optional) |
| `pool` | int | Pool assignment (optional) |
| `metadata` | dict | Additional custom metadata |

## Parsers

PrePrimer provides parsers for multiple primer design formats.

### Available Parsers

```python
from preprimer.parsers import (
    VarVAMPParser,    # VarVAMP TSV format
    ARTICParser,      # ARTIC BED format
    OlivarParser,     # Olivar CSV format
    STSParser         # STS TSV format
)
```

### VarVAMP Parser

Parse VarVAMP 13-column TSV files with full IUPAC degenerate nucleotide support.

```python
from preprimer.parsers import VarVAMPParser

parser = VarVAMPParser()

# Check if file is valid VarVAMP format
if parser.can_parse("primers.tsv"):
    # Parse file
    amplicons = parser.parse("primers.tsv", prefix="NC_045512")

    # Access parsed data
    for amplicon in amplicons:
        print(f"{amplicon.amplicon_id}: {amplicon.length}bp, {len(amplicon.primers)} primers")

        for primer in amplicon.primers:
            if "N" in primer.sequence or "R" in primer.sequence:
                print(f"  Degenerate primer: {primer.name}")
```

**Features:**
- Full 13-column VarVAMP specification support
- IUPAC degenerate nucleotide codes (R, Y, S, W, K, M, B, D, H, V, N)
- Quality metrics (GC content, Tm, primer scores)
- Coordinate validation
- Pool assignment parsing

### ARTIC Parser

Parse ARTIC BED format files (articbedversion v2.0 and v3.0).

```python
from preprimer.parsers import ARTICParser
from pathlib import Path

parser = ARTICParser()

# Parse ARTIC BED file
amplicons = parser.parse("scheme.primer.bed", prefix="nCoV-2019")

# Get associated reference file
ref_file = parser.get_reference_file("scheme.primer.bed")
if ref_file and ref_file.exists():
    print(f"Reference: {ref_file}")

# Check for info.json metadata
info_file = Path("scheme.primer.bed").parent / "info.json"
if info_file.exists():
    import json
    with open(info_file) as f:
        metadata = json.load(f)
    print(f"Scheme: {metadata.get('schemename')} v{metadata.get('schemeversion')}")
```

**Features:**
- articbedversion v2.0 and v3.0 compatibility
- 0-based BED coordinate handling
- Extended 7-column format with sequences
- Automatic reference file detection
- Primal-page info.json integration
- Topology-aware (circular genome support)

### Olivar Parser

Parse Olivar CSV format with variant-aware primer designs.

```python
from preprimer.parsers import OlivarParser

parser = OlivarParser()

# Parse Olivar CSV
amplicons = parser.parse("olivar-design.csv", prefix="mtDNA")

# Check for circular genome topology
for amplicon in amplicons:
    if amplicon.start and amplicon.end and amplicon.start > amplicon.end:
        print(f"Circular amplicon detected: {amplicon.amplicon_id}")
        print(f"  Wraps around origin: {amplicon.start} -> {amplicon.end}")
```

**Features:**
- Row-based amplicon format (primer pairs per row)
- IUPAC degenerate nucleotide support
- Circular genome coordinate handling
- Optional metadata columns
- JSON configuration file support

### STS Parser

Parse simple Sequence Tagged Site (STS) format for in-silico PCR.

```python
from preprimer.parsers import STSParser

parser = STSParser()

# Parse STS TSV file (minimal 3-column format)
amplicons = parser.parse("primers.sts.tsv", prefix="reference")

# STS format has no coordinate information
# Placeholder coordinates are assigned
for amplicon in amplicons:
    print(f"{amplicon.amplicon_id}:")
    for primer in amplicon.primers:
        print(f"  {primer.name}: {primer.sequence}")
        # Note: start/stop are placeholders (0-based)
```

**Features:**
- Minimal 3-column format (NAME, FORWARD, REVERSE)
- No coordinate requirements
- IUPAC support for degenerate primers
- Compatible with e-PCR and me-pcr tools
- Automatic coordinate assignment

### Parser Registry

Dynamic parser detection and registration.

```python
from preprimer.core.registry import parser_registry

# List all registered parsers
parsers = parser_registry.list_parsers()
print("Available parsers:", parsers)  # ['varvamp', 'artic', 'olivar', 'sts']

# Get parser by format name
varvamp_parser = parser_registry.get_parser('varvamp')

# Detect format automatically
detected_parser = parser_registry.detect_format("primers.tsv")
if detected_parser:
    print(f"Detected format: {detected_parser.format_name()}")
    amplicons = detected_parser.parse("primers.tsv", prefix="ref")
```

## Writers

PrePrimer provides writers for multiple output formats.

### Available Writers

```python
from preprimer.writers import (
    ARTICWriter,      # ARTIC primerscheme structure
    VarVAMPWriter,    # VarVAMP TSV format
    OlivarWriter,     # Olivar CSV format
    FASTAWriter,      # Multi-FASTA format
    STSWriter         # STS TSV format
)
```

### ARTIC Writer

Generate official ARTIC primerscheme structure with metadata.

```python
from preprimer.writers import ARTICWriter
from preprimer.parsers import VarVAMPParser

# Parse input
parser = VarVAMPParser()
amplicons = parser.parse("primers.tsv", prefix="SARS-CoV-2")

# Write ARTIC format
writer = ARTICWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/artic/",
    reference_seq="ACGT..." * 1000,  # Optional reference sequence
    prefix="SARS-CoV-2",
    metadata={
        "schemename": "SARS-CoV-2",
        "schemeversion": "v1.0.0",
        "species": "Severe acute respiratory syndrome coronavirus 2",
        "ampliconsize": 400
    }
)
```

**Output Structure:**
```
output/artic/
├── primer.bed       # 7-column extended BED format
├── reference.fasta  # Reference genome (if provided)
└── info.json       # Primal-page metadata
```

**Features:**
- Official primerscheme directory structure
- Primal-page info.json with MD5 validation
- articbedversion v3.0 compatible
- 0-based BED coordinates
- Optional reference FASTA generation

### FASTA Writer

Generate multi-FASTA primer sequences with metadata.

```python
from preprimer.writers import FASTAWriter

writer = FASTAWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/primers.fasta",
    prefix="COVID19",
    include_metadata=True,
    line_width=80
)
```

**Output Example:**
```fasta
>COVID19_1_LEFT pool=1 amplicon=COVID19_1 direction=forward start=30 stop=54
ACCAACCAACTTTCGATCTCTTGT
>COVID19_1_RIGHT pool=1 amplicon=COVID19_1 direction=reverse start=385 stop=410
CATCTTTAAGATGTTGACGTGCCTC
```

### STS Writer

Generate STS format for in-silico PCR validation.

```python
from preprimer.writers import STSWriter

writer = STSWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/primers.sts.tsv",
    prefix="reference"
)
```

**Output Format:**
```tsv
NAME	FORWARD	REVERSE
amp1	ACCAACCAACTTTCGATCTCTTGT	CATCTTTAAGATGTTGACGTGCCTC
amp2	TTGCTAGGAGTACACTGGAACGGT	CAAATGTTAAAAACACTATTAGCATA
```

### VarVAMP Writer

Generate VarVAMP-compatible TSV files.

```python
from preprimer.writers import VarVAMPWriter

writer = VarVAMPWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/primers.tsv",
    prefix="ref",
    include_scores=True
)
```

### Olivar Writer

Generate Olivar CSV format with amplicon metadata.

```python
from preprimer.writers import OlivarWriter

writer = OlivarWriter()
writer.write(
    amplicons=amplicons,
    output_path="output/olivar-design.csv",
    prefix="mtDNA"
)
```

### Writer Registry

```python
from preprimer.core.registry import writer_registry

# List all registered writers
writers = writer_registry.list_writers()
print("Available writers:", writers)

# Get writer by format name
artic_writer = writer_registry.get_writer('artic')
```

## Converter

High-level conversion interface with automatic format detection.

### Basic Conversion

```python
from preprimer.core.converter import Converter

converter = Converter()

# Single format conversion
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic"],
    prefix="MyVirus"
)

print(f"Converted {len(amplicons)} amplicons to ARTIC format")
```

### Multiple Format Conversion

```python
# Convert to multiple formats simultaneously
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic", "fasta", "sts", "varvamp", "olivar"],
    prefix="MultiFormat"
)

# Output directory structure:
# output/
# ├── artic/
# │   ├── primer.bed
# │   ├── reference.fasta
# │   └── info.json
# ├── fasta/
# │   └── MultiFormat.fasta
# ├── sts/
# │   └── MultiFormat.sts.tsv
# ├── varvamp/
# │   └── MultiFormat.tsv
# └── olivar/
#     └── MultiFormat.csv
```

### Format Detection

```python
# Automatic format detection
converter = Converter()

# Converter automatically detects input format
amplicons = converter.convert(
    input_file="unknown_format.txt",  # Will detect VarVAMP/ARTIC/Olivar/STS
    output_dir="output/",
    output_formats=["artic"]
)

# Manual format specification
amplicons = converter.convert(
    input_file="ambiguous.txt",
    input_format="varvamp",  # Force VarVAMP parser
    output_dir="output/",
    output_formats=["artic"]
)
```

### Conversion with Metadata

```python
# Include custom metadata
amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic"],
    prefix="SARS-CoV-2",
    metadata={
        "schemename": "SARS-CoV-2-tiled",
        "schemeversion": "v5.3.2",
        "species": "Severe acute respiratory syndrome coronavirus 2",
        "ampliconsize": 400,
        "authors": "ARTIC Network",
        "license": "CC-BY-4.0"
    }
)
```

## Configuration

### Loading Configuration

```python
from preprimer.core.config import PrePrimerConfig

# Default configuration
config = PrePrimerConfig()

# Load from file
config = PrePrimerConfig.from_file("config.json")

# Load with environment variables
config = PrePrimerConfig.from_env(prefix="PREPRIMER_")
```

### Configuration Options

```python
config = PrePrimerConfig(
    # Output settings
    output_formats=["artic", "fasta"],
    force_overwrite=False,

    # Parser settings
    default_pool=1,
    primer_naming_scheme="artic",
    validate_sequences=True,

    # Validation settings
    min_primer_length=15,
    max_primer_length=35,
    check_gc_content=True,
    min_gc_content=30.0,
    max_gc_content=70.0,

    # Performance
    parallel_processing=True,
    max_workers=4
)
```

### Custom Configuration

```python
# Save configuration
config.save("my_config.json")

# Update configuration
config.update(
    output_formats=["artic", "fasta", "sts"],
    validate_sequences=False
)
```

## Advanced Usage

### Custom Parser Implementation

```python
from preprimer.core.interfaces import PrimerParser, AmpliconData, PrimerData
from preprimer.core.registry import parser_registry
from pathlib import Path
from typing import List

class CustomParser(PrimerParser):
    """Custom primer format parser."""

    @classmethod
    def format_name(cls) -> str:
        return "custom"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".custom", ".cst"]

    def can_parse(self, file_path: str) -> bool:
        """Check if file is custom format."""
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline()
                return first_line.startswith("##CUSTOM_FORMAT")
        except:
            return False

    def parse(self, file_path: str, prefix: str = "") -> List[AmpliconData]:
        """Parse custom format file."""
        amplicons = []

        with open(file_path, 'r') as f:
            # Skip header
            f.readline()

            for line in f:
                if not line.strip():
                    continue

                # Parse custom format
                parts = line.strip().split('\t')
                name, fwd_seq, rev_seq = parts[:3]

                # Create primers
                fwd_primer = PrimerData(
                    name=f"{name}_F",
                    sequence=fwd_seq,
                    start=0,
                    stop=len(fwd_seq),
                    strand="+",
                    direction="forward",
                    pool=1,
                    amplicon_id=name,
                    reference_id=prefix
                )

                rev_primer = PrimerData(
                    name=f"{name}_R",
                    sequence=rev_seq,
                    start=300,
                    stop=300 + len(rev_seq),
                    strand="-",
                    direction="reverse",
                    pool=1,
                    amplicon_id=name,
                    reference_id=prefix
                )

                amplicon = AmpliconData(
                    amplicon_id=name,
                    primers=[fwd_primer, rev_primer],
                    length=300 + len(rev_seq),
                    reference_id=prefix
                )

                amplicons.append(amplicon)

        return amplicons

# Register custom parser
parser_registry.register(CustomParser)

# Use custom parser
from preprimer.core.converter import Converter
converter = Converter()
amplicons = converter.convert(
    input_file="data.custom",
    output_dir="output/",
    output_formats=["artic"]
)
```

### Filtering and Manipulation

```python
from preprimer.parsers import VarVAMPParser

parser = VarVAMPParser()
amplicons = parser.parse("primers.tsv", prefix="ref")

# Filter by pool
pool1_amplicons = [a for a in amplicons if a.pool == 1]

# Filter by amplicon length
optimal_amplicons = [a for a in amplicons if 350 <= a.length <= 450]

# Get primers with high GC content
high_gc_primers = []
for amplicon in amplicons:
    for primer in amplicon.primers:
        if primer.gc_content and primer.gc_content > 60:
            high_gc_primers.append(primer)

print(f"Found {len(high_gc_primers)} primers with GC% > 60")

# Modify primers
for amplicon in amplicons:
    for primer in amplicon.primers:
        # Convert sequences to uppercase
        primer.sequence = primer.sequence.upper()

        # Add custom metadata
        if not primer.metadata:
            primer.metadata = {}
        primer.metadata['processed'] = True
```

### Batch Processing

```python
from pathlib import Path
from preprimer.core.converter import Converter

converter = Converter()

# Process multiple files
input_dir = Path("input_schemes/")
output_dir = Path("converted/")

for input_file in input_dir.glob("*.tsv"):
    try:
        print(f"Processing {input_file.name}...")

        amplicons = converter.convert(
            input_file=str(input_file),
            output_dir=str(output_dir / input_file.stem),
            output_formats=["artic", "fasta"],
            prefix=input_file.stem
        )

        print(f"  ✓ Converted {len(amplicons)} amplicons")

    except Exception as e:
        print(f"  ✗ Error: {e}")
```

### Topology-Aware Processing

```python
from preprimer.core.topology import TopologyDetector, GenomeTopology
from preprimer.parsers import VarVAMPParser

parser = VarVAMPParser()
amplicons = parser.parse("mitochondrial_primers.tsv", prefix="NC_012920.1")

# Detect genome topology
detector = TopologyDetector()
topology = detector.detect_topology(amplicons, reference_length=16569)

if topology == GenomeTopology.CIRCULAR:
    print("Circular genome detected (mitochondrial/plasmid)")

    # Handle cross-origin amplicons
    for amplicon in amplicons:
        if amplicon.start and amplicon.end and amplicon.start > amplicon.end:
            # This amplicon wraps around the origin
            actual_length = detector.calculate_amplicon_length(
                start=amplicon.start,
                end=amplicon.end,
                reference_length=16569,
                is_circular=True
            )
            print(f"{amplicon.amplicon_id}: wraps origin, length={actual_length}bp")
else:
    print("Linear genome detected")
```

## Error Handling

PrePrimer provides structured exception hierarchy for robust error handling.

### Exception Types

```python
from preprimer.core.exceptions import (
    PrePrimerError,          # Base exception
    ParserError,             # Parsing failures
    InvalidFormatError,      # Format validation errors
    CorruptedDataError,      # Data integrity issues
    InsufficientDataError,   # Insufficient primer data
    SecurityError,           # Security violations
    ConfigError,             # Configuration errors
)
```

### Basic Error Handling

```python
from preprimer.core.converter import Converter
from preprimer.core.exceptions import ParserError, InvalidFormatError

converter = Converter()

try:
    amplicons = converter.convert(
        input_file="primers.tsv",
        output_dir="output/",
        output_formats=["artic"]
    )
except InvalidFormatError as e:
    print(f"Invalid file format: {e}")
    print(f"Expected format: {e.expected_format}")

except ParserError as e:
    print(f"Parsing error: {e}")
    print(f"File: {e.file_path}")
    print(f"Suggestions: {e.suggestions}")

except Exception as e:
    print(f"Unexpected error: {e}")
```

### Comprehensive Error Handling

```python
from preprimer.core.exceptions import PrePrimerError

def safe_conversion(input_file, output_dir):
    """Convert with comprehensive error handling."""
    try:
        converter = Converter()
        amplicons = converter.convert(
            input_file=input_file,
            output_dir=output_dir,
            output_formats=["artic", "fasta"]
        )
        return amplicons, None

    except PrePrimerError as e:
        # PrePrimer-specific errors
        error_info = {
            'type': type(e).__name__,
            'message': str(e),
            'user_message': e.user_message if hasattr(e, 'user_message') else None,
            'suggestions': e.suggestions if hasattr(e, 'suggestions') else [],
            'file_path': e.file_path if hasattr(e, 'file_path') else None
        }
        return None, error_info

    except Exception as e:
        # Unexpected errors
        error_info = {
            'type': 'UnexpectedError',
            'message': str(e)
        }
        return None, error_info

# Usage
amplicons, error = safe_conversion("primers.tsv", "output/")
if error:
    print(f"Conversion failed: {error['message']}")
    if error.get('suggestions'):
        print("Suggestions:")
        for suggestion in error['suggestions']:
            print(f"  - {suggestion}")
else:
    print(f"Success: {len(amplicons)} amplicons converted")
```

## Best Practices

### 1. Always Validate Input

```python
from pathlib import Path
from preprimer.parsers import VarVAMPParser

parser = VarVAMPParser()
input_file = Path("primers.tsv")

# Check file exists
if not input_file.exists():
    raise FileNotFoundError(f"Input file not found: {input_file}")

# Check file size
if input_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
    print("Warning: Large file may take time to process")

# Validate format before parsing
if not parser.can_parse(str(input_file)):
    raise ValueError(f"File is not valid VarVAMP format: {input_file}")

# Parse
amplicons = parser.parse(str(input_file), prefix="ref")
```

### 2. Use Configuration Files

```python
# config.json
{
    "output_formats": ["artic", "fasta", "sts"],
    "validate_sequences": true,
    "min_primer_length": 18,
    "max_primer_length": 30,
    "parallel_processing": true
}

# Code
from preprimer.core.config import PrePrimerConfig
from preprimer.core.converter import Converter

config = PrePrimerConfig.from_file("config.json")
converter = Converter(config=config)

amplicons = converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    prefix="MyScheme"
)
```

### 3. Provide Meaningful Metadata

```python
converter.convert(
    input_file="primers.tsv",
    output_dir="output/",
    output_formats=["artic"],
    prefix="SARS-CoV-2",
    metadata={
        "schemename": "SARS-CoV-2-midnight",
        "schemeversion": "v1.0.0",
        "species": "Severe acute respiratory syndrome coronavirus 2",
        "organism": "2697049",  # NCBI taxonomy ID
        "ampliconsize": 1200,
        "authors": "Lab Name",
        "contact": "lab@example.com",
        "license": "CC-BY-4.0",
        "citation": "DOI:10.xxxx/xxxxx",
        "description": "1200bp midnight primer scheme for SARS-CoV-2"
    }
)
```

### 4. Handle Circular Genomes Properly

```python
from preprimer.core.topology import TopologyDetector, GenomeTopology

# For mitochondrial/plasmid genomes
detector = TopologyDetector()
topology = detector.detect_topology(amplicons, reference_length=16569)

# Provide topology hint in metadata
if topology == GenomeTopology.CIRCULAR:
    metadata = {
        "topology": "circular",
        "genome_length": 16569,
        "organism_type": "mitochondrial"
    }
```

### 5. Batch Processing with Progress

```python
from pathlib import Path
from tqdm import tqdm

input_files = list(Path("schemes/").glob("*.tsv"))

for input_file in tqdm(input_files, desc="Converting schemes"):
    try:
        amplicons = converter.convert(
            input_file=str(input_file),
            output_dir=f"output/{input_file.stem}",
            output_formats=["artic"],
            prefix=input_file.stem
        )
        tqdm.write(f"✓ {input_file.name}: {len(amplicons)} amplicons")

    except Exception as e:
        tqdm.write(f"✗ {input_file.name}: {e}")
```

### 6. Memory-Efficient Processing

```python
# For very large schemes (10,000+ amplicons)
import gc

for input_file in large_file_list:
    amplicons = converter.convert(
        input_file=input_file,
        output_dir="output/",
        output_formats=["artic"]
    )

    # Process and clear
    print(f"Processed {len(amplicons)} amplicons")
    del amplicons
    gc.collect()
```

## Performance Tips

### 1. Use Parallel Processing

```python
config = PrePrimerConfig(
    parallel_processing=True,
    max_workers=4  # Adjust based on CPU cores
)
```

### 2. Minimize Format Conversions

```python
# Efficient: Single parse, multiple writes
amplicons = parser.parse("input.tsv", prefix="ref")
artic_writer.write(amplicons, "output/artic/", prefix="ref")
fasta_writer.write(amplicons, "output/fasta/", prefix="ref")

# Inefficient: Multiple parses
converter.convert(input_file="input.tsv", output_formats=["artic"])
converter.convert(input_file="input.tsv", output_formats=["fasta"])
```

### 3. Profile Performance

```python
import cProfile
import pstats

def profile_conversion():
    converter = Converter()
    amplicons = converter.convert(
        input_file="large_scheme.tsv",
        output_dir="output/",
        output_formats=["artic"]
    )

# Profile execution
profiler = cProfile.Profile()
profiler.enable()
profile_conversion()
profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Complete Examples

See the `examples/` directory for complete, runnable examples:

- `examples/basic_conversion.py` - Simple format conversion
- `examples/batch_processing.py` - Process multiple files
- `examples/custom_parser.py` - Implement custom parser
- `examples/topology_handling.py` - Circular genome handling
- `examples/quality_filtering.py` - Filter primers by quality
- `examples/metadata_enrichment.py` - Add custom metadata
- `examples/error_handling.py` - Robust error handling

## API Reference Summary

### Core Modules

| Module | Description |
|--------|-------------|
| `preprimer.core.converter` | High-level conversion interface |
| `preprimer.core.interfaces` | Data models (PrimerData, AmpliconData) |
| `preprimer.core.config` | Configuration management |
| `preprimer.core.registry` | Parser/Writer registration |
| `preprimer.core.topology` | Genome topology detection |
| `preprimer.core.exceptions` | Exception hierarchy |

### Parser Modules

| Module | Format | Description |
|--------|--------|-------------|
| `preprimer.parsers.varvamp_parser` | VarVAMP | 13-column TSV with IUPAC |
| `preprimer.parsers.artic_parser` | ARTIC | BED format (v2.0/v3.0) |
| `preprimer.parsers.olivar_parser` | Olivar | CSV with amplicon metadata |
| `preprimer.parsers.sts_parser` | STS | Simple 3-column TSV |

### Writer Modules

| Module | Format | Description |
|--------|--------|-------------|
| `preprimer.writers.artic_writer` | ARTIC | Official primerscheme structure |
| `preprimer.writers.varvamp_writer` | VarVAMP | 13-column TSV output |
| `preprimer.writers.olivar_writer` | Olivar | CSV format |
| `preprimer.writers.fasta_writer` | FASTA | Multi-FASTA sequences |
| `preprimer.writers.sts_writer` | STS | Simple TSV output |

## Support and Contributing

- **Documentation**: https://github.com/FOI-Bioinformatics/preprimer/tree/main/docs
- **Issues**: https://github.com/FOI-Bioinformatics/preprimer/issues
- **Contributing**: See CONTRIBUTING.md

---

**Version**: 1.0.0
**Last Updated**: 2024-10-14
**License**: MIT
