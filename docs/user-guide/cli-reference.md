# 🖥️ CLI Reference

Complete command-line interface reference for PrePrimer.

## 🚀 **Global Commands**

### **preprimer --help**
Display help information and available commands.

```bash
preprimer --help
preprimer -h
```

### **preprimer --version**
Show PrePrimer version information.

```bash
preprimer --version
preprimer -v
```

**Output:**
```
PrePrimer 0.2.0
```

## 📋 **Main Commands**

### **preprimer convert**
Convert primer schemes between formats.

#### **Syntax**
```bash
preprimer convert [OPTIONS] --input FILE --output-dir DIR --output-formats FORMAT[,FORMAT...]
```

#### **Required Arguments**
- `--input PATH, -i PATH` - Input primer file path
- `--output-dir PATH, -o PATH` - Output directory for converted files  
- `--output-formats FORMAT[,FORMAT...], -f FORMAT[,FORMAT...]` - Output formats (artic, fasta, sts)

#### **Optional Arguments**

**Input Control:**
- `--format FORMAT` - Force specific input format (varvamp, artic, olivar)
- `--prefix STRING, -p STRING` - Prefix for output files

**Processing Options:**
- `--config PATH, -c PATH` - JSON configuration file
- `--validate-only` - Only validate input, don't convert
- `--force` - Overwrite existing output files
- `--reference PATH` - Reference sequence file for validation

**Validation Settings:**
- `--min-primer-length N` - Minimum allowed primer length (default: 15)
- `--max-primer-length N` - Maximum allowed primer length (default: 35)
- `--validate-sequences` - Validate DNA sequences for validity

**Output Control:**
- `--quiet, -q` - Suppress non-error output
- `--verbose, -v` - Enable verbose output for debugging

#### **Examples**

**Basic Usage:**
```bash
# Auto-detect format, convert to ARTIC
preprimer convert -i primers.tsv -o output/ -f artic

# Multiple output formats
preprimer convert -i primers.csv -o schemes/ -f artic,fasta,sts -p MyVirus

# Force specific input format
preprimer convert -i ambiguous.txt --format varvamp -o output/ -f artic
```

**Advanced Usage:**
```bash
# With custom configuration
preprimer convert -i primers.tsv -o output/ -f artic -c strict-config.json

# Validation only
preprimer convert -i primers.csv --validate-only

# Verbose processing
preprimer convert -i primers.tsv -o output/ -f artic --verbose

# Custom validation parameters
preprimer convert -i primers.tsv -o output/ -f artic \
                 --min-primer-length 18 \
                 --max-primer-length 30 \
                 --validate-sequences
```

**Batch Processing:**
```bash
# Process multiple files
for file in *.tsv; do
    preprimer convert -i "$file" -o "output/$(basename "$file" .tsv)/" -f artic
done
```

#### **Exit Codes**
- `0` - Success
- `1` - General error (file not found, invalid format, etc.)
- `2` - Validation error (invalid primers, sequences, etc.)
- `3` - Configuration error (invalid config file, missing required options)
- `4` - Output error (permission denied, disk full, etc.)

### **preprimer info**
Display detailed information about primer files.

#### **Syntax**
```bash
preprimer info [OPTIONS] FILE
```

#### **Arguments**
- `FILE` - Input primer file to analyze

#### **Options**
- `--format FORMAT` - Force specific input format
- `--detailed, -d` - Show detailed information including primer sequences
- `--json` - Output information in JSON format

#### **Examples**

**Basic Information:**
```bash
preprimer info primers.tsv
```

**Output:**
```
📁 File: primers.tsv
📏 Size: 3,247 bytes (3.2 KB)
🔍 Detected format: varvamp
🧬 Amplicons: 80
🔬 Primers: 160
📊 Pool distribution:
  Pool 1: 80 primers (50.0%)
  Pool 2: 80 primers (50.0%)
🎯 Primer length range: 22-28 bp
📐 Amplicon size range: 300-400 bp
✅ Validation: All primers valid
```

**Detailed Information:**
```bash
preprimer info primers.csv --detailed
```

**JSON Output:**
```bash
preprimer info primers.tsv --json
```

