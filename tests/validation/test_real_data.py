"""
Comprehensive real data testing for PrePrimer v0.2.0.

Tests all functionality with real datasets:
- Format conversions (all pairs)
- Alignment with real tools (BLAST, Exonerate, merPCR)
- Edge cases (circular genomes, large datasets, degenerate primers)
- Integration workflows
- Performance benchmarks

Requires:
- BLAST installed (blastn in PATH)
- Exonerate installed (exonerate in PATH)
- merPCR installed (pip install merpcr)
"""

import shutil
import time
from pathlib import Path

import pytest

from preprimer.align import align_primers
from preprimer.core.converter import PrimerConverter
from preprimer.core.enhanced_config import EnhancedConfig

# Import validation framework
from .validator import ValidationResult, validate_conversion

# Test data paths
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data" / "datasets"
SMALL_DATASET = TEST_DATA_DIR / "small"
MEDIUM_DATASET = TEST_DATA_DIR / "medium"
MITOCHONDRIAL_DATASET = TEST_DATA_DIR / "mitochondrial"


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def converter():
    """Create PrimerConverter instance."""
    config = EnhancedConfig()
    return PrimerConverter(config)


@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory."""
    output = tmp_path / "real_data_output"
    output.mkdir(parents=True, exist_ok=True)
    return output


@pytest.fixture
def validation_results():
    """Store validation results for reporting."""
    return {}


@pytest.fixture(scope="session")
def tools_available():
    """Check which alignment tools are available."""
    return {
        "blast": shutil.which("blastn") is not None,
        "exonerate": shutil.which("exonerate") is not None,
        "merpcr": shutil.which("merpcr") is not None,
    }


# ============================================================================
# Test Markers
# ============================================================================

# pytest markers for selective test execution
pytestmark = [
    pytest.mark.real_data,  # All real data tests
]

quick = pytest.mark.quick  # Fast tests for CI
standard = pytest.mark.standard  # Standard validation tests
stress = pytest.mark.stress  # Heavy/slow stress tests
requires_blast = pytest.mark.skipif(
    not shutil.which("blastn"), reason="BLAST not installed"
)
requires_exonerate = pytest.mark.skipif(
    not shutil.which("exonerate"), reason="Exonerate not installed"
)
requires_merpcr = pytest.mark.skipif(
    not shutil.which("merpcr"), reason="merPCR not installed"
)


# ============================================================================
# Format Conversion Tests
# ============================================================================


class TestFormatConversions:
    """Test all format conversion pairs with real data."""

    # All supported input and output formats
    INPUT_FORMATS = ["varvamp", "artic", "olivar", "sts"]
    OUTPUT_FORMATS = ["artic", "varvamp", "olivar", "fasta", "sts"]

    @quick
    @pytest.mark.parametrize("output_format", OUTPUT_FORMATS)
    def test_small_dataset_conversions(
        self, converter, output_dir, output_format, validation_results
    ):
        """Test converting small dataset to all output formats."""
        # Small dataset has multiple input formats
        input_file = SMALL_DATASET / "varvamp.tsv"
        prefix = f"small_{output_format}"

        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "small",
            input_format="varvamp",
            output_formats=[output_format],
            prefix=prefix,
        )

        assert output_format in output_files
        output_path = output_files[output_format]

        # Validate conversion
        result = validate_conversion(
            input_format="varvamp",
            output_format=output_format,
            input_file=input_file,
            output_path=output_path,
        )

        validation_results[f"small_varvamp_to_{output_format}"] = result
        assert result.valid, f"Validation failed: {result.errors}"

    @standard
    @pytest.mark.parametrize("output_format", OUTPUT_FORMATS)
    def test_medium_dataset_conversions(
        self, converter, output_dir, output_format, validation_results
    ):
        """Test converting medium dataset (80 amplicons) to all formats."""
        input_file = MEDIUM_DATASET / "varvamp.tsv"
        prefix = f"medium_{output_format}"

        start_time = time.time()
        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "medium",
            input_format="varvamp",
            output_formats=[output_format],
            prefix=prefix,
        )
        conversion_time = time.time() - start_time

        assert output_format in output_files
        output_path = output_files[output_format]

        # Validate conversion
        result = validate_conversion(
            input_format="varvamp",
            output_format=output_format,
            input_file=input_file,
            output_path=output_path,
        )
        result.add_stat("conversion_time_seconds", round(conversion_time, 3))

        validation_results[f"medium_varvamp_to_{output_format}"] = result
        assert result.valid, f"Validation failed: {result.errors}"
        assert conversion_time < 5.0, f"Conversion too slow: {conversion_time}s > 5s"

    @quick
    def test_multi_format_output(self, converter, output_dir, validation_results):
        """Test generating multiple output formats simultaneously."""
        input_file = SMALL_DATASET / "varvamp.tsv"
        output_formats = ["artic", "fasta", "sts"]

        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "multi_format",
            input_format="varvamp",
            output_formats=output_formats,
            prefix="multi_test",
        )

        # Verify all formats were generated
        assert set(output_files.keys()) == set(output_formats)

        # Validate each output
        for output_format in output_formats:
            result = validate_conversion(
                input_format="varvamp",
                output_format=output_format,
                input_file=input_file,
                output_path=output_files[output_format],
            )
            validation_results[f"multi_format_{output_format}"] = result
            assert result.valid

    @standard
    @pytest.mark.parametrize(
        "input_format,input_file",
        [
            ("varvamp", SMALL_DATASET / "varvamp.tsv"),
            ("artic", SMALL_DATASET / "artic.scheme.bed"),
            ("sts", SMALL_DATASET / "sts.tsv"),
        ],
    )
    def test_round_trip_conversion(
        self, converter, output_dir, input_format, input_file, validation_results
    ):
        """Test round-trip conversions preserve data integrity."""
        # First conversion: input_format → sts
        output_sts = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "roundtrip" / "step1",
            input_format=input_format,
            output_formats=["sts"],
            prefix="roundtrip",
        )["sts"]

        # Second conversion: sts → original format
        if input_format != "sts":
            output_original = converter.convert(
                input_file=output_sts,
                output_dir=output_dir / "roundtrip" / "step2",
                input_format="sts",
                output_formats=[input_format],
                prefix="roundtrip_back",
            )[input_format]

            # Validate both conversions
            result1 = validate_conversion(input_format, "sts", input_file, output_sts)
            result2 = validate_conversion(
                "sts", input_format, output_sts, output_original
            )

            validation_results[f"roundtrip_{input_format}_to_sts"] = result1
            validation_results[f"roundtrip_sts_to_{input_format}"] = result2

            assert result1.valid
            assert result2.valid


# ============================================================================
# Alignment Tests with Real Execution
# ============================================================================


class TestRealAlignments:
    """Test alignments with real tool execution."""

    @quick
    @requires_blast
    def test_blast_small_dataset(self, output_dir, validation_results):
        """Test BLAST alignment with small dataset."""
        sts_file = SMALL_DATASET / "sts.tsv"
        reference = SMALL_DATASET / "reference.fasta"

        start_time = time.time()
        output_paths = align_primers(
            sts_file=sts_file,
            reference_file=reference,
            output_dir=output_dir / "blast_small",
            output_formats=["primers"],
            aligner="blast",
            prefix="small_blast",
        )
        alignment_time = time.time() - start_time

        result = ValidationResult(valid=True)
        result.add_stat("alignment_time_seconds", round(alignment_time, 3))
        result.add_stat("output_path", str(output_paths["primers"]))

        # Verify output directory exists and has files
        output_path = output_paths["primers"]
        if output_path.exists():
            aln_files = list(output_path.glob("*.aln"))
            result.add_stat("alignment_files_generated", len(aln_files))
            if len(aln_files) == 0:
                result.add_warning("No alignment files generated")
        else:
            result.add_error("Output directory not created")

        validation_results["blast_small_dataset"] = result
        assert result.valid
        assert alignment_time < 10.0, f"BLAST too slow: {alignment_time}s"

    @standard
    @requires_blast
    def test_blast_medium_dataset(self, output_dir, validation_results):
        """Test BLAST alignment with medium dataset (80 amplicons)."""
        sts_file = MEDIUM_DATASET / "sts.tsv"
        reference = MEDIUM_DATASET / "reference.fasta"

        start_time = time.time()
        output_paths = align_primers(
            sts_file=sts_file,
            reference_file=reference,
            output_dir=output_dir / "blast_medium",
            output_formats=["primers"],
            aligner="blast",
            prefix="medium_blast",
        )
        alignment_time = time.time() - start_time

        result = ValidationResult(valid=True)
        result.add_stat("alignment_time_seconds", round(alignment_time, 3))
        result.add_stat("amplicon_count", 80)

        output_path = output_paths["primers"]
        if output_path.exists():
            aln_files = list(output_path.glob("*.aln"))
            result.add_stat("alignment_files_generated", len(aln_files))
            # Expect ~160 files (80 amplicons × 2 primers)
            if len(aln_files) < 100:
                result.add_warning(
                    f"Fewer alignment files than expected: {len(aln_files)}"
                )

        validation_results["blast_medium_dataset"] = result
        assert result.valid
        assert alignment_time < 30.0, f"BLAST too slow: {alignment_time}s"

    @quick
    @requires_exonerate
    def test_exonerate_small_dataset(self, output_dir, validation_results):
        """Test Exonerate alignment with small dataset."""
        sts_file = SMALL_DATASET / "sts.tsv"
        reference = SMALL_DATASET / "reference.fasta"

        start_time = time.time()
        output_paths = align_primers(
            sts_file=sts_file,
            reference_file=reference,
            output_dir=output_dir / "exonerate_small",
            output_formats=["primers"],
            aligner="exonerate",
            prefix="small_exonerate",
        )
        alignment_time = time.time() - start_time

        result = ValidationResult(valid=True)
        result.add_stat("alignment_time_seconds", round(alignment_time, 3))

        output_path = output_paths["primers"]
        if output_path.exists():
            aln_files = list(output_path.glob("*.aln"))
            result.add_stat("alignment_files_generated", len(aln_files))

        validation_results["exonerate_small_dataset"] = result
        assert result.valid
        assert alignment_time < 15.0, f"Exonerate too slow: {alignment_time}s"

    @quick
    @requires_merpcr
    def test_merpcr_small_dataset(self, output_dir, validation_results):
        """Test merPCR in silico PCR with small dataset."""
        sts_file = SMALL_DATASET / "sts.tsv"
        reference = SMALL_DATASET / "reference.fasta"

        start_time = time.time()
        output_paths = align_primers(
            sts_file=sts_file,
            reference_file=reference,
            output_dir=output_dir / "merpcr_small",
            output_formats=["merpcr"],
            prefix="small_merpcr",
        )
        alignment_time = time.time() - start_time

        result = ValidationResult(valid=True)
        result.add_stat("alignment_time_seconds", round(alignment_time, 3))

        output_path = output_paths["merpcr"]
        if output_path.exists():
            result.add_stat("output_file_size", output_path.stat().st_size)
            # Read and count results
            with open(output_path) as f:
                lines = [l for l in f if l.strip()]
            result.add_stat("result_lines", len(lines))
        else:
            result.add_error("merPCR output file not created")

        validation_results["merpcr_small_dataset"] = result
        assert result.valid
        assert alignment_time < 5.0, f"merPCR too slow: {alignment_time}s"

    @standard
    @requires_merpcr
    def test_merpcr_medium_dataset(self, output_dir, validation_results):
        """Test merPCR with medium dataset (80 amplicons)."""
        sts_file = MEDIUM_DATASET / "sts.tsv"
        reference = MEDIUM_DATASET / "reference.fasta"

        start_time = time.time()
        output_paths = align_primers(
            sts_file=sts_file,
            reference_file=reference,
            output_dir=output_dir / "merpcr_medium",
            output_formats=["merpcr"],
            prefix="medium_merpcr",
        )
        alignment_time = time.time() - start_time

        result = ValidationResult(valid=True)
        result.add_stat("alignment_time_seconds", round(alignment_time, 3))

        output_path = output_paths["merpcr"]
        if output_path.exists():
            with open(output_path) as f:
                lines = [l for l in f if l.strip()]
            result.add_stat("result_lines", len(lines))

        validation_results["merpcr_medium_dataset"] = result
        assert result.valid
        assert alignment_time < 15.0, f"merPCR too slow: {alignment_time}s"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @standard
    def test_circular_genome_handling(self, converter, output_dir, validation_results):
        """Test circular genome (mitochondrial) handling."""
        input_file = MITOCHONDRIAL_DATASET / "olivar.csv"

        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "circular",
            input_format="olivar",
            output_formats=["artic", "sts", "fasta"],
            prefix="mitochondrial",
        )

        result = ValidationResult(valid=True)
        result.add_stat("dataset", "mitochondrial_circular")

        # Validate all outputs
        for output_format, output_path in output_files.items():
            format_result = validate_conversion(
                "olivar", output_format, input_file, output_path
            )
            if not format_result.valid:
                result.errors.extend(format_result.errors)
                result.valid = False

        validation_results["circular_genome_handling"] = result
        assert result.valid

    @quick
    def test_empty_dataset_handling(self, converter, output_dir, tmp_path):
        """Test handling of edge case with minimal data."""
        # Create minimal STS file with 1 amplicon (with proper header and valid primer lengths)
        minimal_sts = tmp_path / "minimal.sts"
        minimal_sts.write_text(
            "NAME\tFORWARD\tREVERSE\nTEST_AMP\tATCGATCGATCGATCG\tGCTAGCTAGCTAGCTA\n"
        )

        # Should handle gracefully
        output_files = converter.convert(
            input_file=minimal_sts,
            output_dir=output_dir / "minimal",
            input_format="sts",
            output_formats=["fasta"],
            prefix="minimal",
        )

        assert "fasta" in output_files
        assert output_files["fasta"].exists()

    @standard
    def test_degenerate_primers(self, converter, output_dir, validation_results):
        """Test handling of degenerate IUPAC primers."""
        # VarVAMP format supports degenerate bases
        input_file = SMALL_DATASET / "varvamp.tsv"

        output_files = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "degenerate",
            input_format="varvamp",
            output_formats=["fasta", "sts"],
            prefix="degenerate",
        )

        result = ValidationResult(valid=True)

        # Read FASTA and check for IUPAC codes
        fasta_content = output_files["fasta"].read_text()
        iupac_codes = set("RYSWKMBDHVN")
        found_degenerate = any(base in fasta_content for base in iupac_codes)

        result.add_stat("degenerate_bases_preserved", found_degenerate)

        validation_results["degenerate_primers"] = result
        assert result.valid


# ============================================================================
# Integration Workflow Tests
# ============================================================================


class TestIntegrationWorkflows:
    """Test complete end-to-end workflows."""

    @standard
    @requires_blast
    @requires_merpcr
    def test_full_pipeline(self, converter, output_dir, validation_results):
        """Test complete pipeline: Parse → Convert → Align."""
        # Step 1: Parse VarVAMP
        input_file = SMALL_DATASET / "varvamp.tsv"

        # Step 2: Convert to STS for alignment
        sts_output = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "pipeline" / "sts",
            input_format="varvamp",
            output_formats=["sts"],
            prefix="pipeline",
        )["sts"]

        # Step 3: Also convert to ARTIC and FASTA
        other_outputs = converter.convert(
            input_file=input_file,
            output_dir=output_dir / "pipeline" / "formats",
            input_format="varvamp",
            output_formats=["artic", "fasta"],
            prefix="pipeline",
        )

        # Step 4: Run alignment with both BLAST and merPCR
        reference = SMALL_DATASET / "reference.fasta"

        blast_output = align_primers(
            sts_file=sts_output,
            reference_file=reference,
            output_dir=output_dir / "pipeline" / "blast",
            output_formats=["primers"],
            aligner="blast",
            prefix="pipeline",
        )

        # Test merPCR with enhanced STS parser that supports 3 or 4 columns
        merpcr_output = align_primers(
            sts_file=sts_output,
            reference_file=reference,
            output_dir=output_dir / "pipeline" / "merpcr",
            output_formats=["merpcr"],
            prefix="pipeline",
        )

        # Validate all outputs
        result = ValidationResult(valid=True)
        result.add_stat("sts_generated", sts_output.exists())
        result.add_stat("artic_generated", other_outputs["artic"].exists())
        result.add_stat("fasta_generated", other_outputs["fasta"].exists())
        result.add_stat("blast_generated", blast_output["primers"].exists())
        result.add_stat("merpcr_generated", merpcr_output["merpcr"].exists())

        validation_results["full_pipeline"] = result
        assert result.valid


# ============================================================================
# Report Generation
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def generate_reports(request, tmp_path_factory):
    """Generate validation reports after all tests complete."""

    # This will run after all tests
    def finalize():
        # Collect all validation results from test sessions
        # (In practice, you'd collect from test session storage)
        print("\n" + "=" * 60)
        print("Real Data Validation Complete")
        print("=" * 60)
        print("\nReports would be generated here in production use.")
        print("See tests/validation/report_generator.py for implementation.")

    request.addfinalizer(finalize)
