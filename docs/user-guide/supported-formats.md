# 🧬 Supported Formats Guide

Complete guide to all input and output formats supported by PrePrimer.

## 📥 **Input Formats**

PrePrimer supports three major primer design tool formats for input.

### **VarVAMP Format**

**Description:** Tab-separated values format from the VarVAMP primer design tool.

**File Extensions:** `.tsv`, `.txt`

**Format Characteristics:**
- Tab-separated values with headers
- One primer per row
- Includes amplicon metadata and quality metrics
- Commonly used for SARS-CoV-2 and other viral genome primer schemes

#### **File Structure**
```tsv
amplicon_name	primer_name	sequence	start	stop	length	gc_content	tm	penalty	pool
ASFV_1	ASFV_1_LEFT	ATCGATCGATCGATCGATCG	100	120	20	0.5	60.2	1.5	1
ASFV_1	ASFV_1_RIGHT	CGATCGATCGATCGATCGAT	380	400	20	0.5	59.8	1.2	1
ASFV_2	ASFV_2_LEFT	GCTAGCTAGCTAGCTAGCTA	250	270	20	0.5	60.5	1.8	2
ASFV_2	ASFV_2_RIGHT	TAGCTAGCTAGCTAGCTAGC	530	550	20	0.5	60.1	1.6	2
```

#### **Required Columns**
- `amplicon_name` - Unique identifier for amplicon
- `primer_name` - Unique primer identifier  
- `sequence` - DNA primer sequence (5' to 3')
- `start` - Primer start coordinate (1-based)
- `stop` - Primer end coordinate (1-based)
- `pool` - Pool assignment (1, 2, etc.)

#### **Optional Columns**
- `length` - Primer length in base pairs
- `gc_content` - GC content ratio (0.0-1.0)
- `tm` - Melting temperature in Celsius
- `penalty` - Primer design penalty score

#### **Example Usage**
```bash
# Auto-detect VarVAMP format
preprimer convert --input varvamp_output.tsv --output-dir schemes/ --output-formats artic

# Force VarVAMP format
preprimer convert --input ambiguous_file.txt --format varvamp --output-formats artic
```

### **ARTIC Format**

**Description:** BED format used by ARTIC tools for tiled amplicon sequencing workflows.

**File Extensions:** `.bed`, `.scheme.bed`

**Format Characteristics:**
- Standard BED format with 6 columns
- 0-based coordinates (BED convention)
- Primer names encode amplicon and direction
- Compatible with existing ARTIC workflows

#### **File Structure**
```bed
ref	99	119	ASFV_1_LEFT	60	+
ref	379	399	ASFV_1_RIGHT	60	-
ref	249	269	ASFV_2_LEFT	60	+
ref	529	549	ASFV_2_RIGHT	60	-
```

#### **Column Specification**
1. `chrom` - Reference sequence name (usually "ref")
2. `start` - Primer start coordinate (0-based, inclusive)
3. `stop` - Primer end coordinate (0-based, exclusive)  
4. `name` - Primer name (AMPLICON_DIRECTION format)
5. `score` - BED score (typically 60)
6. `strand` - Strand orientation (+ for forward, - for reverse)

#### **Naming Convention**
- Forward primers: `AMPLICON_LEFT`
- Reverse primers: `AMPLICON_RIGHT`
- Pool information encoded in amplicon names or separate file

#### **Example Usage**
```bash
# Convert ARTIC BED file
preprimer convert --input primers.scheme.bed --output-formats fasta sts

# Get information about ARTIC file
preprimer info existing_scheme.bed
```

### **Olivar Format**

**Description:** CSV format from Olivar primer design tool with row-based primer pairs.

**File Extension:** `.csv`

**Format Characteristics:**
- Comma-separated values with headers
- One amplicon per row (forward and reverse primers in same row)
- Includes amplicon coordinates and primer sequences
- Common for variant-aware primer design

#### **File Structure**
```csv
amplicon_id,chrom,pool,start,end,fP,rP
COVID_amplicon_1,EPI_ISL_402124,1,100,380,ATCGATCGATCGATCGATCG,CGATCGATCGATCGATCGAT
COVID_amplicon_2,EPI_ISL_402124,2,250,530,GCTAGCTAGCTAGCTAGCTA,TAGCTAGCTAGCTAGCTAGC
COVID_amplicon_3,EPI_ISL_402124,1,400,680,TTTTAAAAAGGGGCCCCCC,CCCCGGGGAAAAATTTTTT
COVID_amplicon_4,EPI_ISL_402124,2,550,830,ATATATATATATATATAT,CGCGCGCGCGCGCGCG
COVID_amplicon_5,EPI_ISL_402124,1,700,980,TGATCGATCGATCGATCG,ACGTACGTACGTACGTAC
```

