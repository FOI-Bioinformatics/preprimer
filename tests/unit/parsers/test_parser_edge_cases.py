"""
Edge-case and error-path tests for the format parsers.

Targets validate_file() detection branches and the malformed-input handling in
_parse_file_content that the happy-path BaseParserTest suite does not exercise.
"""

import pytest

from preprimer.core.exceptions import ParserError
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.olivar_parser import OlivarParser
from preprimer.parsers.sts_parser import STSParser
from preprimer.parsers.varvamp_parser import VarVAMPParser


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


# --- STS -------------------------------------------------------------------


def test_sts_validate_rejects_bad_inputs(tmp_path):
    parser = STSParser()
    assert parser.validate_file(tmp_path / "missing.tsv") is False
    assert parser.validate_file(_write(tmp_path, "empty.tsv", "")) is False
    # Wrong column count.
    assert parser.validate_file(_write(tmp_path, "two.tsv", "a\tACGT\n")) is False
    # Non-DNA sequence fields.
    assert (
        parser.validate_file(_write(tmp_path, "nd.tsv", "amp\thello\tworld\n")) is False
    )
    # 4-column with non-numeric size.
    assert (
        parser.validate_file(_write(tmp_path, "badsize.tsv", "amp\tACGT\tTGCA\tbig\n"))
        is False
    )
    # 4-column with non-positive size.
    assert (
        parser.validate_file(_write(tmp_path, "neg.tsv", "amp\tACGT\tTGCA\t0\n"))
        is False
    )


def test_sts_validate_accepts_3_and_4_col(tmp_path):
    parser = STSParser()
    assert parser.validate_file(_write(tmp_path, "a.sts.tsv", "amp\tACGT\tTGCA\n"))
    assert parser.validate_file(
        _write(
            tmp_path,
            "b.sts.tsv",
            "NAME\tFORWARD\tREVERSE\tSIZE\namp\tACGT\tTGCA\t100\n",
        )
    )


def test_sts_validate_with_header_variants(tmp_path):
    parser = STSParser()
    # Valid header form.
    assert parser.validate_file(
        _write(tmp_path, "h.sts.tsv", "NAME\tFORWARD\tREVERSE\namp\tACGT\tTGCA\n")
    )
    # Header first field not a recognized name field.
    assert (
        parser.validate_file(
            _write(tmp_path, "bn.sts.tsv", "FOO\tFORWARD\tREVERSE\namp\tACGT\tTGCA\n")
        )
        is False
    )
    # Header name OK but columns 2/3 lack primer keywords (and aren't DNA).
    assert (
        parser.validate_file(
            _write(tmp_path, "np.sts.tsv", "NAME\tXX\tYY\namp\tACGT\tTGCA\n")
        )
        is False
    )


def test_sts_parse_size_warnings(tmp_path):
    # Non-numeric and non-positive sizes are warned and ignored, not fatal.
    parser = STSParser()
    # First row has a valid size (validate_file inspects only the first data
    # line); later rows carry the bad sizes that exercise the parse warnings.
    f = _write(
        tmp_path,
        "sz.sts.tsv",
        "NAME\tFORWARD\tREVERSE\tSIZE\n"
        "amp1\tACGTACGTAC\tTGCATGCATG\t150\n"
        "amp2\tACGTACGTAC\tTGCATGCATG\tnotanumber\n"
        "amp3\tACGTACGTAC\tTGCATGCATG\t-5\n",
    )
    amplicons = parser.parse(f, prefix="x")
    assert len(amplicons) == 3


def test_sts_parse_inconsistent_columns_raises(tmp_path):
    parser = STSParser()
    f = _write(tmp_path, "bad.sts.tsv", "amp1\tACGT\tTGCA\namp2\tACGT\n")
    with pytest.raises(ParserError):
        parser.parse(f, prefix="x")


def test_sts_get_reference_file_is_none(tmp_path):
    f = _write(tmp_path, "a.sts.tsv", "amp\tACGT\tTGCA\n")
    assert STSParser().get_reference_file(f) is None


def test_sts_validate_header_only_no_data(tmp_path):
    # Header present but no data rows -> invalid.
    f = _write(tmp_path, "h.sts.tsv", "NAME\tFORWARD\tREVERSE\n")
    assert STSParser().validate_file(f) is False


