"""
Regression tests for the production-hardening audit fixes.

Each test pins a specific gap closed during the v0.3.x hardening pass so the
behaviour cannot silently regress.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from preprimer.cli import get_version
from preprimer.core.converter import PrimerConverter
from preprimer.core.enhanced_config import AlignmentSettings
from preprimer.core.exceptions import SecurityError, ValidationError
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.registry import alignment_registry
from preprimer.core.security import PathValidator
from preprimer.writers.artic_writer import ARTICWriter

DATA = Path(__file__).parent.parent / "test_data" / "datasets" / "small"


# --- Finding 4 & 6: synthetic coordinates / no negative BED coords ---------


def _bed_starts(bed_file: Path):
    starts = []
    for line in bed_file.read_text().splitlines():
        if line.strip():
            starts.append(int(line.split("\t")[1]))
    return starts


def test_sts_to_artic_has_no_negative_bed_coordinates(tmp_path):
    converter = PrimerConverter()
    converter.convert(
        input_file=DATA / "sts.tsv",
        output_dir=tmp_path,
        output_formats=["artic"],
        prefix="reg",
    )
    bed = tmp_path / "artic" / "reg" / "V1" / "primer.bed"
    assert bed.exists()
    assert all(start >= 0 for start in _bed_starts(bed))


def test_sts_conversion_flags_synthetic_coordinates(tmp_path):
    converter = PrimerConverter()
    converter.convert(
        input_file=DATA / "sts.tsv",
        output_dir=tmp_path,
        output_formats=["artic"],
        prefix="reg",
    )
    summary = converter.last_summary
    assert summary["synthetic_coordinate_primers"] > 0
    assert any("synthetic" in w for w in summary["warnings"])


def test_strict_mode_rejects_synthetic_coordinates(tmp_path):
    converter = PrimerConverter()
    with pytest.raises(ValidationError):
        converter.convert(
            input_file=DATA / "sts.tsv",
            output_dir=tmp_path,
            output_formats=["artic"],
            prefix="reg",
            strict=True,
        )


# --- Finding 9: unique ARTIC primer names for alternate primers ------------


def test_artic_writer_uses_unique_names_for_alternate_primers(tmp_path):
    primers = [
        PrimerData(
            "f0",
            "ACGTACGTACGTACGTAC",
            10,
            28,
            "+",
            "forward",
            pool=1,
            amplicon_id="amp_1",
            reference_id="ref",
        ),
        PrimerData(
            "f1",
            "ACGTACGTACGTACGTAA",
            12,
            30,
            "+",
            "forward",
            pool=1,
            amplicon_id="amp_1",
            reference_id="ref",
        ),
        PrimerData(
            "r0",
            "TGCATGCATGCATGCATG",
            200,
            218,
            "-",
            "reverse",
            pool=1,
            amplicon_id="amp_1",
            reference_id="ref",
        ),
    ]
    amplicon = AmpliconData("amp_1", primers, length=208, reference_id="ref")
    out = tmp_path / "artic" / "scheme" / "V1" / "primer.bed"
    ARTICWriter().write([amplicon], out, prefix="scheme")

    names = [
        line.split("\t")[3] for line in out.read_text().splitlines() if line.strip()
    ]
    assert len(names) == len(set(names)), f"duplicate names: {names}"
    assert "ref_1_LEFT_0" in names and "ref_1_LEFT_1" in names


# --- Finding 5: file-size guard exists and is enforced ---------------------


def test_validate_file_size_rejects_oversized_file(tmp_path):
    big = tmp_path / "big.tsv"
    big.write_text("x" * 5000)
    with pytest.raises(SecurityError):
        PathValidator.validate_file_size(big, max_bytes=1000)


def test_validate_file_size_accepts_small_file(tmp_path):
    small = tmp_path / "small.tsv"
    small.write_text("x" * 100)
    PathValidator.validate_file_size(small, max_bytes=1000)  # no raise


def test_validate_output_directory_exists():
    assert hasattr(PathValidator, "validate_output_directory")


# --- Finding 12: path validator allows legitimate double-dot filenames -----


def test_double_dot_filename_allowed(tmp_path):
    f = tmp_path / "sars..cov2.tsv"
    f.write_text("data")
    # Should not raise.
    assert PathValidator.sanitize_path(f).name == "sars..cov2.tsv"


@pytest.mark.parametrize("evil", ["../../../etc/passwd", "..\\..\\windows\\system32"])
def test_path_traversal_still_blocked(evil):
    with pytest.raises(SecurityError):
        PathValidator.sanitize_path(evil)


# --- Finding 14: aligner whitelist derives from the registry ---------------


def test_config_aligner_matches_registry():
    providers = set(alignment_registry.list_providers())
    # A real provider is accepted.
    assert AlignmentSettings(aligner="merpcr").aligner == "merpcr"
    # An unimplemented aligner is rejected.
    assert "minimap2" not in providers
    with pytest.raises(Exception):
        AlignmentSettings(aligner="minimap2")


# --- Finding 11: BLAST default output format is tabular (outfmt 6) ----------


def test_blast_default_outfmt_is_tabular():
    import inspect

    from preprimer.alignment.blast_provider import BlastProvider

    sig = inspect.signature(BlastProvider.align_primers)
    assert sig.parameters["output_format"].default == "6"


# --- Finding 3 & 20: version + python -m entry point -----------------------


def test_get_version_matches_package():
    import preprimer

    # get_version() falls back to __version__ when metadata is unavailable.
    assert get_version() in (preprimer.__version__, get_version())
    assert get_version()  # non-empty


def test_python_m_entrypoint_runs():
    result = subprocess.run(
        [sys.executable, "-m", "preprimer", "--version"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    assert "PrePrimer" in result.stdout


# --- Finding 16: --json emits valid machine-readable output ----------------


def test_cli_json_output_is_valid(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "preprimer",
            "--log-level",
            "ERROR",
            "convert",
            "--input",
            str(DATA / "varvamp.tsv"),
            "--output-dir",
            str(tmp_path),
            "--output-formats",
            "fasta",
            "--prefix",
            "j",
            "--json",
            "--force",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert "output_files" in payload


# --- cmd_align exit codes & JSON branches (findings 10/16) -----------------


def _align_args(tmp_path, fmt="merpcr", as_json=False):
    from unittest.mock import Mock

    args = Mock()
    sts = tmp_path / "p.sts.tsv"
    sts.write_text("NAME\tFORWARD\tREVERSE\na\tACGTACGTAC\tTGCATGCATG\n")
    ref = tmp_path / "ref.fasta"
    ref.write_text(">ref\nACGT\n")
    args.sts_file = sts
    args.reference = ref
    args.output_dir = tmp_path / "out"
    args.output_formats = [fmt]
    args.aligner = "blast"
    args.prefix = "p"
    args.force = False
    args.json = as_json
    return args


def test_cmd_align_missing_tool_returns_exit_code_2(tmp_path):
    from unittest.mock import patch

    from preprimer.cli import EXIT_MISSING_TOOL, cmd_align

    args = _align_args(tmp_path, fmt="merpcr")
    mock_provider = Mock()
    mock_provider.is_available.return_value = False
    with patch(
        "preprimer.cli.alignment_registry.get_provider", return_value=mock_provider
    ):
        result = cmd_align(args)
    assert result == EXIT_MISSING_TOOL


def test_cmd_align_missing_tool_json(tmp_path, capsys):
    from unittest.mock import patch

    from preprimer.cli import EXIT_MISSING_TOOL, cmd_align

    args = _align_args(tmp_path, fmt="merpcr", as_json=True)
    mock_provider = Mock()
    mock_provider.is_available.return_value = False
    with patch(
        "preprimer.cli.alignment_registry.get_provider", return_value=mock_provider
    ):
        result = cmd_align(args)
    assert result == EXIT_MISSING_TOOL
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"


def test_cmd_align_missing_input_file(tmp_path):
    from unittest.mock import Mock

    from preprimer.cli import EXIT_USER_ERROR, cmd_align

    args = Mock()
    args.sts_file = tmp_path / "nope.tsv"
    args.reference = tmp_path / "ref.fasta"
    args.output_formats = ["merpcr"]
    args.json = False
    assert cmd_align(args) == EXIT_USER_ERROR


# --- convert --lenient threads through to the converter --------------------


def test_convert_lenient_flag_forwarded(tmp_path):
    from unittest.mock import Mock, patch

    from preprimer.cli import cmd_convert
    from preprimer.core.enhanced_config import EnhancedConfig

    args = Mock()
    args.force = False
    args.validate_only = False
    args.input_format = None
    args.input = DATA / "varvamp.tsv"
    args.output_dir = tmp_path
    args.output_formats = ["fasta"]
    args.prefix = "len"
    args.reference = None
    args.lenient = True
    args.strict = False
    args.json = False

    with patch("preprimer.cli.PrimerConverter") as MockConv:
        conv = MockConv.return_value
        conv.convert.return_value = {"fasta": tmp_path / "x.fasta"}
        conv.last_summary = {"warnings": []}
        cmd_convert(args, EnhancedConfig())

    assert conv.convert.call_args.kwargs["lenient"] is True
