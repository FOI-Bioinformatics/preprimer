"""
Coverage for OlivarWriter.write_with_metadata, validate_output and
get_output_info, which the standard writer suite does not exercise.
"""

import csv

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.olivar_writer import OlivarWriter


def _amplicon():
    fwd = PrimerData(
        "amp1_F",
        "ACGTACGTACGT",
        10,
        22,
        "+",
        "forward",
        pool=1,
        amplicon_id="amp1",
        reference_id="chr1",
    )
    rev = PrimerData(
        "amp1_R",
        "TGCATGCATGCA",
        200,
        212,
        "-",
        "reverse",
        pool=1,
        amplicon_id="amp1",
        reference_id="chr1",
    )
    return AmpliconData("amp1", [fwd, rev], length=202, reference_id="chr1")


def test_write_with_metadata(tmp_path):
    out = tmp_path / "out.csv"
    result = OlivarWriter().write_with_metadata(
        [_amplicon()],
        out,
        prefix="run",
        metadata={"reference_name": "chr1", "custom_field": "v"},
    )
    assert result == out
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) == 1
    row = rows[0]
    assert row["amplicon_id"] == "run_amp1"
    assert row["fP"] and row["rP"]
    assert "amplicon_length" in row
    assert row["custom_field"] == "v"


def test_write_with_metadata_skips_incomplete_amplicons(tmp_path):
    # Amplicon with only a forward primer is skipped.
    fwd = PrimerData(
        "x_F",
        "ACGTACGT",
        1,
        9,
        "+",
        "forward",
        pool=1,
        amplicon_id="x",
        reference_id="chr1",
    )
    amp = AmpliconData("x", [fwd], length=100, reference_id="chr1")
    out = tmp_path / "out.csv"
    OlivarWriter().write_with_metadata([amp], out, metadata=None)
    # No complete amplicons -> empty file (no rows written).
    assert out.read_text() == ""


def test_validate_output(tmp_path):
    writer = OlivarWriter()
    out = tmp_path / "ok.csv"
    writer.write([_amplicon()], out)
    assert writer.validate_output(out) is True
    assert writer.validate_output(tmp_path / "missing.csv") is False


def test_get_output_info():
    info = OlivarWriter().get_output_info()
    assert info["format"] == "olivar"
    assert info["extension"] == ".csv"
    assert "separator" in info
