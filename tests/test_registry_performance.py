"""
Performance tests for the optimized registry system.
"""

import time
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from preprimer.core.interfaces import PrimerParser
from preprimer.core.registry import ParserRegistry
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.olivar_parser import OlivarParser
from preprimer.parsers.varvamp_parser import VarVAMPParser


class SlowMockParser(PrimerParser):
    """Mock parser that simulates slow initialization."""

    def __init__(self):
        # Simulate slow initialization
        time.sleep(0.1)  # 100ms delay
        super().__init__()

    @classmethod
    def format_name(cls) -> str:
        return "slow_mock"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".slow"]

    def validate_file(self, file_path) -> bool:
        return True

    def parse(self, file_path, prefix=""):
        return []


class OldStyleSlowParser(PrimerParser):
    """Mock parser using old instance-based properties."""

    def __init__(self):
        # Simulate slow initialization
        time.sleep(0.1)  # 100ms delay
        super().__init__()
        self._format_name = "old_slow"
        self._file_extensions = [".old"]

    @property
    def format_name(self) -> str:
        return self._format_name

    @property
    def file_extensions(self) -> List[str]:
        return self._file_extensions

    def validate_file(self, file_path) -> bool:
        return True

    def parse(self, file_path, prefix=""):
        return []


class TestRegistryPerformance:
    """Test registry performance optimizations."""

    def test_registration_performance_improvement(self):
        """Test that class-level metadata improves registration performance."""

        # Test optimized registration (class methods)
        optimized_registry = ParserRegistry()

        start_time = time.time()
        optimized_registry.register(SlowMockParser)
        optimized_time = time.time() - start_time

        # The registration should be fast because it doesn't create instances
        assert (
            optimized_time < 0.05
        ), f"Optimized registration took {optimized_time:.3f}s, should be <0.05s"

        # Verify the parser was registered correctly
        assert "slow_mock" in optimized_registry.list_formats()
        assert optimized_registry.list_extensions("slow_mock") == [".slow"]

    def test_multiple_registrations_performance(self):
        """Test performance when registering multiple parsers."""

        # Create multiple slow parsers
        parsers = [VarVAMPParser, ARTICParser, OlivarParser]

        # Test optimized registration
        optimized_registry = ParserRegistry()
        start_time = time.time()

        for parser_class in parsers:
            optimized_registry.register(parser_class)

        optimized_time = time.time() - start_time

        # Should be very fast since no instances are created during registration
        assert (
            optimized_time < 0.01
        ), f"Multiple registrations took {optimized_time:.3f}s, should be <0.01s"

        # Verify all parsers were registered
        formats = optimized_registry.list_formats()
        assert "varvamp" in formats
        assert "artic" in formats
        assert "olivar" in formats

    def test_format_detection_memory_efficiency(self):
        """Test that format detection only creates instances when needed."""

        registry = ParserRegistry()
        registry.register(VarVAMPParser)
        registry.register(ARTICParser)
        registry.register(OlivarParser)

        # Create a mock file that would match VarVAMP format
        test_file = Path("/tmp/test.tsv")  # VarVAMP extension

        # Mock the validation to track instance creation
        instance_count = {"count": 0}

        def mock_get_parser(format_name):
            instance_count["count"] += 1
            return registry._components[format_name]()

        # Test format detection
        with patch.object(registry, "get_parser", side_effect=mock_get_parser):
            with patch.object(VarVAMPParser, "validate_file", return_value=True):
                detected_format = registry.detect_format(test_file)

        # Should have found VarVAMP format
        assert detected_format == "varvamp"

        # Should have created only one instance (VarVAMP, since it matches by extension first)
        assert (
            instance_count["count"] == 1
        ), f"Created {instance_count['count']} instances, should be 1"

    def test_registry_metadata_access_performance(self):
        """Test that accessing format metadata is fast."""

        registry = ParserRegistry()
        registry.register(VarVAMPParser)
        registry.register(ARTICParser)
        registry.register(OlivarParser)

        # Test metadata access speed
        start_time = time.time()

        for _ in range(1000):
            formats = registry.list_formats()
            for format_name in formats:
                extensions = registry.list_extensions(format_name)
                assert len(extensions) > 0

        access_time = time.time() - start_time

        # Should be very fast since no instances are created
        assert (
            access_time < 0.1
        ), f"Metadata access took {access_time:.3f}s for 1000 iterations, should be <0.1s"

    def test_class_method_vs_instance_property_performance(self):
        """Test that class methods work correctly without requiring instance creation."""

        # Test class method access (optimized) - no instance creation needed
        format_name = VarVAMPParser.format_name()
        extensions = VarVAMPParser.file_extensions()

        assert format_name == "varvamp"
        assert extensions == [".tsv", ".txt"]
        assert len(extensions) > 0

        # Test that we can still create instances when needed
        instance = VarVAMPParser()
        assert instance.format_name() == format_name
        assert instance.file_extensions() == extensions

        # The key improvement is that we don't need to create instances
        # just to access metadata in the registry

    def test_parser_registry_memory_usage(self):
        """Test that registry uses minimal memory by not storing instances."""

        registry = ParserRegistry()

        # Register parsers
        registry.register(VarVAMPParser)
        registry.register(ARTICParser)
        registry.register(OlivarParser)

        # Registry should only store class references, not instances
        for format_name, parser_class in registry._components.items():
            # Should be a class, not an instance
            assert isinstance(parser_class, type)
            assert issubclass(parser_class, PrimerParser)

            # Verify we can still create instances when needed
            instance = parser_class()
            assert isinstance(instance, PrimerParser)
            assert instance.format_name() == format_name