```json
{
  "file_path": "primers.tsv",
  "file_size": 3247,
  "detected_format": "varvamp",
  "amplicon_count": 80,
  "primer_count": 160,
  "pools": {
    "1": 80,
    "2": 80
  },
  "primer_length": {
    "min": 22,
    "max": 28,
    "mean": 24.5
  },
  "amplicon_size": {
    "min": 300,
    "max": 400,
    "mean": 350
  },
  "validation": {
    "valid": true,
    "errors": []
  }
}
```

### **preprimer list**
Display available input and output formats.

#### **Syntax**
```bash
preprimer list [OPTIONS]
```

#### **Options**
- `--input-only` - Show only input formats
- `--output-only` - Show only output formats
- `--json` - Output in JSON format

#### **Examples**

**All Formats:**
```bash
preprimer list
```

**Output:**
```
📥 Available input formats:
  varvamp: .tsv, .txt
    Description: VarVAMP tiled primer schemes
    Example: amplicon_name, primer_name, sequence, start, stop

  artic: .bed, .scheme.bed  
    Description: ARTIC primer scheme BED format
    Example: chrom, start, stop, name, score, strand

  olivar: .csv
    Description: Olivar primer design output
    Example: amplicon_id, fP, rP

📤 Available output formats:
  artic: .scheme.bed
    Description: ARTIC workflow-compatible BED format
    Structure: ProjectName/V1/ProjectName.scheme.bed

  fasta: .fasta
    Description: Multi-FASTA with primer sequences
    Headers: Include amplicon and pool information

  sts: .sts.tsv  
    Description: STS format for in-silico PCR validation
    Columns: primer_name, forward_seq, reverse_seq
```

**Input Formats Only:**
```bash
preprimer list --input-only
```

**JSON Output:**
```bash
preprimer list --json
```

## ⚙️ **Configuration File Format**

Configuration files use JSON format to specify processing options.

### **Basic Configuration**
```json
{
    "validate_sequences": true,
    "force_overwrite": false,
    "min_primer_length": 15,
    "max_primer_length": 35
}
```

### **Advanced Configuration**
```json
{
    "validation": {
        "validate_sequences": true,
        "check_primer_pairs": true,
        "allow_ambiguous_bases": false,
        "min_primer_length": 18,
        "max_primer_length": 32
    },
    "output": {
        "force_overwrite": true,
        "create_reference": true,
        "include_metadata": true
    },
    "processing": {
        "skip_invalid_primers": false,
        "normalize_sequences": true,
        "sort_by_position": true
    }
}
```

### **Format-Specific Configuration**
```json
{
    "parsers": {
        "varvamp": {
            "header_variations": ["amlicon_name", "amplicon_name"],
            "separator": "\t"
        },
        "olivar": {
            "forward_column": "fP",
            "reverse_column": "rP"  
        },
        "artic": {
            "coordinate_system": "bed"
        }
    },
    "writers": {
        "artic": {
            "include_reference": true,
            "version_directory": "V1"
        },
        "fasta": {
            "line_width": 80,
            "include_pools": true
        }
    }
}
```

## 🔧 **Environment Variables**

Control PrePrimer behavior with environment variables:

### **General Settings**
- `PREPRIMER_CONFIG_DIR` - Default configuration directory
- `PREPRIMER_DATA_DIR` - Default data directory  
- `PREPRIMER_OUTPUT_DIR` - Default output directory
- `PREPRIMER_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### **Processing Options**
- `PREPRIMER_VALIDATE` - Enable validation by default (true/false)
- `PREPRIMER_FORCE` - Enable force overwrite by default (true/false)
- `PREPRIMER_QUIET` - Enable quiet mode by default (true/false)

### **Format Detection**
- `PREPRIMER_AUTO_DETECT` - Enable format auto-detection (true/false)
- `PREPRIMER_FALLBACK_FORMAT` - Fallback format if detection fails

### **Example Usage**
```bash
# Set default output directory
export PREPRIMER_OUTPUT_DIR=~/primer_schemes

# Enable verbose logging
export PREPRIMER_LOG_LEVEL=DEBUG

# Run with environment settings
preprimer convert -i primers.tsv -f artic
```

## 📊 **Output Format Details**

### **ARTIC Format Output**
```
output_dir/
└── artic/
    └── PREFIX/
        └── V1/
            ├── PREFIX.scheme.bed
            └── PREFIX.reference.fasta
