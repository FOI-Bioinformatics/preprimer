"""
Parser and writer registry system for preprimer.
"""

import logging
from pathlib import Path
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

from .exceptions import OutputError, ParserError
from .interfaces import OutputWriter, PrimerParser

# Note: AlignmentProvider removed in v0.2.0 (unused functionality)
# AlignmentRegistry kept with deprecation warning for backward compatibility

logger = logging.getLogger(__name__)

# Type variable for generic registry
T = TypeVar("T")


class BaseRegistry(Generic[T]):
    """
    Base registry class for managing plugin-style components.

    This generic registry provides common functionality for registering,
    retrieving, and listing plugin classes (parsers, writers, aligners, etc.).

    Type Parameters:
        T: The base type of components managed by this registry
    """

    def __init__(self, component_type_name: str, error_class: Type[Exception]):
        """
        Initialize the base registry.

        Args:
            component_type_name: Human-readable name for component type (e.g., "parser", "writer")
            error_class: Exception class to raise for errors (e.g., ParserError, OutputError)
        """
        self._components: Dict[str, Type[T]] = {}
        self._component_type_name = component_type_name
        self._error_class = error_class

    def register(self, component_class: Type[T], key: str) -> None:
        """
        Register a component class.

        Args:
            component_class: The component class to register
            key: Registry key (usually format name or tool name)
        """
        key = key.lower()
        logger.debug(f"Registering {self._component_type_name}: {key}")
        self._components[key] = component_class

    def get_component(self, key: str) -> T:
        """
        Get component instance for a key.

        Args:
            key: Registry key to look up

        Returns:
            Instance of the component

        Raises:
            Exception: If component not found (uses error_class from __init__)
        """
        key = key.lower()
        if key not in self._components:
            available = list(self._components.keys())
            raise self._error_class(
                f"No {self._component_type_name} registered for: {key}. "
                f"Available: {available}"
            )
        return self._components[key]()

    def list_components(self) -> List[str]:
        """
        List all registered component keys.

        Returns:
            List of registered keys
        """
        return list(self._components.keys())

    def is_registered(self, key: str) -> bool:
        """
        Check if a component is registered.

        Args:
            key: Registry key to check

        Returns:
            True if registered, False otherwise
        """
        return key.lower() in self._components

    def get_component_class(self, key: str) -> Type[T]:
        """
        Get the component class (not instance) for a key.

        Args:
            key: Registry key to look up

        Returns:
            The component class

        Raises:
            Exception: If component not found
        """
        key = key.lower()
        if key not in self._components:
            raise self._error_class(
                f"No {self._component_type_name} registered for: {key}"
            )
        return self._components[key]


class ParserRegistry(BaseRegistry[PrimerParser]):
    """Registry for primer format parsers."""

    def __init__(self):
        super().__init__(component_type_name="parser", error_class=ParserError)
        self._format_extensions: Dict[str, List[str]] = {}

    def register(self, parser_class: Type[PrimerParser]) -> None:
        """Register a parser class."""
        # Get format info directly from class (no instance creation)
        format_name = parser_class.format_name().lower()

        # Register with base class
        super().register(parser_class, format_name)

        # Cache extensions for format detection
        self._format_extensions[format_name] = parser_class.file_extensions()

    def get_parser(self, format_name: str) -> PrimerParser:
        """Get parser instance for a format."""
        return self.get_component(format_name)

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
        for format_name in self._components:
            parser = self.get_parser(format_name)
            if parser.validate_file(file_path):
                return format_name

        return None

    def list_formats(self) -> List[str]:
        """List all registered formats."""
        return self.list_components()

    def list_extensions(self, format_name: str) -> List[str]:
        """List extensions for a format."""
        format_name = format_name.lower()
        return self._format_extensions.get(format_name, [])


class WriterRegistry(BaseRegistry[OutputWriter]):
    """Registry for output format writers."""

    def __init__(self):
        super().__init__(component_type_name="writer", error_class=OutputError)
        self._format_extensions: Dict[str, str] = {}

    def register(self, writer_class: Type[OutputWriter]) -> None:
        """Register a writer class."""
        # Get format info directly from class (no instance creation)
        format_name = writer_class.format_name().lower()

        # Register with base class
        super().register(writer_class, format_name)

        # Cache extension for easy lookup
        self._format_extensions[format_name] = writer_class.file_extension()

    def get_writer(self, format_name: str) -> OutputWriter:
        """Get writer instance for a format."""
        return self.get_component(format_name)

    def list_formats(self) -> List[str]:
        """List all registered output formats."""
        return self.list_components()

    def get_extension(self, format_name: str) -> str:
        """Get file extension for a format."""
        format_name = format_name.lower()
        return self._format_extensions.get(format_name, "")


class AlignmentRegistry(BaseRegistry["AlignmentProvider"]):  # noqa: F821
    """Registry for alignment providers (BLAST, Exonerate, me-PCR)."""

    def __init__(self):
        # Import here to avoid circular import
        from preprimer.core.exceptions import ParserError as AlignmentError

        super().__init__(
            component_type_name="alignment provider", error_class=AlignmentError
        )

    def register(self, provider_class: Type["AlignmentProvider"]) -> None:  # noqa: F821
        """
        Register an alignment provider class.

        Args:
            provider_class: AlignmentProvider subclass to register
        """
        # Get tool info directly from class (no instance creation)
        tool_name = provider_class.tool_name().lower()

        # Register with base class
        super().register(provider_class, tool_name)

    def get_provider(self, tool_name: str) -> "AlignmentProvider":  # noqa: F821
        """
        Get alignment provider instance.

        Args:
            tool_name: Name of the alignment tool (blast, exonerate, me-pcr)

        Returns:
            AlignmentProvider instance

        Raises:
            ParserError: If provider not found
        """
        return self.get_component(tool_name)

    def list_providers(self) -> List[str]:
        """
        List all registered alignment providers.

        Returns:
            List of provider names
        """
        return self.list_components()

    def list_available_providers(self) -> List[str]:
        """
        List alignment providers that are actually available on the system.

        .. deprecated:: 0.2.0
            Always returns empty list as no providers exist.
        """
        available = []
        for tool_name in self.list_providers():
            provider = self.get_provider(tool_name)
            if hasattr(provider, "is_available") and provider.is_available():
                available.append(tool_name)
        return available


# Global registry instances
parser_registry = ParserRegistry()
writer_registry = WriterRegistry()
alignment_registry = AlignmentRegistry()