#### **Required Columns**
- `amplicon_id` - Unique amplicon identifier
- `fP` - Forward primer sequence (5' to 3')
- `rP` - Reverse primer sequence (5' to 3')
- `pool` - Pool assignment

#### **Optional Columns**
- `chrom` - Reference chromosome/sequence
- `start` - Amplicon start coordinate
- `end` - Amplicon end coordinate

#### **Example Usage**
```bash
# Convert Olivar CSV
preprimer convert --input olivar-design.csv --output-formats artic fasta

# Check Olivar file details
preprimer info olivar_primers.csv
```

## 📤 **Output Formats**

PrePrimer converts to five different output formats for maximum compatibility and bidirectional conversion.

### **ARTIC BED Format**

**Description:** ARTIC-compatible BED format for tiled amplicon workflows.

**File Extension:** `.scheme.bed`

**Use Cases:**
- Direct use with `artic minion` and `artic medaka`
- Integration with existing ARTIC workflows
- Nanopore sequencing primer schemes

#### **Output Structure**
```
output_dir/
└── artic/
    └── PROJECT_NAME/
        └── V1/
            ├── PROJECT_NAME.scheme.bed
            └── PROJECT_NAME.reference.fasta
```

#### **File Format**
```bed
ref	99	119	PROJECT_1_LEFT	1	+
ref	379	399	PROJECT_1_RIGHT	1	-
ref	249	269	PROJECT_2_LEFT	2	+
ref	529	549	PROJECT_2_RIGHT	2	-
```

#### **Features**
- 0-based BED coordinates
- Pool information encoded in score column
- Compatible with ARTIC directory structure
- Includes reference FASTA when available

#### **Usage with ARTIC**
```bash
# Convert to ARTIC format
preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic --prefix SARS_CoV_2

# Use with ARTIC minion
artic minion SARS_CoV_2 data/ --scheme-directory schemes/artic/
```

### **FASTA Format**

**Description:** Multi-FASTA format with detailed primer information in headers.

**File Extension:** `.fasta`

**Use Cases:**
- In-silico primer validation
- Sequence analysis and BLAST searches
- Custom bioinformatics pipelines
- Primer database creation

#### **Output Structure**
```
output_dir/
└── fasta/
    └── PROJECT_NAME.fasta
```

#### **File Format**
```fasta
>PROJECT_1_LEFT pool=1 amplicon=1 direction=forward start=100 stop=120
ATCGATCGATCGATCGATCG
>PROJECT_1_RIGHT pool=1 amplicon=1 direction=reverse start=380 stop=400
CGATCGATCGATCGATCGAT
>PROJECT_2_LEFT pool=2 amplicon=2 direction=forward start=250 stop=270
GCTAGCTAGCTAGCTAGCTA
>PROJECT_2_RIGHT pool=2 amplicon=2 direction=reverse start=530 stop=550
TAGCTAGCTAGCTAGCTAGC
```

#### **Header Information**
- `pool` - Pool assignment number
- `amplicon` - Amplicon identifier
- `direction` - Primer direction (forward/reverse)
- `start` - Start coordinate (1-based)
- `stop` - End coordinate (1-based)

#### **Customization Options**
```json
{
    "writers": {
        "fasta": {
            "line_width": 80,
            "include_pools": true,
            "include_coordinates": true,
            "header_format": ">{{name}} pool={{pool}} amplicon={{amplicon}}"
        }
    }
}
```

### **STS Format**

**Description:** Tab-separated format for Sequence Tagged Sites (STS) and in-silico PCR validation.

**File Extension:** `.sts.tsv`

**Use Cases:**
- In-silico PCR with e-PCR or me-pcr
- Amplicon prediction and validation
- Cross-reference with genome databases
- Quality control workflows

#### **Output Structure**
```
output_dir/
└── sts/
    └── PROJECT_NAME.sts.tsv
```

#### **File Format**
```tsv
primer_name	forward_primer	reverse_primer
PROJECT_1	ATCGATCGATCGATCGATCG	CGATCGATCGATCGATCGAT
PROJECT_2	GCTAGCTAGCTAGCTAGCTA	TAGCTAGCTAGCTAGCTAGC
PROJECT_3	TTTTAAAAAGGGGCCCCCC	CCCCGGGGAAAAATTTTTT
```

#### **Column Specification**
1. `primer_name` - Amplicon/primer pair name
2. `forward_primer` - Forward primer sequence (5' to 3')
3. `reverse_primer` - Reverse primer sequence (5' to 3')

