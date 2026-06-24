"""
G1: canonical 6-column primer.bed support (read + write).

The community/legacy primer.bed (pha4ge primaschema, quick-lab) is 6-column
(chrom start end name pool strand) with the primer sequence in a separate
reference, while PrimalScheme-like BED appends the sequence as a 7th column.
PrePrimer must parse both and be able to emit 6-column.
"""

from preprimer.core.converter import PrimerConverter
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.writers.artic_writer import ARTICWriter

SIX_COL = (
    "MN908947.3\t30\t54\tnCoV_1_LEFT\t1\t+\n"
    "MN908947.3\t385\t410\tnCoV_1_RIGHT\t1\t-\n"
    "MN908947.3\t320\t342\tnCoV_2_LEFT\t2\t+\n"
    "MN908947.3\t704\t726\tnCoV_2_RIGHT\t2\t-\n"
)

SEVEN_COL = (
    "MN908947.3\t30\t54\tnCoV_1_LEFT\t1\t+\tACGTACGTACGTACGTACGTACGT\n"
    "MN908947.3\t385\t410\tnCoV_1_RIGHT\t1\t-\tTGCATGCATGCATGCATGCATGCAT\n"
)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_parse_6col_bed_yields_amplicons(tmp_path):
    f = _write(tmp_path, "primer.bed", SIX_COL)
    amplicons = ARTICParser().parse(f, prefix="x")
    assert len(amplicons) == 2  # nCoV_1, nCoV_2
    total = sum(len(a.primers) for a in amplicons)
    assert total == 4
    # 6-column BED carries no sequence.
    first = amplicons[0].primers[0]
    assert first.sequence == ""
    assert first.pool == 1
    assert first.start == 30 and first.stop == 54


def test_parse_7col_bed_still_has_sequence(tmp_path):
    f = _write(tmp_path, "primer.bed", SEVEN_COL)
    amplicons = ARTICParser().parse(f, prefix="x")
    assert sum(len(a.primers) for a in amplicons) == 2
    assert amplicons[0].primers[0].sequence == "ACGTACGTACGTACGTACGTACGT"


def test_validate_accepts_6col(tmp_path):
    f = _write(tmp_path, "primer.bed", SIX_COL)
    assert ARTICParser().validate_file(f) is True


# --- writer: emit 6-column -------------------------------------------------


def test_writer_bed_columns_6(tmp_path):
    amplicons = ARTICParser().parse(_write(tmp_path, "in.bed", SEVEN_COL), prefix="x")
    out = tmp_path / "artic" / "s" / "V1" / "primer.bed"
    ARTICWriter().write(amplicons, out, prefix="s", bed_columns=6)
    rows = [ln.split("\t") for ln in out.read_text().splitlines() if ln.strip()]
    assert rows, "expected output rows"
    assert all(
        len(r) == 6 for r in rows
    ), f"expected 6 columns, got {[len(r) for r in rows]}"


def test_writer_default_is_7col(tmp_path):
    amplicons = ARTICParser().parse(_write(tmp_path, "in.bed", SEVEN_COL), prefix="x")
    out = tmp_path / "artic" / "s" / "V1" / "primer.bed"
    ARTICWriter().write(amplicons, out, prefix="s")
    rows = [ln.split("\t") for ln in out.read_text().splitlines() if ln.strip()]
    assert all(len(r) == 7 for r in rows)


def test_6col_roundtrip_preserves_coordinates(tmp_path):
    src = _write(tmp_path, "src.bed", SIX_COL)
    amplicons = ARTICParser().parse(src, prefix="x")
    out = tmp_path / "artic" / "rt" / "V1" / "primer.bed"
    ARTICWriter().write(amplicons, out, prefix="rt", bed_columns=6)

    def coords(text):
        return sorted(
            (p[1], p[2], p[4], p[5])
            for ln in text.splitlines()
            if ln.strip()
            for p in [ln.split("\t")]
        )

    assert coords(out.read_text()) == coords(SIX_COL)


def test_converter_accepts_seqless_6col_without_lenient(tmp_path):
    """A 6-column primer.bed (empty sequences) must convert without --lenient;
    empty sequence is valid for this format."""
    src = _write(tmp_path, "primer.bed", SIX_COL)
    out_files = PrimerConverter().convert(
        input_file=src,
        output_dir=tmp_path / "out",
        output_formats=["artic"],
        prefix="s",
        bed_columns=6,
    )
    assert "artic" in out_files


def test_converter_warns_seqless_to_fasta(tmp_path):
    src = _write(tmp_path, "primer.bed", SIX_COL)
    conv = PrimerConverter()
    conv.convert(
        input_file=src,
        output_dir=tmp_path / "out",
        output_formats=["fasta"],
        prefix="s",
    )
    assert any("no sequence" in w for w in conv.last_summary["warnings"])
