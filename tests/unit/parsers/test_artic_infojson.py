"""
G2: import scheme metadata from a sibling info.json and preserve it across
conversion (instead of regenerating placeholder metadata).
"""

import json

from preprimer.parsers.artic_parser import ARTICParser
from preprimer.writers.artic_writer import ARTICWriter

BED7 = (
    "MN908947.3\t30\t54\tnCoV_1_LEFT\t1\t+\tACGTACGTACGTACGTACGTACGT\n"
    "MN908947.3\t385\t410\tnCoV_1_RIGHT\t1\t-\tTGCATGCATGCATGCATGCATGCAT\n"
)

INFO = {
    "schemename": "sars-cov-2-400",
    "schemeversion": "v4.1.0",
    "ampliconsize": 400,
    "species": "Severe acute respiratory syndrome coronavirus 2",
    "primer_bed_md5": "a" * 32,
    "reference_fasta_md5": "b" * 32,
    "authors": ["Jane Researcher", "John Scientist"],
    "description": "Real scheme metadata",
}


def _scheme_dir(tmp_path):
    (tmp_path / "primer.bed").write_text(BED7)
    (tmp_path / "info.json").write_text(json.dumps(INFO))
    return tmp_path / "primer.bed"


def test_parser_imports_info_json_metadata(tmp_path):
    bed = _scheme_dir(tmp_path)
    amplicons = ARTICParser().parse(bed, prefix="x")
    scheme_info = amplicons[0].metadata.get("scheme_info")
    assert scheme_info is not None
    assert scheme_info["species"] == INFO["species"]
    assert scheme_info["schemeversion"] == "v4.1.0"
    assert scheme_info["authors"] == INFO["authors"]


def test_parser_without_info_json_has_no_scheme_info(tmp_path):
    (tmp_path / "primer.bed").write_text(BED7)
    amplicons = ARTICParser().parse(tmp_path / "primer.bed", prefix="x")
    assert "scheme_info" not in amplicons[0].metadata


def test_writer_preserves_imported_metadata(tmp_path):
    bed = _scheme_dir(tmp_path)
    amplicons = ARTICParser().parse(bed, prefix="x")

    out = tmp_path / "out" / "s" / "V1" / "primer.bed"
    ARTICWriter().write(amplicons, out, prefix="s")
    info = json.loads((out.parent / "info.json").read_text())

    # Metadata from the source info.json survives, not placeholders.
    assert info["species"] == INFO["species"]
    assert info["schemeversion"] == "v4.1.0"
    assert info["authors"] == INFO["authors"]


def test_writer_kwargs_override_imported_metadata(tmp_path):
    bed = _scheme_dir(tmp_path)
    amplicons = ARTICParser().parse(bed, prefix="x")

    out = tmp_path / "out" / "s" / "V1" / "primer.bed"
    ARTICWriter().write(amplicons, out, prefix="s", species="Override species")
    info = json.loads((out.parent / "info.json").read_text())
    assert info["species"] == "Override species"
