# ⚙️ Configuration Guide

Customize PrePrimer behavior with configuration files and settings.

## 🎯 **Configuration Overview**

PrePrimer uses JSON configuration files to customize:
- Validation rules and thresholds
- Input/output format settings
- Processing behavior
- Error handling options

## 📝 **Basic Configuration**

### **Creating a Configuration File**

Create a JSON file with your preferred settings:

```json
{
    "validate_sequences": true,
    "force_overwrite": false,
    "min_primer_length": 15,
    "max_primer_length": 35
}
```

### **Using Configuration Files**

```bash
# Use custom configuration
preprimer convert -i primers.tsv -o output/ -f artic --config my-config.json

# Configuration file path can be relative or absolute
preprimer convert -i primers.tsv -o output/ -f artic -c /path/to/config.json
```

## 🔧 **Configuration Sections**

### **1. Validation Settings**

Control primer and sequence validation:

```json
{
    "validation": {
        "validate_sequences": true,
        "check_primer_pairs": true,
        "allow_ambiguous_bases": false,
        "min_primer_length": 18,
        "max_primer_length": 32,
        "min_amplicon_size": 200,
        "max_amplicon_size": 500,
        "check_gc_content": true,
        "min_gc_content": 0.4,
        "max_gc_content": 0.6
    }
}
```

**Validation Options:**
- `validate_sequences` - Check DNA sequence validity
- `check_primer_pairs` - Validate forward/reverse primer pairs
- `allow_ambiguous_bases` - Allow IUPAC ambiguous nucleotides
- `min/max_primer_length` - Primer length constraints
- `min/max_amplicon_size` - Amplicon size constraints
- `check_gc_content` - Validate GC content
- `min/max_gc_content` - GC content range (0.0-1.0)

### **2. Processing Settings**

Control how PrePrimer processes data:

```json
{
    "processing": {
        "skip_invalid_primers": false,
        "normalize_sequences": true,
        "sort_by_position": true,
        "deduplicate_primers": false,
        "case_sensitive_names": false,
        "auto_assign_pools": false
    }
}
```

**Processing Options:**
- `skip_invalid_primers` - Skip primers that fail validation
- `normalize_sequences` - Convert to uppercase, remove whitespace
- `sort_by_position` - Sort primers by genomic position
- `deduplicate_primers` - Remove duplicate primer sequences
- `case_sensitive_names` - Treat primer names as case-sensitive
- `auto_assign_pools` - Automatically assign primers to pools

### **3. Output Settings**

Customize output file generation:

```json
{
    "output": {
        "force_overwrite": true,
        "create_reference": true,
        "include_metadata": true,
        "preserve_original_names": false,
        "add_version_suffix": false
    }
}
```

**Output Options:**
- `force_overwrite` - Overwrite existing files without prompting
- `create_reference` - Generate reference FASTA files
- `include_metadata` - Add metadata to output files
- `preserve_original_names` - Keep original primer names
- `add_version_suffix` - Add version suffix to file names

## 🧬 **Format-Specific Configuration**

### **VarVAMP Parser Settings**

```json
{
    "parsers": {
        "varvamp": {
            "header_variations": [
                "amplicon_name", 
                "amlicon_name",
                "amplicon_id"
            ],
            "separator": "\t",
            "skip_rows": 0,
            "expected_columns": [
                "amplicon_name",
                "primer_name", 
                "sequence",
                "start",
                "stop",
                "length",
                "gc_content",
                "tm",
                "penalty",
                "pool"
            ],
            "coordinate_system": "1-based"
        }
    }
}
```

### **ARTIC Parser Settings**

```json
{
    "parsers": {
        "artic": {
            "coordinate_system": "bed",
            "require_strand": true,
            "allow_overlaps": true,
            "validate_pool_names": true,
            "expected_chrom_name": "ref"
        }
    }
}
```

### **Olivar Parser Settings**

