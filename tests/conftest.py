"""
Pytest configuration and shared fixtures for PrePrimer tests.

This module provides shared test configuration, fixtures, and utilities
for harmonized testing across all parser types using the unified test data structure.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

# Import and register all components
import preprimer.parsers  # noqa: E402, F401
import preprimer.writers  # noqa: E402, F401
from preprimer.core.enhanced_config import EnhancedConfig
from preprimer.core.registry import parser_registry, writer_registry


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def unified_datasets_dir(test_data_dir):
    """Path to unified datasets directory."""
    return test_data_dir / "datasets"


@pytest.fixture(scope="session")
def test_fixtures_dir(test_data_dir):
    """Path to test fixtures directory."""
    return test_data_dir / "fixtures"


@pytest.fixture(scope="session")
def legacy_data_dir(test_data_dir):
    """Path to legacy test data directory."""
    return test_data_dir / "legacy"


# Unified dataset fixtures
@pytest.fixture(scope="session", params=["small", "medium"])
def dataset_size(request):
    """Parametrized fixture for dataset sizes."""
    return request.param


@pytest.fixture(scope="session")
def small_dataset(unified_datasets_dir):
    """Small dataset (COVID-19, 5 amplicons)."""
    dataset_dir = unified_datasets_dir / "small"
    metadata_file = dataset_dir / "metadata.yaml"

    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)

    return {
        "name": "small",
        "dir": dataset_dir,
        "metadata": metadata,
        "reference": dataset_dir / "reference.fasta",
        "varvamp": dataset_dir / "varvamp.tsv",
        "artic": dataset_dir / "artic.scheme.bed",
        "olivar_csv": dataset_dir / "olivar.csv",
        "olivar_bed": dataset_dir / "olivar.primer.bed",
        "sts": dataset_dir / "sts.tsv",
        "expected_amplicons": metadata.get("amplicon_count", 5),
        "expected_primers": metadata.get("primer_count", 10),
        "organism": metadata.get("organism", "SARS-CoV-2"),
        "prefix": "COVID19",
    }


@pytest.fixture(scope="session")
def medium_dataset(unified_datasets_dir):
    """Medium dataset (ASFV, 80 amplicons)."""
    dataset_dir = unified_datasets_dir / "medium"
    metadata_file = dataset_dir / "metadata.yaml"

    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)

    return {
        "name": "medium",
        "dir": dataset_dir,
        "metadata": metadata,
        "reference": dataset_dir / "reference.fasta",
        "varvamp": dataset_dir / "varvamp.tsv",
        "artic": dataset_dir / "artic.scheme.bed",
        "olivar_csv": dataset_dir / "olivar.csv",
        "olivar_bed": dataset_dir / "olivar.primer.bed",
        "sts": dataset_dir / "sts.tsv",
        "expected_amplicons": metadata.get("amplicon_count", 80),
        "expected_primers": metadata.get("primer_count", 160),
        "organism": metadata.get("organism", "ASFV"),
        "prefix": "ASFV",
    }


@pytest.fixture(scope="session")
def dataset(request, small_dataset, medium_dataset):
    """Dynamic dataset fixture based on parameter."""
    dataset_name = getattr(request, "param", "small")
    if dataset_name == "small":
        return small_dataset
    elif dataset_name == "medium":
        return medium_dataset
    else:
        pytest.skip(f"Unknown dataset: {dataset_name}")


# Format-specific fixtures
@pytest.fixture(params=["varvamp", "artic", "olivar"])
def format_type(request):
    """Parametrized fixture for format types."""
    return request.param


@pytest.fixture(scope="session")
def unified_parser_test_data(request, unified_datasets_dir):
    """
    Unified parametrized fixture providing test data for all parsers.

    This replaces the old parser_test_data fixture with the new unified structure.
    """
    # Get parameters (format and dataset size)
    format_param = getattr(request, "param", "varvamp")

    # Support both old parameter style and new tuple style
    if isinstance(format_param, tuple):
        format_name, dataset_name = format_param
    else:
        format_name = format_param
        dataset_name = "small"  # Default to small dataset

    dataset_dir = unified_datasets_dir / dataset_name
    metadata_file = dataset_dir / "metadata.yaml"

    # Load metadata
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)

    # File mappings
    file_mappings = {
        "varvamp": dataset_dir / "varvamp.tsv",
        "artic": dataset_dir / "artic.scheme.bed",
        "olivar": dataset_dir / "olivar.csv",
    }

    reference_file = dataset_dir / "reference.fasta"
    test_file = file_mappings.get(format_name)

    if not test_file or not test_file.exists():
        pytest.skip(
            f"Test file not available for {format_name} in {dataset_name}: {test_file}"
        )

    return {
        "format": format_name,
        "dataset": dataset_name,
        "file": test_file,
        "reference": reference_file if reference_file.exists() else None,
        "expected_amplicons": metadata.get("amplicon_count", 5),
        "expected_primers": metadata.get("primer_count", 10),
        "prefix": metadata.get("organism", "TEST"),
        "metadata": metadata,
    }


# Legacy fixtures for backward compatibility
@pytest.fixture(scope="session")
def varvamp_test_file(legacy_data_dir):
    """VarVAMP test file (legacy)."""
    return legacy_data_dir / "ASFV_long" / "primers.tsv"


@pytest.fixture(scope="session")
def varvamp_reference_file(legacy_data_dir):
    """VarVAMP reference file (legacy)."""
    return legacy_data_dir / "ASFV_long" / "ambiguous_consensus.fasta"


@pytest.fixture(scope="session")
def artic_test_file(legacy_data_dir):
    """ARTIC test file (legacy)."""
    return legacy_data_dir / "ASFV.scheme.bed"


@pytest.fixture(scope="session")
def olivar_test_file(legacy_data_dir):
    """Olivar test file (legacy)."""
    return legacy_data_dir / "olivar_examples" / "olivar-design.csv"


@pytest.fixture(scope="session")
def olivar_reference_file(legacy_data_dir):
    """Olivar reference file (legacy)."""
    return legacy_data_dir / "olivar_examples" / "EPI_ISL_402124_ref.fasta"


@pytest.fixture(params=["varvamp", "artic", "olivar"])
def parser_test_data(request, legacy_data_dir):
    """
    Parametrized fixture providing test data for all parsers (legacy).

    This maintains backward compatibility with existing tests.
    """
    parser_files = {
        "varvamp": {
            "file": legacy_data_dir / "ASFV_long" / "primers.tsv",
            "reference": legacy_data_dir / "ASFV_long" / "ambiguous_consensus.fasta",
            "expected_amplicons": 80,
            "expected_primers": 160,
            "prefix": "ASFV",
        },
        "artic": {
            "file": legacy_data_dir / "ASFV.scheme.bed",
            "reference": None,
            "expected_amplicons": 80,
            "expected_primers": 160,
            "prefix": "ASFV",
        },
        "olivar": {
            "file": legacy_data_dir / "olivar_examples" / "olivar-design.csv",
            "reference": legacy_data_dir
            / "olivar_examples"
            / "EPI_ISL_402124_ref.fasta",
            "expected_amplicons": 5,
            "expected_primers": 10,
            "prefix": "COVID19",
        },
    }

    data = parser_files[request.param]
    data["format"] = request.param

    # Skip if test file doesn't exist
    if not data["file"].exists():
        pytest.skip(f"Test file not available for {request.param}: {data['file']}")

    # Calculate actual values for ARTIC
    if request.param == "artic":
        with open(data["file"]) as f:
            lines = [line for line in f if line.strip() and not line.startswith("#")]
        data["expected_primers"] = len(lines)
        data["expected_amplicons"] = len(lines) // 2

    return data


# Fixture for cross-format testing
@pytest.fixture(
    params=[
        ("varvamp", "small"),
        ("artic", "small"),
        ("olivar", "small"),
        ("varvamp", "medium"),
        ("artic", "medium"),
        ("olivar", "medium"),
    ]
)
def cross_format_test_data(request, unified_datasets_dir):
    """
    Parametrized fixture for testing across all formats and datasets.

    This enables comprehensive cross-format conversion testing.
    """
    format_name, dataset_name = request.param
    dataset_dir = unified_datasets_dir / dataset_name

    # Load metadata
    metadata_file = dataset_dir / "metadata.yaml"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = yaml.safe_load(f)

    # All available files for this dataset
    files = {
        "varvamp": dataset_dir / "varvamp.tsv",
        "artic": dataset_dir / "artic.scheme.bed",
        "olivar": dataset_dir / "olivar.csv",
        "sts": dataset_dir / "sts.tsv",
    }

    # Primary test file
    test_file = files[format_name]
    if not test_file.exists():
        pytest.skip(f"Test file not available: {test_file}")

    return {
        "format": format_name,
        "dataset": dataset_name,
        "file": test_file,
        "all_files": files,
        "reference": dataset_dir / "reference.fasta",
        "metadata": metadata,
        "expected_amplicons": metadata.get("amplicon_count", 5),
        "expected_primers": metadata.get("primer_count", 10),
        "prefix": metadata.get("organism", "TEST"),
    }


# Test fixtures for malformed/edge case data
@pytest.fixture(scope="session")
def malformed_data_fixtures(test_fixtures_dir):
    """Malformed data files for error testing."""
    malformed_dir = test_fixtures_dir / "malformed"
    return {
        "invalid_varvamp": malformed_dir / "invalid_varvamp.tsv",
        "invalid_artic": malformed_dir / "invalid_artic.bed",
        "invalid_olivar": malformed_dir / "invalid_olivar.csv",
        "corrupt_reference": malformed_dir / "corrupt_reference.fasta",
    }


@pytest.fixture(scope="session")
def minimal_data_fixtures(test_fixtures_dir):
    """Minimal valid data files for testing."""
    minimal_dir = test_fixtures_dir / "minimal"
    return {
        "minimal_varvamp": minimal_dir / "minimal_varvamp.tsv",
        "minimal_artic": minimal_dir / "minimal_artic.bed",
        "minimal_olivar": minimal_dir / "minimal_olivar.csv",
        "minimal_reference": minimal_dir / "minimal_reference.fasta",
    }


# Standard fixtures
@pytest.fixture
def test_config():
    """Standard test configuration."""
    from preprimer.core.enhanced_config import OutputSettings, ValidationSettings

    return EnhancedConfig(
        validation=ValidationSettings(
            enabled=True,
            min_length=10,
            max_length=50,
        ),
        output=OutputSettings(
            force_overwrite=True,
        ),
    )


@pytest.fixture
def temp_output_dir():
    """Temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session", autouse=True)
