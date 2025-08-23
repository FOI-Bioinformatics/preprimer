"""
Abstract base classes and data structures for preprimer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd


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

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name this parser handles."""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> List[str]:
        """Return supported file extensions."""
        pass

    @abstractmethod
    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """Validate that the file can be parsed by this parser."""
        pass

    @abstractmethod
    def parse(
        self, file_path: Union[str, Path], prefix: str = ""
    ) -> List[AmpliconData]:
        """Parse primer file and return list of AmpliconData objects."""
        pass

    def get_reference_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """Get associated reference file if it exists."""
        return None


class OutputWriter(ABC):
    """Abstract base class for output format writers."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the output format name."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass

    @abstractmethod
    def write(
        self,
        amplicons: List[AmpliconData],
        output_path: Union[str, Path],
        reference_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> None:
        """Write amplicon data to the specified output format."""
        pass

    def validate_output_path(self, output_path: Union[str, Path]) -> Path:
        """Validate and prepare output path."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


class AlignmentProvider(ABC):
    """Abstract base class for alignment tools."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the alignment tool name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the alignment tool is available."""
        pass

    @abstractmethod
    def align_primers(
        self,
        primers: List[PrimerData],
        reference_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> List[PrimerData]:
        """Align primers to reference and return updated primer data."""
        pass

    @abstractmethod
    def create_amplicons(
        self,
        primers_file: Union[str, Path],
        reference_path: Union[str, Path],
        output_path: Union[str, Path],
    ) -> pd.DataFrame:
        """Create in-silico PCR amplicons."""
        pass