class TestRegistryMemoryEfficiency:
    """Test memory efficiency of the registry."""

    def test_no_instance_storage_in_registry(self):
        """Test that registry doesn't store parser instances."""

        registry = ParserRegistry()

        # Mock a parser class to track instantiation
        instantiation_count = {"count": 0}

        class TrackedParser(PrimerParser):
            def __init__(self):
                instantiation_count["count"] += 1
                super().__init__()

            @classmethod
            def format_name(cls):
                return "tracked"

            @classmethod
            def file_extensions(cls):
                return [".tracked"]

            def validate_file(self, file_path):
                return True

            def parse(self, file_path, prefix=""):
                return []

        # Register the parser
        registry.register(TrackedParser)

        # Registration should not have created any instances
        assert (
            instantiation_count["count"] == 0
        ), f"Registration created {instantiation_count['count']} instances, should be 0"

        # Verify metadata is accessible without creating instances
        formats = registry.list_formats()
        assert "tracked" in formats

        extensions = registry.list_extensions("tracked")
        assert extensions == [".tracked"]

        # Still no instances should have been created
        assert (
            instantiation_count["count"] == 0
        ), f"Metadata access created {instantiation_count['count']} instances, should be 0"

        # Only when we actually get a parser should an instance be created
        parser_instance = registry.get_parser("tracked")
        assert (
            instantiation_count["count"] == 1
        ), f"get_parser created {instantiation_count['count']} instances, should be 1"

        assert isinstance(parser_instance, TrackedParser)
        assert parser_instance.format_name() == "tracked"

    def test_concurrent_registry_access(self):
        """Test that multiple registry operations don't interfere."""

        registry = ParserRegistry()
        registry.register(VarVAMPParser)
        registry.register(ARTICParser)
        registry.register(OlivarParser)

        # Simulate concurrent access to registry metadata
        results = []

        def access_registry():
            formats = registry.list_formats()
            for format_name in formats:
                extensions = registry.list_extensions(format_name)
                results.append((format_name, extensions))

        # Multiple concurrent accesses
        import threading

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=access_registry)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have results from all threads
        assert len(results) > 0

        # All results should be consistent
        format_counts = {}
        for format_name, extensions in results:
            if format_name not in format_counts:
                format_counts[format_name] = []
            format_counts[format_name].append(extensions)

        # Each format should have consistent extensions across all accesses
        for format_name, extensions_list in format_counts.items():
            first_extensions = extensions_list[0]
            for extensions in extensions_list[1:]:
                assert (
                    extensions == first_extensions
                ), f"Inconsistent extensions for {format_name}: {extensions} vs {first_extensions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
