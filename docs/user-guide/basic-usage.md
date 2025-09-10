# 📘 Basic Usage Guide

Essential PrePrimer commands and workflows for daily use.

## 🚀 **Core Commands**

### **Convert Primers**
The main command for converting primer schemes:

```bash
preprimer convert --input INPUT_FILE --output-dir OUTPUT_DIR --output-formats FORMAT [OPTIONS]
```

**Basic Examples:**
```bash
# Auto-detect format and convert to ARTIC
preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic

# Multiple output formats
preprimer convert --input primers.csv \
                 --output-dir output/ \
                 --output-formats artic fasta sts \
                 --prefix MyVirus

# Custom configuration
preprimer convert --input primers.bed \
                 --output-dir schemes/ \
                 --output-formats artic \
                 --config my-config.json
```

### **File Information**
Get detailed information about primer files:

```bash
preprimer info INPUT_FILE
```

**Example Output:**
```
📁 File: varvamp_primers.tsv
📏 Size: 3,247 bytes
🔍 Detected format: varvamp  
🧬 Amplicons: 80
🔬 Primers: 160
📊 Pool distribution: Pool 1 (80), Pool 2 (80)
```

### **List Formats**
See all supported input and output formats:

```bash
preprimer list
```

**Output:**
```
📥 Available input formats:
  varvamp: .tsv, .txt
  artic: .bed, .scheme.bed
  olivar: .csv

📤 Available output formats:
  artic: .scheme.bed
  fasta: .fasta
  sts: .sts.tsv
```

## 🎯 **Common Workflows**

### **1. VarVAMP to ARTIC Workflow**

Most common use case - converting VarVAMP primers for ARTIC tools:

```bash
# Step 1: Validate input file
preprimer info varvamp_output.tsv

# Step 2: Convert to ARTIC format
preprimer convert \
    --input varvamp_output.tsv \
    --output-dir artic_schemes/ \
    --output-formats artic \
    --prefix SARS_CoV_2

# Step 3: Use with ARTIC minion
artic minion SARS_CoV_2 data/ --scheme-directory artic_schemes/artic/
```

### **2. Multi-Format Export**

Create multiple output formats for different tools:

```bash
# Convert to all supported formats
preprimer convert \
    --input primers.csv \
    --output-dir multi_format/ \
    --output-formats artic fasta sts \
    --prefix COVID19_Study

# Results:
# multi_format/artic/COVID19_Study/V1/COVID19_Study.scheme.bed
# multi_format/fasta/COVID19_Study.fasta  
# multi_format/sts/COVID19_Study.sts.tsv
```

### **3. Batch Processing**

Process multiple primer files:

```bash
# Process all TSV files in directory
for file in *.tsv; do
    basename=$(basename "$file" .tsv)
    preprimer convert \
        --input "$file" \
        --output-dir "output/$basename/" \
        --output-formats artic \
        --prefix "$basename"
done
```

### **4. Quality Control Pipeline**

Validate and convert with quality checks:

```bash
# Step 1: Check all files
for file in primers/*.{tsv,csv,bed}; do
    echo "Checking $file:"
    preprimer info "$file"
    echo "---"
done

# Step 2: Convert with validation
preprimer convert \
    --input primers/validated.tsv \
    --output-dir qc_output/ \
    --output-formats artic fasta \
    --prefix QC_Validated \
    --config strict-validation.json
```

### **5. Circular Genome Example**

PrePrimer automatically detects circular genomes and handles coordinate wrapping for biologically accurate interpretation:

```bash
# Convert human mitochondrial primers (automatically detected as circular)
preprimer convert \
    --input mitochondrial_primers.tsv \
    --output-dir mito_schemes/ \
    --output-formats artic fasta sts \
    --prefix NC_012920.1

# Log output shows automatic topology detection:
# INFO: Detected circular topology for reference NC_012920.1
# INFO: Amplicon NC_012920.1_1: length 370 (wrapping boundary)
```

**Topology Detection Examples:**

```bash
# Automatic detection from reference ID
preprimer convert --input primers.tsv --prefix NC_012920.1 --output-formats artic
# → Detects: circular, 16,569 bp (human mitochondrial genome)

# Automatic detection from metadata file
echo "topology: circular\ngenome_length: 16569" > metadata.yaml
preprimer convert --input primers.tsv --output-formats artic
# → Uses metadata specification

# Warning for potential mismatches
preprimer convert --input suspicious_primers.tsv --output-formats artic
# → WARNING: High start (16400) with low end (200) on linear genome - check topology
```

**Coordinate Wrapping Example:**
```tsv
# Amplicon spanning genome boundary (16,569 bp circular genome)
amplicon_name       primer_name           start  stop  sequence
NC_012920.1_1      NC_012920.1_1_FW      16400  16420  ATCGATCG...
NC_012920.1_1      NC_012920.1_1_RW      200    220    CGATCGAT...
# Amplicon length: (16569-16400) + 200 + 1 = 370 bp
```