def verify_test_environment():
    """Verify test environment is properly set up."""
    # Check that parsers are registered
    expected_parsers = ["varvamp", "artic", "olivar"]
    registered_parsers = parser_registry.list_formats()

    for parser in expected_parsers:
        assert parser in registered_parsers, f"Parser '{parser}' not registered"

    # Check that writers are registered
    expected_writers = ["artic", "fasta", "sts", "varvamp", "olivar"]
    registered_writers = writer_registry.list_formats()

    for writer in expected_writers:
        assert writer in registered_writers, f"Writer '{writer}' not registered"


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "parser: marks tests for specific parsers")
    config.addinivalue_line("markers", "unified: marks tests using unified test data")
    config.addinivalue_line(
        "markers", "cross_format: marks cross-format conversion tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "workflow" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark parser-specific tests
        if "varvamp" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)
        elif "artic" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)
        elif "olivar" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)

        # Mark unified data tests
        if "unified" in item.nodeid.lower() or "cross_format" in item.nodeid.lower():
            item.add_marker(pytest.mark.unified)


@pytest.fixture
def sample_primer_data():
    """Sample primer data for testing."""
    from preprimer.core.interfaces import PrimerData

    return [
        PrimerData(
            name="test_primer_F",
            sequence="ATCGATCGATCGATCGATCG",
            start=100,
            stop=120,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon_1",
            reference_id="test_ref",
            gc_content=50.0,
            tm=60.0,
            score=1.0,
        ),
        PrimerData(
            name="test_primer_R",
            sequence="CGATCGATCGATCGATCGAT",
            start=300,
            stop=280,  # Reverse primer
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon_1",
            reference_id="test_ref",
            gc_content=50.0,
            tm=60.0,
            score=1.0,
        ),
    ]


@pytest.fixture
def sample_amplicon_data(sample_primer_data):
    """Sample amplicon data for testing."""
    from preprimer.core.interfaces import AmpliconData

    return AmpliconData(
        amplicon_id="test_amplicon_1",
        primers=sample_primer_data,
        length=200,
        reference_id="test_ref",
    )