#### **Usage with e-PCR**
```bash
# Convert to STS format
preprimer convert --input primers.tsv --output-formats sts --prefix MyVirus

# Use with e-PCR for validation
e-PCR -S reference.fasta -N primers.sts.tsv -o results.txt
```

### **VarVAMP TSV Format**

**Description:** VarVAMP-compatible tab-separated format for primer design workflows.

**File Extension:** `.tsv`

**Use Cases:**
- VarVAMP primer design tool input
- Primer scheme analysis and validation
- Cross-platform primer data exchange
- Research and development workflows

#### **Output Structure**
```
output_dir/
└── varvamp/
    └── PROJECT_NAME.tsv
```

#### **File Format**
```tsv
amplicon_name	primer_name	sequence	start	stop	length	gc_content	tm	penalty	pool
COVID_1	COVID_1_F	ATCGATCGATCGATCGATCG	100	120	20	0.5	60.2	1.5	1
COVID_1	COVID_1_R	CGATCGATCGATCGATCGAT	380	400	20	0.5	59.8	1.2	1
COVID_2	COVID_2_F	GCTAGCTAGCTAGCTAGCTA	250	270	20	0.5	60.5	1.8	2
COVID_2	COVID_2_R	TAGCTAGCTAGCTAGCTAGC	530	550	20	0.5	60.1	1.6	2
```

#### **Column Specification**
- `amplicon_name` - Amplicon identifier
- `primer_name` - Unique primer name
- `sequence` - Primer DNA sequence (5' to 3')
- `start` - Start coordinate (1-based)
- `stop` - End coordinate (1-based)
- `length` - Primer length in base pairs
- `gc_content` - GC content ratio (0.0-1.0)
- `tm` - Melting temperature in Celsius
- `penalty` - Primer design penalty score
- `pool` - Pool assignment number

### **Olivar CSV Format**

**Description:** Olivar-compatible comma-separated format for variant-aware primer design.

**File Extension:** `.csv`

**Use Cases:**
- Olivar primer design tool input
- Variant-aware primer schemes
- Research primer development
- Cross-platform compatibility

#### **Output Structure**
```
output_dir/
└── olivar/
    └── PROJECT_NAME.csv
```

#### **File Format**
```csv
amplicon_id,chrom,pool,start,end,fP,rP
COVID_amplicon_1,EPI_ISL_402124,1,100,380,ATCGATCGATCGATCGATCG,CGATCGATCGATCGATCGAT
COVID_amplicon_2,EPI_ISL_402124,2,250,530,GCTAGCTAGCTAGCTAGCTA,TAGCTAGCTAGCTAGCTAGC
```

#### **Column Specification**
- `amplicon_id` - Unique amplicon identifier
- `chrom` - Reference chromosome/sequence name
- `pool` - Pool assignment number
- `start` - Amplicon start coordinate
- `end` - Amplicon end coordinate
- `fP` - Forward primer sequence (5' to 3')
- `rP` - Reverse primer sequence (5' to 3')

## 🔄 **Format Conversion Matrix**

**Complete bidirectional conversion support:**

| Input → Output | ARTIC | FASTA | STS | VarVAMP | Olivar |
|----------------|-------|-------|-----|---------|--------|
| **VarVAMP** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **ARTIC** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Olivar** | ✅ | ✅ | ✅ | ✅ | ✅ |

**🎉 All 15 conversion pathways supported!**

### **Conversion Examples**

**VarVAMP to All Formats:**
```bash
preprimer convert --input varvamp_output.tsv \
                 --output-dir multi_format/ \
                 --output-formats artic fasta sts varvamp olivar \
                 --prefix SARS_CoV_2
```

**ARTIC to VarVAMP and Olivar (Bidirectional):**
```bash
preprimer convert --input existing.scheme.bed \
                 --output-dir converted/ \
                 --output-formats varvamp olivar \
                 --prefix ARTIC_to_Others
```

**Olivar to VarVAMP (Cross-Platform):**
```bash
preprimer convert --input olivar-design.csv \
                 --output-dir cross_platform/ \
                 --output-formats varvamp artic \
                 --prefix Olivar_to_VarVAMP
```

**Full Round-Trip Conversion:**
```bash
# Start with VarVAMP
preprimer convert --input primers.tsv --output-formats olivar --prefix Step1

# Convert Olivar to ARTIC  
preprimer convert --input Step1.csv --output-formats artic --prefix Step2

# Convert ARTIC back to VarVAMP
preprimer convert --input Step2.scheme.bed --output-formats varvamp --prefix Step3

# Result: VarVAMP → Olivar → ARTIC → VarVAMP (full round-trip!)
```

