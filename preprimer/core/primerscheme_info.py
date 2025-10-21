"""
Official primerscheme info.json schema and generation.

Based on the primal-page specification:
https://github.com/artic-network/primal-page
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class PrimerschemeInfo:
    """
    Official primerscheme info.json metadata following primal-page specification.

    Based on: https://github.com/artic-network/primal-page
    """

    # Required fields
    schemename: str  # Lowercase alphanumeric with hyphens, cannot start/end with hyphen
    schemeversion: str  # Format "v{Major}.{Minor}.{Patch}"
    ampliconsize: int  # Positive integer representing amplicon size
    species: str  # NCBI Taxonomy IDs recommended
    primer_bed_md5: str  # MD5 hash of primer.bed file
    reference_fasta_md5: str  # MD5 hash of reference.fasta file

    # Standard fields
    articbedversion: str = "v3.0"  # Version of primer.bed format
    infoschema: str = "v2.0.0"  # Version of info.json schema
    primerclass: str = "primerscheme"  # Currently only "primerscheme"
    status: str = "draft"  # "draft", "tested", "validated", etc.

    # Optional fields
    authors: List[str] = field(default_factory=list)  # Primary contributors
    citations: List[str] = field(default_factory=list)  # DOI links recommended
    algorithmversion: Optional[str] = None  # Scheme generation algorithm version
    collections: List[str] = field(
        default_factory=list
    )  # Tags like "ARTIC", "WASTE-WATER"
    description: Optional[str] = None  # Free text description
    license: Optional[str] = None  # Software license

    # Additional optional fields from primal-page spec
    contactinfo: Optional[str] = None  # Contact information
    derivedfrom: Optional[str] = None  # Parent scheme if derived
    links: Optional[Dict[str, List[str]]] = None  # Various related links

    # PrePrimer specific metadata
    created_by: str = "PrePrimer"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate the schema after initialization."""
        self._validate_schemename()
        self._validate_schemeversion()
        self._validate_ampliconsize()

    def _validate_schemename(self):
        """Validate schemename follows official specification."""
        if not self.schemename:
            raise ValueError("schemename cannot be empty")

        # Must be lowercase alphanumeric with hyphens
        import re

        if not re.match(r"^[a-z0-9-]+$", self.schemename):
            raise ValueError(
                "schemename must be lowercase alphanumeric with hyphens only"
            )

        # Cannot start or end with hyphen
        if self.schemename.startswith("-") or self.schemename.endswith("-"):
            raise ValueError("schemename cannot start or end with hyphen")

    def _validate_schemeversion(self):
        """Validate schemeversion follows semantic versioning."""
        import re

        pattern = r"^v\d+\.\d+\.\d+(-[a-zA-Z0-9-]+)?$"
        if not re.match(pattern, self.schemeversion):
            raise ValueError(
                "schemeversion must follow format 'v{Major}.{Minor}.{Patch}[-suffix]'"
            )

    def _validate_ampliconsize(self):
        """Validate ampliconsize is positive."""
        if not isinstance(self.ampliconsize, int) or self.ampliconsize <= 0:
            raise ValueError("ampliconsize must be a positive integer")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def save(self, file_path: Union[str, Path]) -> None:
        """Save info.json to file."""
        file_path = Path(file_path)
        with open(file_path, "w") as f:
            f.write(self.to_json())

        logger.info(f"Saved primerscheme info.json to {file_path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrimerschemeInfo":
        """Create instance from dictionary."""
        # Handle default factory fields
        if "authors" not in data:
            data["authors"] = []
        if "citations" not in data:
            data["citations"] = []
        if "collections" not in data:
            data["collections"] = []

        # Handle fields that might not be in PrePrimer-generated data
        if "created_by" not in data:
            data["created_by"] = "External"
        if "created_date" not in data:
            data["created_date"] = datetime.now().isoformat()

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "PrimerschemeInfo":
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "PrimerschemeInfo":
        """Load from info.json file."""
        file_path = Path(file_path)
        with open(file_path, "r") as f:
            return cls.from_json(f.read())


def calculate_md5(file_path: Union[str, Path]) -> str:
    """Calculate MD5 hash of a file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def generate_info_json(
    schemename: str,
    schemeversion: str,
    ampliconsize: int,
    species: str,
    primer_bed_path: Union[str, Path],
    reference_fasta_path: Union[str, Path],
    authors: Optional[List[str]] = None,
    description: Optional[str] = None,
    collections: Optional[List[str]] = None,
    **kwargs,
) -> PrimerschemeInfo:
    """
    Generate info.json for a primerscheme.

    Args:
        schemename: Scheme name (lowercase alphanumeric with hyphens)
        schemeversion: Version string (v{Major}.{Minor}.{Patch})
        ampliconsize: Target amplicon size in base pairs
        species: Species name or NCBI Taxonomy ID
        primer_bed_path: Path to primer.bed file
        reference_fasta_path: Path to reference.fasta file
        authors: List of author names
        description: Free text description
        collections: Tags like ["ARTIC", "COVID-19"]
        **kwargs: Additional metadata fields

    Returns:
        PrimerschemeInfo object
    """
    primer_bed_path = Path(primer_bed_path)
    reference_fasta_path = Path(reference_fasta_path)

    # Calculate MD5 hashes
    primer_bed_md5 = calculate_md5(primer_bed_path)
    reference_fasta_md5 = calculate_md5(reference_fasta_path)

    # Create info object
    info = PrimerschemeInfo(
        schemename=schemename,
        schemeversion=schemeversion,
        ampliconsize=ampliconsize,
        species=species,
        primer_bed_md5=primer_bed_md5,
        reference_fasta_md5=reference_fasta_md5,
        authors=authors or [],
        description=description,
        collections=collections or [],
        **kwargs,
    )

    return info


def validate_primerscheme_directory(scheme_dir: Union[str, Path]) -> Dict[str, bool]:
    """
    Validate that a directory contains valid primerscheme files.

    Args:
        scheme_dir: Path to primerscheme directory

    Returns:
        Dictionary with validation results for each required file
    """
    scheme_dir = Path(scheme_dir)

    results = {
        "directory_exists": scheme_dir.exists() and scheme_dir.is_dir(),
        "primer_bed_exists": (scheme_dir / "primer.bed").exists(),
        "reference_fasta_exists": (scheme_dir / "reference.fasta").exists(),
        "info_json_exists": (scheme_dir / "info.json").exists(),
        "info_json_valid": False,
        "md5_hashes_match": False,
    }

    if results["info_json_exists"]:
        try:
            info = PrimerschemeInfo.from_file(scheme_dir / "info.json")
            results["info_json_valid"] = True

            # Verify MD5 hashes if files exist
            if results["primer_bed_exists"] and results["reference_fasta_exists"]:
                primer_md5 = calculate_md5(scheme_dir / "primer.bed")
                ref_md5 = calculate_md5(scheme_dir / "reference.fasta")

                results["md5_hashes_match"] = (
                    primer_md5 == info.primer_bed_md5
                    and ref_md5 == info.reference_fasta_md5
                )

        except Exception as e:
            logger.warning(f"Invalid info.json in {scheme_dir}: {e}")

    return results