```json
{
    "parsers": {
        "olivar": {
            "forward_column": "fP",
            "reverse_column": "rP",
            "amplicon_id_column": "amplicon_id",
            "separator": ",",
            "create_amplicon_names": true,
            "pool_assignment_method": "alternating"
        }
    }
}
```

## 📤 **Output Format Configuration**

### **ARTIC Output Settings**

```json
{
    "writers": {
        "artic": {
            "include_reference": true,
            "version_directory": "V1",
            "coordinate_system": "bed",
            "chrom_name": "ref",
            "include_pool_column": true,
            "bed_score": 60
        }
    }
}
```

### **FASTA Output Settings**

```json
{
    "writers": {
        "fasta": {
            "line_width": 80,
            "include_pools": true,
            "include_coordinates": true,
            "include_amplicon_info": true,
            "header_format": ">{{name}} pool={{pool}} amplicon={{amplicon}} direction={{direction}} start={{start}} stop={{stop}}"
        }
    }
}
```

### **STS Output Settings**

```json
{
    "writers": {
        "sts": {
            "separator": "\t",
            "include_header": true,
            "columns": [
                "primer_name",
                "forward_primer", 
                "reverse_primer"
            ],
            "pair_naming": "amplicon"
        }
    }
}
```

## 🎨 **Preset Configurations**

### **Strict Validation**

For high-quality primer schemes:

```json
{
    "validation": {
        "validate_sequences": true,
        "check_primer_pairs": true,
        "allow_ambiguous_bases": false,
        "min_primer_length": 20,
        "max_primer_length": 30,
        "min_amplicon_size": 300,
        "max_amplicon_size": 400,
        "check_gc_content": true,
        "min_gc_content": 0.45,
        "max_gc_content": 0.55
    },
    "processing": {
        "skip_invalid_primers": false,
        "normalize_sequences": true,
        "sort_by_position": true
    }
}
```

### **Permissive Processing**

For experimental or draft primer schemes:

```json
{
    "validation": {
        "validate_sequences": false,
        "check_primer_pairs": false,
        "allow_ambiguous_bases": true,
        "min_primer_length": 10,
        "max_primer_length": 50
    },
    "processing": {
        "skip_invalid_primers": true,
        "normalize_sequences": true,
        "sort_by_position": false
    },
    "output": {
        "force_overwrite": true
    }
}
```

### **ARTIC Workflow**

Optimized for ARTIC minion workflows:

```json
{
    "validation": {
        "validate_sequences": true,
        "min_primer_length": 15,
        "max_primer_length": 35,
        "min_amplicon_size": 250,
        "max_amplicon_size": 450
    },
    "writers": {
        "artic": {
            "include_reference": true,
            "version_directory": "V1",
            "chrom_name": "ref",
            "bed_score": 60
        }
    },
    "output": {
        "create_reference": true
    }
}
```

### **Multi-Format Export**

For cross-platform compatibility:

```json
{
    "validation": {
        "validate_sequences": true,
        "normalize_sequences": true
    },
    "writers": {
        "artic": {
            "include_reference": true,
            "version_directory": "V1"
        },
        "fasta": {
            "line_width": 80,
            "include_pools": true,
            "include_coordinates": true
        },
        "sts": {
            "include_header": true,
            "separator": "\t"
        }
    },
    "output": {
        "include_metadata": true,
        "force_overwrite": true
    }
}
```

## 🌐 **Environment Variables**

Override configuration with environment variables:

### **General Settings**
```bash
# Default configuration directory
export PREPRIMER_CONFIG_DIR=~/.preprimer/config

# Default output directory
export PREPRIMER_OUTPUT_DIR=~/primer_schemes

# Logging level
export PREPRIMER_LOG_LEVEL=INFO
```

### **Processing Defaults**
```bash
# Enable validation by default
export PREPRIMER_VALIDATE=true

# Force overwrite by default
export PREPRIMER_FORCE=false

# Default output formats
export PREPRIMER_OUTPUT_FORMATS=artic,fasta
```