def test_get_reference_file_rejects_unsafe_path():
    # A traversal path makes sanitize_path raise inside get_reference_file,
    # which is caught and returns None.
    assert VarVAMPParser().get_reference_file("../../etc/x.tsv") is None
    assert OlivarParser().get_reference_file("../../etc/x.csv") is None


@pytest.mark.parametrize(
    "parser_cls,name",
    [
        (STSParser, "x.sts.tsv"),
        (VarVAMPParser, "x.tsv"),
        (OlivarParser, "x.csv"),
    ],
)
def test_parsers_handle_permission_error(parser_cls, name, tmp_path):
    from unittest.mock import patch

    from preprimer.core.exceptions import ParserError as PErr

    f = _write(tmp_path, name, "data")
    with patch("builtins.open", side_effect=PermissionError("denied")):
        with pytest.raises(PErr):
            parser_cls()._parse_file_content(f, "x")


# --- VarVAMP ---------------------------------------------------------------

VARVAMP_HEADER = (
    "amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\tseq\tsize\t"
    "gc_best\ttemp_best\tmean_gc\tmean_temp\tscore"
)


def test_varvamp_validate_rejects_missing_columns(tmp_path):
    parser = VarVAMPParser()
    assert parser.validate_file(tmp_path / "missing.tsv") is False
    assert parser.validate_file(_write(tmp_path, "empty.tsv", "")) is False
    assert (
        parser.validate_file(_write(tmp_path, "partial.tsv", "amplicon_name\tseq\n"))
        is False
    )


def test_varvamp_validate_accepts_good_header(tmp_path):
    f = _write(
        tmp_path,
        "v.tsv",
        VARVAMP_HEADER
        + "\namp\t300\tFW_1\t1\t0\t20\tACGTACGTACGTACGTACGT\t20\t50\t60\t50\t60\t90\n",
    )
    assert VarVAMPParser().validate_file(f)


def test_varvamp_fixes_amlicon_typo(tmp_path):
    # 'amlicon_name' typo in the header should be auto-corrected during parse.
    header = VARVAMP_HEADER.replace("amplicon_name", "amlicon_name")
    f = _write(
        tmp_path,
        "typo.tsv",
        header
        + "\namp\t300\tFW_1\t1\t0\t20\tACGTACGTACGTACGTACGT\t20\t50\t60\t50\t60\t90"
        + "\namp\t300\tRW_1\t1\t40\t60\tACGTACGTACGTACGTACGT\t20\t50\t60\t50\t60\t90\n",
    )
    # validate_file normalizes the typo too.
    assert VarVAMPParser().validate_file(f)
    amplicons = VarVAMPParser().parse(f, prefix="x")
    assert len(amplicons) == 1


def test_varvamp_parse_bad_coordinates_raises(tmp_path):
    # start >= stop is a fatal coordinate error.
    f = _write(
        tmp_path,
        "v.tsv",
        VARVAMP_HEADER
        + "\namp\t300\tFW_1\t1\t30\t20\tACGTACGTACGTACGTACGT\t20\t50\t60\t50\t60\t90\n",
    )
    with pytest.raises(ParserError):
        VarVAMPParser().parse(f, prefix="x")


def test_varvamp_parse_bad_primer_name_raises(tmp_path):
    f = _write(
        tmp_path,
        "v.tsv",
        VARVAMP_HEADER
        + "\namp\t300\tXX_1\t1\t0\t20\tACGTACGTACGTACGTACGT\t20\t50\t60\t50\t60\t90\n",
    )
    with pytest.raises(ParserError):
        VarVAMPParser().parse(f, prefix="x")


# --- ARTIC -----------------------------------------------------------------


def test_artic_validate_rejects_bad_inputs(tmp_path):
    parser = ARTICParser()
    assert parser.validate_file(tmp_path / "missing.bed") is False
    # Too few fields.
    assert parser.validate_file(_write(tmp_path, "few.bed", "chr1\t0\t20\n")) is False
    # Bad strand.
    assert (
        parser.validate_file(
            _write(tmp_path, "strand.bed", "chr1\t0\t20\tref_1_LEFT\t1\t?\tACGT\n")
        )
        is False
    )
    # Missing LEFT/RIGHT in name.
    assert (
        parser.validate_file(
            _write(tmp_path, "noname.bed", "chr1\t0\t20\tref_1_MID\t1\t+\tACGT\n")
        )
        is False
    )


