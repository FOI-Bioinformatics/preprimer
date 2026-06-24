"""
EMBOSS primersearch in-silico-PCR provider.

primersearch is the standard EMBOSS tool for searching a sequence set with
primer pairs; it is degenerate-aware. Its input file is tab/space separated
(name, forward, reverse), compatible with PrePrimer's STS format.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union

from preprimer.core.interfaces import AlignmentProvider


class PrimersearchProvider(AlignmentProvider):
    """In-silico PCR via EMBOSS `primersearch`."""

    @classmethod
    def tool_name(cls) -> str:
        return "primersearch"

    def is_available(self) -> bool:
        return shutil.which("primersearch") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "primers",
        mismatch_percent: int = 10,
        **kwargs,
    ) -> Path:
        """Run EMBOSS primersearch, returning the results file."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{prefix}.primersearch.txt"

        command = [
            "primersearch",
            "-seqall",
            str(reference_file),
            "-infile",
            str(primer_file),
            "-mismatchpercent",
            str(mismatch_percent),
            "-outfile",
            str(output_file),
        ]

        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
        return output_file