### **Format Detection**
```bash
# Disable auto-detection
export PREPRIMER_AUTO_DETECT=false

# Default fallback format
export PREPRIMER_FALLBACK_FORMAT=varvamp
```

## 🔧 **Configuration Hierarchy**

Configuration is applied in this order (later overrides earlier):

1. **Built-in defaults**
2. **Environment variables**
3. **Configuration file** (`--config`)
4. **Command-line options**

### **Example Priority**
```bash
# Environment variable
export PREPRIMER_VALIDATE=false

# Configuration file sets validation to true
{
    "validate_sequences": true
}

# Command line overrides both
preprimer convert --validate-sequences

# Result: validation is enabled (command line wins)
```

## 📋 **Configuration Templates**

### **COVID-19 Surveillance**
```json
{
    "validation": {
        "validate_sequences": true,
        "min_primer_length": 22,
        "max_primer_length": 28,
        "min_amplicon_size": 300,
        "max_amplicon_size": 400
    },
    "processing": {
        "sort_by_position": true,
        "normalize_sequences": true
    },
    "writers": {
        "artic": {
            "chrom_name": "MN908947.3",
            "include_reference": true
        }
    }
}
```

### **Influenza Sequencing**
```json
{
    "validation": {
        "validate_sequences": true,
        "allow_ambiguous_bases": true,
        "min_primer_length": 20,
        "max_primer_length": 32
    },
    "processing": {
        "auto_assign_pools": true
    },
    "writers": {
        "artic": {
            "chrom_name": "influenza"
        },
        "fasta": {
            "include_pools": true
        }
    }
}
```

## 🔍 **Validation Configuration**

### **Sequence Validation**
```json
{
    "sequence_validation": {
        "allowed_bases": ["A", "T", "G", "C"],
        "ambiguous_bases": ["N", "R", "Y", "S", "W", "K", "M", "D", "V", "H", "B"],
        "check_palindromes": false,
        "check_hairpins": false,
        "max_homopolymer_length": 6
    }
}
```

### **Primer Pair Validation**
```json
{
    "primer_pair_validation": {
        "check_tm_difference": true,
        "max_tm_difference": 5.0,
        "check_secondary_structures": false,
        "check_primer_dimers": false,
        "min_product_size": 100,
        "max_product_size": 2000
    }
}
```

## ⚠️ **Common Configuration Issues**

### **Invalid JSON**
```bash
# Error: Invalid JSON syntax
Error: JSON decode error at line 5: Expecting ',' delimiter

# Solution: Validate JSON syntax
python -m json.tool config.json
```

### **Unknown Configuration Keys**
```bash
# Error: Unknown configuration option
Warning: Unknown configuration key 'invalid_option' - ignoring

# Solution: Check documentation for valid keys
```

### **Type Mismatches**
```bash
# Error: Wrong value type
Error: 'min_primer_length' must be integer, got string

# Solution: Use correct data types
{
    "min_primer_length": 15,    // integer
    "validate_sequences": true   // boolean
}
```

## 💾 **Saving and Managing Configurations**

### **Configuration Directory Structure**
```
~/.preprimer/
├── config/
│   ├── default.json
│   ├── strict.json
│   ├── permissive.json
│   └── artic-workflow.json
└── logs/
    └── preprimer.log
```

### **Using Named Configurations**
```bash
# Save configuration with descriptive name
cp my-config.json ~/.preprimer/config/covid-surveillance.json

# Use named configuration
preprimer convert -i primers.tsv -o output/ -f artic -c covid-surveillance.json
```

---

## 🔗 **Related Documentation**

- **[CLI Reference](cli-reference.md)** - Command-line options
- **[Basic Usage](basic-usage.md)** - Essential workflows
- **[Python API](python-api-basics.md)** - Programmatic configuration
- **[Format Guide](supported-formats.md)** - Format-specific settings

**Configure PrePrimer for your specific workflow needs! ⚙️✨**