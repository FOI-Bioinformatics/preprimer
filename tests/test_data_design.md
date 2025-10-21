# PrePrimer Unified Test Data Design

## 📊 **Proposed Structure**

```
tests/test_data/
├── datasets/
│   ├── small/              # COVID-19: 5 amplicons, 10 primers
│   │   ├── reference.fasta
│   │   ├── varvamp.tsv     # VarVAMP format (13 fields)
│   │   ├── artic.scheme.bed # ARTIC BED format (7 fields)
│   │   ├── olivar.csv      # Olivar CSV format (13 fields)
│   │   ├── olivar.primer.bed # Olivar BED format (7 fields)
│   │   ├── sts.tsv         # STS format (4 fields)
│   │   └── metadata.yaml   # Dataset metadata
│   │
│   ├── medium/             # ASFV: 80 amplicons, 160 primers
│   │   ├── reference.fasta
│   │   ├── varvamp.tsv
│   │   ├── artic.scheme.bed
│   │   ├── olivar.csv
│   │   ├── olivar.primer.bed
│   │   ├── sts.tsv
│   │   └── metadata.yaml
│   │
│   └── large/              # Synthetic: 500 amplicons, 1000 primers
│       ├── reference.fasta
│       ├── varvamp.tsv
│       ├── artic.scheme.bed
│       ├── olivar.csv
│       ├── olivar.primer.bed
│       ├── sts.tsv
│       └── metadata.yaml
│
├── fixtures/
│   ├── malformed/          # Invalid files for error testing
│   │   ├── invalid_varvamp.tsv
│   │   ├── invalid_artic.bed
│   │   ├── invalid_olivar.csv
│   │   └── corrupt_reference.fasta
│   │
│   ├── edge_cases/         # Edge case scenarios
│   │   ├── single_amplicon.tsv
│   │   ├── overlapping_primers.bed
│   │   ├── non_standard_naming.csv
│   │   └── minimal_headers.tsv
│   │
│   └── minimal/            # Minimal valid examples
│       ├── minimal_varvamp.tsv
│       ├── minimal_artic.bed
│       ├── minimal_olivar.csv
│       └── minimal_reference.fasta
│
├── legacy/                 # Current files (for migration)
│   ├── ASFV_long/
│   ├── ASFV.scheme.bed
│   ├── ASFV.sts.tsv
│   ├── LR722600.1.fasta
│   └── olivar_examples/
│
└── README.md               # Documentation
```

## 🎯 **Design Principles**

### 1. **Data Set Consistency**
- **Same biological data** across all formats within each dataset
- **Enables accurate conversion testing** between formats
- **Supports cross-format validation** and comparison

### 2. **Scalable Testing**
- **Small dataset**: Fast unit tests, CI/CD pipelines
- **Medium dataset**: Integration testing, realistic scenarios  
- **Large dataset**: Performance testing, stress testing

### 3. **Format Completeness**
Every dataset includes all supported formats:
- **VarVAMP**: `.tsv` (13 fields with quality metrics)
- **ARTIC**: `.scheme.bed` (7 fields with sequences)
- **Olivar**: `.csv` + `.primer.bed` (dual format support)
- **STS**: `.tsv` (4 fields, amplicon-based)

### 4. **Comprehensive Test Coverage**
- **Valid data**: Standard format compliance
- **Malformed data**: Error handling validation
- **Edge cases**: Boundary conditions
- **Minimal examples**: Simplest valid cases

### 5. **Metadata-Driven**
Each dataset includes `metadata.yaml`:
```yaml
name: "COVID-19 Small Dataset"
organism: "SARS-CoV-2"
reference_id: "EPI_ISL_402124"
amplicon_count: 5
primer_count: 10
coverage_bp: 1500
description: "Small COVID-19 dataset for unit testing"
formats:
  varvamp: "13-field TSV with quality metrics"
  artic: "7-field BED with sequences"
  olivar: "CSV design + primer BED"
  sts: "4-field amplicon format"
```

