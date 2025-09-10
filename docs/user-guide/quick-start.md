# 🚀 Quick Start Guide

Get up and running with PrePrimer in 5 minutes! This guide will walk you through your first primer scheme conversion.

## ⚡ **5-Minute Setup**

### **1. Installation (2 minutes)**

```bash
# Clone the repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install PrePrimer
pip install -e .
```

Verify installation:
```bash
preprimer --version
# PrePrimer 0.2.0
```

### **2. Check Available Formats (30 seconds)**

```bash
# See what formats PrePrimer supports
preprimer list

# Output:
# 📥 Available input formats:
#   varvamp: .tsv, .txt
#   artic: .bed, .scheme.bed
#   olivar: .csv
# 
# 📤 Available output formats:
#   artic: .scheme.bed
#   fasta: .fasta
#   sts: .sts.tsv
```

### **3. Your First Conversion (2 minutes)**

#### **Option A: Using Test Data**
```bash
# Convert VarVAMP test data to ARTIC format
preprimer convert \
    --input tests/test_data/ASFV_long/primers.tsv \
    --output-dir my_first_conversion/ \
    --output-formats artic \
    --prefix ASFV_Test

# Check the results
ls my_first_conversion/artic/ASFV_Test/V1/
# ASFV_Test.scheme.bed
# ASFV_Test.reference.fasta
```

#### **Option B: Using Your Own Data**
```bash
# Get information about your file first
preprimer info your_primer_file.csv

# Convert your file
preprimer convert \
    --input your_primer_file.csv \
    --output-dir output/ \
    --output-formats artic fasta sts \
    --prefix MyProject
```

### **4. Verify Results (30 seconds)**

```bash
# Check what was created
find output/ -type f -name "*.*"

# Look at ARTIC output (first few lines)
head output/artic/MyProject/V1/MyProject.scheme.bed
```

## 🎯 **Common Use Cases**

### **VarVAMP → ARTIC (Most Common)**
```bash
# Convert VarVAMP primers for use with ARTIC workflow
preprimer convert \
    --input varvamp_output.tsv \
    --output-dir artic_schemes/ \
    --output-formats artic \
    --prefix SARS_CoV_2

# Ready for ARTIC!
artic minion SARS_CoV_2 data/ --scheme-directory artic_schemes/artic/
```

### **Olivar → Multiple Formats**
```bash
# Convert Olivar design to all formats
preprimer convert \
    --input olivar-design.csv \
    --output-dir multi_format/ \
    --output-formats artic fasta sts \
    --prefix COVID19_Study
```

### **File Investigation**
```bash
# Don't know what format your file is?
preprimer info mystery_primers.csv

# Example output:
# 📁 File: mystery_primers.csv
# 📏 Size: 2,996 bytes
# 🔍 Detected format: olivar
# 🧬 Amplicons: 5
# 🔬 Primers: 10
```

## 🐍 **Python API Quick Start**

### **Simple Conversion**
```python
from preprimer import convert_primers

# Convert primers
output_files = convert_primers(
    input_file="primers.tsv",
    output_dir="schemes/",
    output_formats=["artic", "fasta"],
    prefix="MyVirus"
)

# Use the results
print(f"ARTIC file: {output_files['artic']}")
print(f"FASTA file: {output_files['fasta']}")
```

### **Advanced Configuration**
```python
from preprimer import PrimerConverter, PrePrimerConfig

# Custom configuration
config = PrePrimerConfig(
    validate_sequences=True,
    force_overwrite=True,
    min_primer_length=15,
    max_primer_length=35
)

# Create converter
converter = PrimerConverter(config)

# Convert with custom settings
output_files = converter.convert(
    input_file="primers.tsv",
    output_dir="schemes/",
    output_formats=["artic", "fasta", "sts"],
    prefix="MyVirus"
)
```

## ✅ **Verify Everything Works**

### **Run Test Suite**
```bash
# Quick test to verify installation
python -c "
import preprimer.parsers
import preprimer.writers
from preprimer.core.registry import parser_registry
print('✅ All parsers registered:', parser_registry.list_formats())
"
```

### **Test with Sample Data**
```bash
# Test all parsers
python tests/test_parsers_unified.py

# Expected output:
# 🧪 Running harmonized parser tests...
# ✅ Testing VarVAMP parser...
# ✅ Testing ARTIC parser...
# ✅ Testing Olivar parser...
# 🎉 All harmonized tests passed!
```

## 🔧 **Next Steps**

### **Explore More Features**
1. **[Configuration Guide](configuration.md)** - Customize PrePrimer behavior
2. **[Format Guide](supported-formats.md)** - Learn about all supported formats  
3. **[CLI Reference](cli-reference.md)** - Complete command-line guide
4. **[Basic Usage](basic-usage.md)** - Essential workflows and examples

### **Additional Documentation**
- **[Technical Documentation](../technical/)** - Security, testing, and compatibility
- **[Developer Documentation](../developer/)** - Architecture and contribution guide
- **[Installation Guide](installation.md)** - Platform-specific installation instructions

## 🎉 **You're Ready!**

Congratulations! You've successfully:
- ✅ Installed PrePrimer
- ✅ Converted your first primer scheme
- ✅ Learned the basic commands
- ✅ Verified everything works

**PrePrimer is now ready for your viral genomics workflows! 🧬✨**

---

## 📊 **Quick Reference Card**

| Task | Command | Time |
|------|---------|------|
| **Install** | `pip install -e .` | 2 min |
| **Check formats** | `preprimer list` | 5 sec |
| **Get file info** | `preprimer info file.csv` | 5 sec |
| **Convert to ARTIC** | `preprimer convert --input file.tsv --output-formats artic` | 30 sec |
| **Multiple formats** | `preprimer convert --output-formats artic fasta sts` | 1 min |
| **Python API** | `from preprimer import convert_primers` | Instant |

**Total time to productivity: < 5 minutes! 🚀**