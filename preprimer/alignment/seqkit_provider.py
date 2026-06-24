"""
seqkit amplicon in-silico-PCR provider.

seqkit (https://bioinf.shenwei.me/seqkit/) ships as a single static binary with
no database setup, and its `amplicon` subcommand reads a tab-separated primer
file (name, forward, reverse) — the same shape as PrePrimer's STS format.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union

from preprimer.core.interfaces import AlignmentProvider


class SeqkitProvider(AlignmentProvider):
    """In-silico PCR via `seqkit amplicon`."""

    @classmethod
    def tool_name(cls) -> str:
        return "seqkit"

    def is_available(self) -> bool:
        return shutil.which("seqkit") is not None

    def align_primers(
        self,
        primer_file: Union[str, Path],
        reference_file: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "primers",
        mismatches: int = 3,
        **kwargs,
    ) -> Path:
        """Run `seqkit amplicon`, returning the BED of predicted amplicons."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{prefix}.seqkit.bed"

        command = [
            "seqkit",
            "amplicon",
            "--primer-file",
            str(primer_file),
            "-m",
            str(mismatches),
            "--bed",
            "-o",
            str(output_file),
            str(reference_file),
        ]

        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
        return output_file