## 🔄 **Format Specifications**

### **VarVAMP Format** (`.tsv`)
```
amplicon_name	amplicon_length	primer_name	pool	start	stop	seq	size	gc_best	temp_best	mean_gc	mean_temp	score
amplicon_1	300	FW_1	1	100	120	ATCGATCGATCGATCGATCG	20	0.5	60.0	0.52	58.5	85.2
amplicon_1	300	RW_1	1	380	400	CGATCGATCGATCGATCGAT	20	0.5	60.0	0.52	58.5	85.2
```

### **ARTIC Format** (`.scheme.bed`)
```
reference	start	end	name	pool	strand	sequence
EPI_ISL_402124	100	120	COVID19_400_1_LEFT_1	1	+	ATCGATCGATCGATCGATCG
EPI_ISL_402124	380	400	COVID19_400_1_RIGHT_1	1	-	CGATCGATCGATCGATCGAT
```

### **Olivar CSV Format** (`.csv`)
```
reference,amplicon_id,pool,fP,rP,start,insert_start,insert_end,end,amplicon,insert,fP_full,rP_full
EPI_ISL_402124,amplicon_1,1,ATCGATCGATCGATCGATCG,CGATCGATCGATCGATCGAT,100,120,380,400,<full_amplicon>,<insert>,<full_fP>,<full_rP>
```

### **Olivar BED Format** (`.primer.bed`)
```
reference	start	end	name	pool	strand	sequence
EPI_ISL_402124	100	120	amplicon_1_LEFT_1	1	+	ATCGATCGATCGATCGATCG
EPI_ISL_402124	380	400	amplicon_1_RIGHT_1	1	-	CGATCGATCGATCGATCGAT
```

### **STS Format** (`.tsv`)
```
amplicon_1	ATCGATCGATCGATCGATCG	CGATCGATCGATCGATCGAT	300
amplicon_2	GCTAGCTAGCTAGCTAGCTA	TAGCTAGCTAGCTAGCTAGT	350
```

## 🧪 **Test Integration Strategy**

### **Parametrized Testing**
```python
@pytest.fixture(params=["small", "medium", "large"])
def dataset_size(request):
    return request.param

@pytest.fixture(params=["varvamp", "artic", "olivar"])
def format_type(request):
    return request.param

def test_format_conversion(dataset_size, format_type):
    """Test conversion between all formats using same data."""
    dataset_path = test_data_dir / "datasets" / dataset_size
    input_file = dataset_path / f"{format_type}.tsv"
    # Test conversion to all other formats
```

### **Cross-Format Validation**
```python
def test_conversion_accuracy(dataset_size):
    """Verify data consistency across format conversions."""
    dataset_path = test_data_dir / "datasets" / dataset_size
    
    # Load same data in different formats
    varvamp_data = parse_varvamp(dataset_path / "varvamp.tsv")
    artic_data = parse_artic(dataset_path / "artic.scheme.bed")
    
    # Verify biological consistency
    assert same_primer_sequences(varvamp_data, artic_data)
    assert same_amplicon_coordinates(varvamp_data, artic_data)
```

## 📈 **Benefits**

1. **Conversion Testing**: Verify accuracy between formats
2. **Performance Scaling**: Test with different data sizes
3. **Error Handling**: Comprehensive malformed data testing
4. **Maintenance**: Single source of truth per dataset
5. **Documentation**: Self-documenting with metadata
6. **Extensibility**: Easy to add new formats or datasets

## 🔄 **Migration Strategy**

1. **Phase 1**: Create new structure alongside existing
2. **Phase 2**: Generate unified datasets from existing data
3. **Phase 3**: Update test fixtures to use new structure
4. **Phase 4**: Deprecate old structure
5. **Phase 5**: Remove legacy files

This unified structure provides the foundation for comprehensive, consistent testing across all PrePrimer tools.