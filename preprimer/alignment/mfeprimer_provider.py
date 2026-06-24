"""
MFEprimer in-silico-PCR provider.

MFEprimer (https://www.mfeprimer.com/) evaluates primer specificity with a
thermodynamic nearest-neighbour model. It needs FASTA primers and an indexed
reference database, so this provider converts the STS primer file to FASTA and
indexes the reference before running.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Union

from preprimer.core.interfaces import AlignmentProvider

_DNA = re.compile(r"^[ATCGNRYSWKMBDHVatcgn]+$")


class MFEprimerProvider(AlignmentProvider):
    """In-silico PCR / specificity via `mfeprimer`."""

    @classmethod
    def tool_name(cls) -> str:
        return "mfeprimer"

    def is_available(self) -> bool:
        return shutil.which("mfeprimer") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "primers",
        **kwargs,
    ) -> Path:
        """Convert primers to FASTA, index the reference, then run mfeprimer."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        primers_fasta = output_dir / f"{prefix}.primers.fasta"
        self._sts_to_fasta(Path(primer_file), primers_fasta)

        # Build the k-mer index for the reference (idempotent in practice).
        subprocess.run(
            ["mfeprimer", "index", "-i", str(reference_file)],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )

        output_file = output_dir / f"{prefix}.mfeprimer.txt"
        subprocess.run(
            [
                "mfeprimer",
                "-i",
                str(primers_fasta),
                "-d",
                str(reference_file),
                "-o",
                str(output_file),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        return output_file

    @staticmethod
    def _sts_to_fasta(sts_file: Path, out_fasta: Path) -> None:
        """Write each STS forward/reverse primer as an individual FASTA record."""
        records = []
        for line in sts_file.read_text().splitlines():
            fields = line.strip().split("\t")
            if len(fields) < 3:
                continue
            name, fwd, rev = fields[0], fields[1].strip(), fields[2].strip()
            # Skip a header row (non-DNA in the primer columns).
            if not _DNA.match(fwd) or not _DNA.match(rev):
                continue
            records.append((f"{name}_F", fwd))
            records.append((f"{name}_R", rev))

        with open(out_fasta, "w") as fh:
            for rec_name, seq in records:
                fh.write(f">{rec_name}\n{seq}\n")