def test_artic_validate_accepts_good_bed(tmp_path):
    f = _write(
        tmp_path,
        "ok.bed",
        "chr1\t0\t20\tref_1_LEFT\t1\t+\tACGTACGTACGTACGTACGT\n",
    )
    assert ARTICParser().validate_file(f)


# --- Olivar ----------------------------------------------------------------


def test_olivar_validate_by_filename(tmp_path):
    # Official naming pattern short-circuits to True.
    f = _write(tmp_path, "x.olivar-design.csv", "anything\n")
    assert OlivarParser().validate_file(f)


def test_olivar_validate_rejects_missing_columns(tmp_path):
    parser = OlivarParser()
    assert parser.validate_file(tmp_path / "missing.csv") is False
    assert (
        parser.validate_file(_write(tmp_path, "bad.csv", "col1,col2\n1,2\n")) is False
    )


def test_olivar_validate_accepts_required_columns(tmp_path):
    f = _write(
        tmp_path,
        "design.csv",
        "amplicon_id,fP,rP,pool\namp1,ACGTACGT,TGCATGCA,1\n",
    )
    assert OlivarParser().validate_file(f)


def test_olivar_parse_missing_required_field_raises(tmp_path):
    # Row missing the 'pool' column value.
    f = _write(
        tmp_path,
        "design.csv",
        "amplicon_id,fP,rP,pool\namp1,ACGTACGT,TGCATGCA,\n",
    )
    with pytest.raises(ParserError):
        OlivarParser().parse(f, prefix="x")


# --- get_reference_file discovery ------------------------------------------


def test_varvamp_get_reference_file_found(tmp_path):
    f = _write(tmp_path, "v.tsv", "data")
    ref = _write(tmp_path, "ambiguous_consensus.fasta", ">r\nACGT\n")
    assert VarVAMPParser().get_reference_file(f) == ref.resolve()


def test_varvamp_get_reference_file_absent(tmp_path):
    f = _write(tmp_path, "v.tsv", "data")
    assert VarVAMPParser().get_reference_file(f) is None


def test_olivar_get_reference_file_found(tmp_path):
    f = _write(tmp_path, "x.csv", "data")
    ref = _write(tmp_path, "reference.fasta", ">r\nACGT\n")
    assert OlivarParser().get_reference_file(f) == ref.resolve()


def test_artic_get_reference_file_found(tmp_path):
    f = _write(tmp_path, "scheme.scheme.bed", "data")
    ref = _write(tmp_path, "scheme.reference.fasta", ">r\nACGT\n")
    assert ARTICParser().get_reference_file(f) == ref


def test_artic_get_reference_file_absent(tmp_path):
    f = _write(tmp_path, "scheme.bed", "data")
    assert ARTICParser().get_reference_file(f) is None


def test_olivar_get_reference_file_ref_pattern(tmp_path):
    f = _write(tmp_path, "myrun-design.csv", "data")
    # base = stem with '-design' and 'olivar-' stripped -> 'myrun'
    ref = _write(tmp_path, "myrun_ref.fasta", ">r\nACGT\n")
    assert OlivarParser().get_reference_file(f) == ref.resolve()


# --- non-UTF-8 input handling (error branches in _parse_file_content) -------


def _write_bytes(tmp_path, name, data):
    p = tmp_path / name
    p.write_bytes(data)
    return p


@pytest.mark.parametrize(
    "parser_cls,name",
    [
        (STSParser, "x.sts.tsv"),
        (VarVAMPParser, "x.tsv"),
        (OlivarParser, "x.csv"),
    ],
)
def test_parsers_reject_non_utf8(parser_cls, name, tmp_path):
    from preprimer.core.exceptions import ParserError as PErr

    # Invalid UTF-8 bytes trigger the UnicodeDecodeError handler.
    f = _write_bytes(tmp_path, name, b"\xff\xfe\x00bad\tdata\n")
    with pytest.raises(PErr):
        parser_cls()._parse_file_content(f, "x")