**Key features for circular genomes:**
- Automatic topology detection from multiple sources
- Biologically accurate amplicon length calculation
- Validation warnings for coordinate mismatches
- Support for all standard formats (VarVAMP, ARTIC, Olivar)

## ⚙️ **Command Options**

### **Input Options**
- `--input PATH` - Input primer file (required)
- `--format FORMAT` - Force specific input format (optional, auto-detected)

### **Output Options**
- `--output-dir PATH` - Output directory (required)
- `--output-formats LIST` - Output formats: artic, fasta, sts (required)
- `--prefix STRING` - Prefix for output files (recommended)

### **Processing Options**
- `--config PATH` - Configuration file for custom settings
- `--validate-only` - Only validate, don't convert
- `--force` - Overwrite existing files
- `--quiet` - Suppress non-error output
- `--verbose` - Detailed processing information

### **Advanced Options**
- `--min-primer-length N` - Minimum primer length (default: 15)
- `--max-primer-length N` - Maximum primer length (default: 35)
- `--validate-sequences` - Validate DNA sequences
- `--reference PATH` - Reference sequence for validation

## 📂 **Output Structure**

PrePrimer creates organized output directories:

```
output_directory/
├── artic/
│   └── ProjectName/
│       └── V1/
│           ├── ProjectName.scheme.bed
│           └── ProjectName.reference.fasta
├── fasta/
│   └── ProjectName.fasta
└── sts/
    └── ProjectName.sts.tsv
```

### **ARTIC Format Structure**
```
ProjectName/
└── V1/                          # Version directory
    ├── ProjectName.scheme.bed   # Primer coordinates
    └── ProjectName.reference.fasta  # Reference sequence
```

### **File Naming Convention**
- **Prefix**: User-defined project name
- **Extensions**: Format-specific (.scheme.bed, .fasta, .sts.tsv)
- **Directories**: Organized by output format

## 🔍 **Format Detection**

PrePrimer automatically detects input formats:

### **VarVAMP Detection**
- Extensions: `.tsv`, `.txt`
- Headers: `amplicon_name`, `primer_name`, `sequence`, `start`, `stop`
- Tab-separated values

### **ARTIC Detection**  
- Extensions: `.bed`, `.scheme.bed`
- Format: BED format with primer names
- Columns: chrom, start, stop, name, score, strand

### **Olivar Detection**
- Extension: `.csv`
- Headers: `amplicon_id`, `fP`, `rP` (forward/reverse primers)
- Comma-separated values

## 💡 **Tips and Best Practices**

### **File Organization**
```bash
# Recommended directory structure
project/
├── input/
│   └── primers.tsv
├── config/
│   └── validation-config.json
└── output/
    ├── artic/
    ├── fasta/
    └── sts/
```

### **Naming Conventions**
```bash
# Use descriptive prefixes
preprimer convert --input primers.tsv --prefix "SARS_CoV_2_WHO_v4"
preprimer convert --input primers.csv --prefix "Influenza_H1N1_2024"
```

### **Quality Control**
```bash
# Always check files first
preprimer info mysterious_file.csv

# Validate before converting
preprimer convert --validate-only --input primers.tsv
```

### **Configuration Files**
Create reusable configurations:

```json
{
    "validate_sequences": true,
    "min_primer_length": 18,
    "max_primer_length": 32,
    "force_overwrite": false
}
```

## ⚠️ **Common Issues**

### **Format Detection Failed**
```bash
# Force specific format
preprimer convert --input file.txt --format varvamp --output-formats artic
```

### **Permission Errors**
```bash
# Use different output directory
preprimer convert --input primers.tsv --output-dir ~/preprimer_output/
```

### **Large Files**
```bash
# Use quiet mode for large files
preprimer convert --input large_primers.tsv --output-formats artic --quiet
```

### **Validation Errors**
```bash
# Skip validation if needed
preprimer convert --input primers.tsv --output-formats artic --config permissive.json
```

## 🔧 **Troubleshooting**

### **Check Installation**
```bash
preprimer --version
preprimer list
```

### **Debug Mode**
```bash
preprimer convert --input primers.tsv --output-formats artic --verbose
```

### **Test with Sample Data**
```bash
# Use built-in test data
preprimer convert \
    --input tests/test_data/ASFV_long/primers.tsv \
    --output-dir test_output/ \
    --output-formats artic \
    --prefix TEST
```

---

## 🔗 **What's Next?**

- **[Configuration Guide](configuration.md)** - Customize PrePrimer behavior
- **[CLI Reference](cli-reference.md)** - Complete command documentation  
- **[Format Guide](supported-formats.md)** - Detailed format information
- **[Quick Start](quick-start.md)** - Your first conversion in 5 minutes

**Ready to convert primers efficiently! 🧬✨**