## 🔍 **Format Detection**

PrePrimer automatically detects input formats based on:

### **File Extensions**
- `.tsv`, `.txt` → VarVAMP
- `.bed`, `.scheme.bed` → ARTIC
- `.csv` → Olivar

### **Header Analysis**
```python
# VarVAMP detection
headers = ["amplicon_name", "primer_name", "sequence", "start", "stop"]

# ARTIC detection  
bed_format = tab_separated and 6_columns and numeric_coordinates

# Olivar detection
headers = ["amplicon_id", "fP", "rP"] or similar_variations
```

### **Content Validation**
- Column count and types
- Coordinate format (0-based vs 1-based)
- Sequence validity
- Required field presence

### **Manual Format Override**
```bash
# Force specific format when detection fails
preprimer convert --input ambiguous.txt --format varvamp --output-formats artic

# Check what PrePrimer detected
preprimer info mystery_file.csv
```

## 📊 **Format Comparison**

| Feature | VarVAMP | ARTIC | Olivar |
|---------|---------|--------|--------|
| **Format** | TSV | BED | CSV |
| **Coordinates** | 1-based | 0-based | Variable |
| **Primer Layout** | One per row | One per row | Pair per row |
| **Pool Info** | Column | Name/separate | Column |
| **Quality Metrics** | Yes | No | Limited |
| **Reference** | Optional | Required | Optional |

### **Coordinate System Differences**

**VarVAMP (1-based):**
```
Sequence: ATCGATCG...
Position: 12345678...
Primer:   ^^^^      (start=1, stop=4)
```

**ARTIC BED (0-based):**
```  
Sequence: ATCGATCG...
Position: 01234567...
Primer:   ^^^^      (start=0, stop=4)
```

**Coordinate Conversion:**
```python
# VarVAMP to BED
bed_start = varvamp_start - 1
bed_stop = varvamp_stop  

# BED to VarVAMP
varvamp_start = bed_start + 1
varvamp_stop = bed_stop
```

## 🎨 **Custom Format Support**

### **Adding New Input Formats**

Create a custom parser by implementing the `PrimerParser` interface:

```python
from preprimer.core.interfaces import PrimerParser, PrimerData, AmpliconData

class MyCustomParser(PrimerParser):
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file."""
        return file_path.suffix == '.custom'
    
    def parse(self, file_path: Path, prefix: str = "") -> List[AmpliconData]:
        """Parse custom format and return amplicon data."""
        # Implementation here
        pass
```

### **Register Custom Parser**
```python
from preprimer.core.registry import parser_registry

# Register your custom parser
parser_registry.register('custom', MyCustomParser())
```

## ⚠️ **Format Limitations**

### **VarVAMP Format**
- Requires specific column headers (case-sensitive by default)
- Tab-separated only (not space-separated)
- Pool information must be numeric
- Coordinates must be 1-based integers

### **ARTIC Format**
- Must follow BED format specification exactly
- Requires 6 columns minimum
- Strand column must be '+' or '-'
- Score column typically ignored but should be numeric

### **Olivar Format**
- Forward and reverse primers must be in same row
- Column names may vary (fP, rP, forward_primer, reverse_primer)
- Pool assignment may be missing (auto-assigned)
- Coordinates optional but helpful for validation

## 🔧 **Troubleshooting Format Issues**

### **Format Detection Failed**
```bash
# Problem: "Could not detect input format"
# Solution: Force format explicitly
preprimer convert --input file.txt --format varvamp --output-formats artic
```

### **Column Header Mismatches**  
```bash
# Problem: "Missing required column 'amplicon_name'"
# Solution: Check spelling, configure alternate headers
{
    "parsers": {
        "varvamp": {
            "header_variations": ["amplicon_name", "amlicon_name", "amplicon_id"]
        }
    }
}
```

### **Coordinate System Errors**
```bash
# Problem: "Invalid coordinates: start > stop"
# Solution: Check coordinate system (0-based vs 1-based)
preprimer info problematic_file.bed --detailed
```

### **Invalid Sequences**
```bash
# Problem: "Invalid DNA sequence characters"
# Solution: Enable sequence validation to identify issues
preprimer convert --input primers.tsv --validate-sequences --output-formats artic
```

---

## 🔗 **Related Documentation**

- **[Basic Usage](basic-usage.md)** - Converting between formats
- **[CLI Reference](cli-reference.md)** - Command-line options
- **[Configuration](configuration.md)** - Format-specific settings
- **[Quick Start Guide](quick-start.md)** - Your first format conversion

**Master all primer formats for seamless conversion workflows! 🧬✨**