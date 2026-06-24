"""
G4: generic interchange formats - GFF3 writer and Primer3 (Boulder-IO) parser.
"""

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.parsers.primer3_parser import Primer3Parser
from preprimer.writers.gff3_writer import GFF3Writer

# --- GFF3 writer -----------------------------------------------------------


def _amplicon():
    fwd = PrimerData(
        "amp1_LEFT",
        "ACGTACGTACGTACGTAC",
        10,
        28,
        "+",
        "forward",
        pool=1,
        amplicon_id="amp1",
        reference_id="chr1",
    )
    rev = PrimerData(
        "amp1_RIGHT",
        "TGCATGCATGCATGCATG",
        200,
        218,
        "-",
        "reverse",
        pool=1,
        amplicon_id="amp1",
        reference_id="chr1",
    )
    return AmpliconData("amp1", [fwd, rev], length=208, reference_id="chr1")


def test_gff3_writer_basic(tmp_path):
    out = tmp_path / "primers.gff3"
    result = GFF3Writer().write([_amplicon()], out)
    assert result == out
    text = out.read_text()
    assert text.startswith("##gff-version 3")
    rows = [ln for ln in text.splitlines() if not ln.startswith("#") and ln.strip()]
    assert len(rows) == 2
    cols = rows[0].split("\t")
    assert len(cols) == 9
    assert cols[0] == "chr1"  # seqid
    # GFF is 1-based inclusive: 0-based start 10 -> 11.
    assert cols[3] == "11"
    assert cols[4] == "28"
    assert cols[6] == "+"  # strand
    assert "ID=amp1_LEFT" in cols[8]


def test_gff3_registered():
    from preprimer.core.registry import writer_registry

    assert "gff3" in writer_registry.list_formats()
    assert writer_registry.get_writer("gff3").file_extension() == ".gff3"


# --- Primer3 parser --------------------------------------------------------

PRIMER3 = (
    "SEQUENCE_ID=example_target\n"
    "PRIMER_LEFT_0_SEQUENCE=ACGTACGTACGTACGTAC\n"
    "PRIMER_RIGHT_0_SEQUENCE=TGCATGCATGCATGCATG\n"
    "PRIMER_LEFT_0=10,18\n"
    "PRIMER_RIGHT_0=217,18\n"
    "PRIMER_PAIR_0_PRODUCT_SIZE=208\n"
    "PRIMER_LEFT_1_SEQUENCE=GGGGACGTACGTACGTAC\n"
    "PRIMER_RIGHT_1_SEQUENCE=CCCCTGCATGCATGCATG\n"
    "PRIMER_LEFT_1=50,18\n"
    "PRIMER_RIGHT_1=260,18\n"
    "=\n"
)


def test_primer3_parser_validate_and_parse(tmp_path):
    f = tmp_path / "out.p3"
    f.write_text(PRIMER3)
    parser = Primer3Parser()
    assert parser.validate_file(f) is True

    amplicons = parser.parse(f, prefix="example_target")
    assert len(amplicons) == 2
    a0 = amplicons[0]
    assert len(a0.forward_primers) == 1 and len(a0.reverse_primers) == 1
    assert a0.forward_primers[0].sequence == "ACGTACGTACGTACGTAC"
    assert a0.reverse_primers[0].sequence == "TGCATGCATGCATGCATG"
    # Left primer: Primer3 "10,18" -> 0-based start 10, stop 28.
    assert a0.forward_primers[0].start == 10
    assert a0.forward_primers[0].stop == 28


def test_primer3_parser_registered():
    from preprimer.core.registry import parser_registry

    assert "primer3" in parser_registry.list_formats()


def test_primer3_validate_rejects_non_primer3(tmp_path):
    f = tmp_path / "x.p3"
    f.write_text("not a primer3 file\njust text\n")
    assert Primer3Parser().validate_file(f) is False
