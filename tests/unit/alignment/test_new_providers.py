"""
G3: new in-silico-PCR providers (seqkit amplicon, EMBOSS primersearch, mfeprimer).

External binaries are not required: shutil.which and subprocess.run are mocked.
"""

from unittest.mock import patch

import pytest

from preprimer.alignment.mfeprimer_provider import MFEprimerProvider
from preprimer.alignment.primersearch_provider import PrimersearchProvider
from preprimer.alignment.seqkit_provider import SeqkitProvider
from preprimer.core.registry import alignment_registry

STS = "amp1\tACGTACGTACGTAC\tTGCATGCATGCATG\namp2\tACGTACGTACGTGG\tTGCATGCATGCACC\n"


@pytest.fixture
def primers(tmp_path):
    p = tmp_path / "p.sts.tsv"
    p.write_text(STS)
    return p


@pytest.fixture
def ref(tmp_path):
    r = tmp_path / "ref.fasta"
    r.write_text(">chr1\n" + "ACGT" * 100 + "\n")
    return r


# --- registration ----------------------------------------------------------


def test_new_providers_registered():
    providers = set(alignment_registry.list_providers())
    assert {"seqkit", "primersearch", "mfeprimer"} <= providers


@pytest.mark.parametrize(
    "cls,name,binary",
    [
        (SeqkitProvider, "seqkit", "seqkit"),
        (PrimersearchProvider, "primersearch", "primersearch"),
        (MFEprimerProvider, "mfeprimer", "mfeprimer"),
    ],
)
def test_tool_name_and_availability(cls, name, binary):
    assert cls.tool_name() == name
    with patch(
        f"preprimer.alignment.{name}_provider.shutil.which",
        return_value="/usr/bin/" + binary,
    ):
        assert cls().is_available() is True
    with patch(f"preprimer.alignment.{name}_provider.shutil.which", return_value=None):
        assert cls().is_available() is False


# --- seqkit ----------------------------------------------------------------


def test_seqkit_align_primers(primers, ref, tmp_path):
    with patch("preprimer.alignment.seqkit_provider.subprocess.run") as run:
        out = SeqkitProvider().align_primers(primers, ref, tmp_path / "o")
    run.assert_called_once()
    cmd = run.call_args[0][0]
    assert cmd[0] == "seqkit" and "amplicon" in cmd and "--bed" in cmd
    assert str(primers) in cmd
    assert "timeout" in run.call_args.kwargs
    assert out.suffix == ".bed"


# --- primersearch ----------------------------------------------------------


def test_primersearch_align_primers(primers, ref, tmp_path):
    with patch("preprimer.alignment.primersearch_provider.subprocess.run") as run:
        out = PrimersearchProvider().align_primers(primers, ref, tmp_path / "o")
    cmd = run.call_args[0][0]
    assert cmd[0] == "primersearch"
    assert "-seqall" in cmd and "-infile" in cmd and "-mismatchpercent" in cmd
    assert out.exists() or out.name.endswith(".primersearch.txt")


# --- mfeprimer (index + FASTA conversion + run) ----------------------------


def test_mfeprimer_align_primers(primers, ref, tmp_path):
    with patch("preprimer.alignment.mfeprimer_provider.subprocess.run") as run:
        out = MFEprimerProvider().align_primers(primers, ref, tmp_path / "o")
    # Two subprocess calls: index, then the mfeprimer run.
    assert run.call_count == 2
    cmds = [c.args[0] for c in run.call_args_list]
    assert any(c[0] == "mfeprimer" and "index" in c for c in cmds)
    assert any(c[0] == "mfeprimer" and "-d" in c for c in cmds)
    # STS primers were converted to a FASTA of individual primers.
    fa = tmp_path / "o" / "primers.primers.fasta"
    assert fa.exists()
    text = fa.read_text()
    assert text.count(">") == 4  # 2 amplicons x (F + R)
    assert "ACGTACGTACGTAC" in text
