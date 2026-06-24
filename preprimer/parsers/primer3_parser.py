"""
Primer3 (Boulder-IO) output parser.

Primer3 is the primer-design engine that many tiled-amplicon tools wrap. Its
output is Boulder-IO: ``KEY=value`` lines, records terminated by a lone ``=``.
This parser extracts the designed primer pairs into amplicons.

Coordinates: Primer3 reports ``PRIMER_LEFT_i=start,length`` with a 0-based
left-primer start (matching PrimerData), and ``PRIMER_RIGHT_i=pos,length`` where
``pos`` is the 0-based rightmost base of the right primer.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Union

from ..core.exceptions import InsufficientDataError, ParserError
from ..core.interfaces import AmpliconData
from ..core.standardized_parser import StandardizedParser

logger = logging.getLogger(__name__)

_PAIR_KEY = re.compile(r"^PRIMER_(LEFT|RIGHT)_(\d+)(_SEQUENCE)?$")


class Primer3Parser(StandardizedParser):
    """Parser for Primer3 Boulder-IO output."""

    @classmethod
    def format_name(cls) -> str:
        return "primer3"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".p3", ".primer3"]

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        file_path = Path(file_path)
        if not file_path.exists():
            return False
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                head = f.read(4096)
        except (OSError, UnicodeDecodeError):
            return False
        # Distinctive Primer3 Boulder-IO keys.
        return "PRIMER_LEFT_0" in head and (
            "_SEQUENCE=" in head or "SEQUENCE_ID=" in head
        )

    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        # Read all KEY=value pairs (Boulder-IO).
        fields: Dict[str, str] = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line == "=" or not line:
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                fields[key] = value

        sequence_id = fields.get("SEQUENCE_ID", prefix or "primer3_target")

        # Discover primer-pair indices present in the output.
        indices = set()
        for key in fields:
            m = _PAIR_KEY.match(key)
            if m:
                indices.add(int(m.group(2)))

        amplicons: Dict[str, AmpliconData] = {}
        for i in sorted(indices):
            left_seq = fields.get(f"PRIMER_LEFT_{i}_SEQUENCE")
            right_seq = fields.get(f"PRIMER_RIGHT_{i}_SEQUENCE")
            if not left_seq or not right_seq:
                continue

            amplicon_id = f"{sequence_id}_{i}"
            left_start, left_len = self._coord(fields.get(f"PRIMER_LEFT_{i}"))
            right_pos, right_len = self._coord(fields.get(f"PRIMER_RIGHT_{i}"))

            fwd_start = left_start if left_start is not None else 0
            fwd_stop = fwd_start + (left_len or len(left_seq))

            # Right primer spans [pos-len+1, pos] inclusive (0-based).
            if right_pos is not None:
                rlen = right_len or len(right_seq)
                rev_start = max(0, right_pos - rlen + 1)
                rev_stop = right_pos + 1
            else:
                rev_start = fwd_stop
                rev_stop = fwd_stop + len(right_seq)

            forward = self._create_primer_data(
                name=f"{amplicon_id}_LEFT",
                sequence=left_seq,
                start=fwd_start,
                stop=fwd_stop,
                strand="+",
                direction="forward",
                pool=1,
                amplicon_id=amplicon_id,
                reference_id=sequence_id,
                metadata={"primer3_index": i},
            )
            reverse = self._create_primer_data(
                name=f"{amplicon_id}_RIGHT",
                sequence=right_seq,
                start=rev_start,
                stop=rev_stop,
                strand="-",
                direction="reverse",
                pool=1,
                amplicon_id=amplicon_id,
                reference_id=sequence_id,
                metadata={"primer3_index": i},
            )

            amplicons[amplicon_id] = AmpliconData(
                amplicon_id=amplicon_id,
                primers=[forward, reverse],
                length=rev_stop - fwd_start,
                reference_id=sequence_id,
            )

        if not amplicons:
            raise InsufficientDataError(
                "No primer pairs found in Primer3 output",
                user_message=f"No Primer3 primer pairs found in {file_path}.",
            ).add_suggestion("Ensure the file is Primer3 Boulder-IO output")

        return amplicons

    @staticmethod
    def _coord(value):
        """Parse a Primer3 'start,length' coordinate; return (int|None, int|None)."""
        if not value:
            return None, None
        try:
            start_s, len_s = value.split(",")[:2]
            return int(start_s), int(len_s)
        except (ValueError, IndexError) as e:
            raise ParserError(f"Invalid Primer3 coordinate '{value}': {e}") from e
