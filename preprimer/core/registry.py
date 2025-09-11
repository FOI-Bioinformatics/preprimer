"""
Parser and writer registry system for preprimer.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from .exceptions import OutputError, ParserError
from .interfaces import AlignmentProvider, OutputWriter, PrimerParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Registry for primer format parsers."""

    def __init__(self):
        self._parsers: Dict[str, Type[PrimerParser]] = {}
        self._format_extensions: Dict[str, List[str]] = {}

    def register(self, parser_class: Type[PrimerParser]) -> None:
        """Register a parser class."""
        # Get format info directly from class (no instance creation)
        format_name = parser_class.format_name().lower()

        logger.debug(f"Registering parser for format: {format_name}")

        self._parsers[format_name] = parser_class
        self._format_extensions[format_name] = parser_class.file_extensions()

    def get_parser(self, format_name: str) -> PrimerParser:
        """Get parser instance for a format."""
        format_name = format_name.lower()
        if format_name not in self._parsers:
            raise ParserError(f"No parser registered for format: {format_name}")

        return self._parsers[format_name]()

    def detect_format(self, file_path: Union[str, Path]) -> Optional[str]:
        """Auto-detect file format based on extension and content."""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        # First try by extension - create instances only when needed
        for format_name, extensions in self._format_extensions.items():
            if extension in extensions:
                parser = self.get_parser(format_name)
                if parser.validate_file(file_path):
                    return format_name

        # If extension doesn't match, try all parsers
        for format_name in self._parsers:
            parser = self.get_parser(format_name)
            if parser.validate_file(file_path):
                return format_name

        return None

    def detect_format_optimized(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Optimized format detection that minimizes instance creation.

        This method only creates parser instances when validation is needed,
        and reuses cached validation results where possible.
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        # Build a priority list: extension matches first, then others
        priority_formats = []
        other_formats = []

        for format_name, extensions in self._format_extensions.items():
            if extension in extensions:
                priority_formats.append(format_name)
            else:
                other_formats.append(format_name)

        # Try priority formats first (extension matches)
        for format_name in priority_formats:
            parser = self.get_parser(format_name)
            if parser.validate_file(file_path):
                return format_name

        # Then try other formats
        for format_name in other_formats:
            parser = self.get_parser(format_name)
            if parser.validate_file(file_path):
                return format_name

        return None

    def list_formats(self) -> List[str]:
        """List all registered formats."""
        return list(self._parsers.keys())

    def list_extensions(self, format_name: str) -> List[str]:
        """List extensions for a format."""
        format_name = format_name.lower()
        return self._format_extensions.get(format_name, [])


class WriterRegistry:
    """Registry for output format writers."""

    def __init__(self):
        self._writers: Dict[str, Type[OutputWriter]] = {}
        self._format_extensions: Dict[str, str] = {}

    def register(self, writer_class: Type[OutputWriter]) -> None:
        """Register a writer class."""
        # Get format info directly from class (no instance creation)
        format_name = writer_class.format_name().lower()

        logger.debug(f"Registering writer for format: {format_name}")

        self._writers[format_name] = writer_class
        self._format_extensions[format_name] = writer_class.file_extension()

    def get_writer(self, format_name: str) -> OutputWriter:
        """Get writer instance for a format."""
        format_name = format_name.lower()
        if format_name not in self._writers:
            raise OutputError(f"No writer registered for format: {format_name}")

        return self._writers[format_name]()

    def list_formats(self) -> List[str]:
        """List all registered output formats."""
        return list(self._writers.keys())

    def get_extension(self, format_name: str) -> str:
        """Get file extension for a format."""
        format_name = format_name.lower()
        return self._format_extensions.get(format_name, "")


class AlignmentRegistry:
    """Registry for alignment providers."""

    def __init__(self):
        self._providers: Dict[str, Type[AlignmentProvider]] = {}

    def register(self, provider_class: Type[AlignmentProvider]) -> None:
        """Register an alignment provider class."""
        # Get tool info directly from class (no instance creation)
        tool_name = provider_class.tool_name().lower()

        logger.debug(f"Registering alignment provider: {tool_name}")

        self._providers[tool_name] = provider_class

    def get_provider(self, tool_name: str) -> AlignmentProvider:
        """Get alignment provider instance."""
        tool_name = tool_name.lower()
        if tool_name not in self._providers:
            available = list(self._providers.keys())
            raise ParserError(
                f"No alignment provider for: {tool_name}. Available: {available}"
            )

        return self._providers[tool_name]()

    def list_providers(self) -> List[str]:
        """List all registered alignment providers."""
        return list(self._providers.keys())

    def list_available_providers(self) -> List[str]:
        """List alignment providers that are actually available on the system."""
        available = []
        for tool_name, provider_class in self._providers.items():
            provider = provider_class()
            if provider.is_available():
                available.append(tool_name)
        return available


# Global registry instances
parser_registry = ParserRegistry()
writer_registry = WriterRegistry()
alignment_registry = AlignmentRegistry()
