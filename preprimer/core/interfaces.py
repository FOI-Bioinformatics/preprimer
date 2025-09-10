"""
Abstract base classes and data structures for preprimer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# import pandas as pd  # Removed to avoid dependency


@dataclass
class PrimerData:
    """Standard primer data structure."""

    name: str
    sequence: str
    start: int
    stop: int
    strand: str  # '+' or '-'
    direction: str  # 'forward' or 'reverse'
    pool: Optional[int] = None
    amplicon_id: str = ""
    reference_id: str = ""

    # Optional quality metrics
    gc_content: Optional[float] = None
    tm: Optional[float] = None
    score: Optional[float] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> int:
        """Return primer length."""
        return len(self.sequence)

    @property
    def artic_name(self) -> str:
        """Generate ARTIC-compatible primer name."""
        amplicon_num = (
            self.amplicon_id.split("_")[-1]
            if "_" in self.amplicon_id
            else self.amplicon_id
        )
        side = "LEFT" if self.direction == "forward" else "RIGHT"
        return f"{self.reference_id}_{amplicon_num}_{side}_0"


@dataclass
class AmpliconData:
    """Standard amplicon data structure."""

    amplicon_id: str
    primers: List[PrimerData]
    length: Optional[int] = None
    reference_id: str = ""

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def forward_primers(self) -> List[PrimerData]:
        """Get forward primers for this amplicon."""
        return [p for p in self.primers if p.direction == "forward"]

    @property
    def reverse_primers(self) -> List[PrimerData]:
        """Get reverse primers for this amplicon."""
        return [p for p in self.primers if p.direction == "reverse"]

    def get_primer_pairs(self) -> List[tuple[PrimerData, PrimerData]]:
        """Get all possible primer pairs (forward, reverse)."""
        pairs = []
        for fwd in self.forward_primers:
            for rev in self.reverse_primers:
                pairs.append((fwd, rev))
        return pairs


class PrimerParser(ABC):
    """Abstract base class for primer format parsers."""

    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Return the format name this parser handles."""

    @classmethod
    @abstractmethod
    def file_extensions(cls) -> List[str]:
        """Return supported file extensions."""

    @abstractmethod
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that the file can be parsed by this parser."""

    @abstractmethod
    def parse(
        self, file_path: Union[str, Path], prefix: str = ""
    ) -> List[AmpliconData]:
        """Parse primer file and return list of AmpliconData objects."""

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """Get associated reference file if it exists."""
        return None


class OutputWriter(ABC):
    """Abstract base class for output format writers."""

    @classmethod
    @abstractmethod
    def format_name(cls) -> str:
        """Return the output format name."""

    @classmethod
    @abstractmethod
    def file_extension(cls) -> str:
        """Return the file extension for this format."""

    @abstractmethod
    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        prefix: str = "",
        **kwargs,
    ) -> Optional[Path]:
        """Write amplicon data to the specified output format."""

    def validate_output_path(self, output_path: Union[str, Path]) -> Path:
        """Validate and prepare output path."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class AlignmentProvider(ABC):
    """Abstract base class for alignment tools."""

    @classmethod
    @abstractmethod
    def tool_name(cls) -> str:
        """Return the alignment tool name."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the alignment tool is available."""

    @abstractmethod
    def align_primers(
        self,
        primers: List[PrimerData],
        reference_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> List[PrimerData]:
        """Align primers to reference and return updated primer data."""

    @abstractmethod
    def create_amplicons(
        self,
        primers_file: Union[str, Path],
        reference_path: Union[str, Path],
        output_path: Union[str, Path],
    ) -> Any:
        """Create in-silico PCR amplicons."""