```

**BED Format:**
```
chrom    start    stop     name                pool    strand
ref      100      125      PREFIX_1_LEFT       1       +
ref      380      405      PREFIX_1_RIGHT      1       -
ref      250      275      PREFIX_2_LEFT       2       +
ref      530      555      PREFIX_2_RIGHT      2       -
```

### **FASTA Format Output**
```
output_dir/
└── fasta/
    └── PREFIX.fasta
```

**FASTA Format:**
```
>PREFIX_1_LEFT pool=1 amplicon=1 direction=forward start=100 stop=125
ATCGATCGATCGATCGATCGATCGAT
>PREFIX_1_RIGHT pool=1 amplicon=1 direction=reverse start=380 stop=405
TAGCTAGCTAGCTAGCTAGCTAGCTA
```

### **STS Format Output**
```
output_dir/
└── sts/
    └── PREFIX.sts.tsv
```

**TSV Format:**
```
primer_name    forward_primer                reverse_primer
PREFIX_1       ATCGATCGATCGATCGATCGATCGAT     TAGCTAGCTAGCTAGCTAGCTAGCTA
PREFIX_2       GCTAGCTAGCTAGCTAGCTAGCTAG     ATCGATCGATCGATCGATCGATCGAT
```

## 🚨 **Error Handling**

### **Common Error Messages**

**File Not Found:**
```
Error: Input file 'primers.tsv' not found
Solution: Check file path and permissions
```

**Format Detection Failed:**
```
Error: Could not detect input format for 'file.txt'
Solution: Use --format option to specify format explicitly
```

**Validation Failed:**
```
Error: 5 primers failed validation
- Primer 'PRIMER_1': sequence contains invalid characters
- Primer 'PRIMER_2': length (45) exceeds maximum (35)
Solution: Check primer sequences or adjust validation settings
```

**Permission Denied:**
```
Error: Permission denied writing to 'output/'
Solution: Check directory permissions or use different output directory
```

### **Debug Mode**
Enable verbose output for troubleshooting:

```bash
preprimer convert -i primers.tsv -o output/ -f artic --verbose
```

**Debug Output:**
```
DEBUG: Detected input format: varvamp
DEBUG: Loading configuration from default settings
DEBUG: Validating 160 primers...
DEBUG: Creating output directory: output/artic/
DEBUG: Writing ARTIC BED file...
INFO: Conversion completed successfully
```

## 📋 **Command Chaining**

### **Pipeline Examples**

**Validation → Conversion → Verification:**
```bash
# Step 1: Validate
preprimer info primers.tsv
if [ $? -eq 0 ]; then
    # Step 2: Convert
    preprimer convert -i primers.tsv -o output/ -f artic -p MyProject
    if [ $? -eq 0 ]; then
        # Step 3: Verify output
        preprimer info output/artic/MyProject/V1/MyProject.scheme.bed
    fi
fi
```

**Batch Processing with Error Handling:**
```bash
for file in *.tsv; do
    echo "Processing $file..."
    preprimer convert -i "$file" -o "output/" -f artic -p "$(basename "$file" .tsv)"
    if [ $? -ne 0 ]; then
        echo "Error processing $file" >> errors.log
    fi
done
```

## 🔗 **Integration Examples**

### **With ARTIC Tools**
```bash
# Convert primers
preprimer convert -i varvamp_output.tsv -o artic_schemes/ -f artic -p SARS_CoV_2

# Use with ARTIC
artic minion SARS_CoV_2 data/ --scheme-directory artic_schemes/artic/
```

### **With Nextflow**
```groovy
process CONVERT_PRIMERS {
    input:
    path primer_file
    
    output:
    path "schemes/artic/*/*"
    
    script:
    """
    preprimer convert -i ${primer_file} -o schemes/ -f artic -p ${params.project_name}
    """
}
```

---

## 📚 **Related Documentation**

- **[Basic Usage Guide](basic-usage.md)** - Essential workflows
- **[Configuration Guide](configuration.md)** - Advanced settings
- **[Python API](python-api-basics.md)** - Programmatic usage
- **[Format Guide](supported-formats.md)** - Input/output formats

**Complete CLI reference for efficient primer conversion! 🖥️✨**