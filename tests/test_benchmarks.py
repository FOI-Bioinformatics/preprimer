"""
Performance benchmarks using pytest-benchmark for preprimer components.
"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest

from preprimer.core.converter import PrimerConverter
from preprimer.core.enhanced_config import ConfigManager, EnhancedConfig
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.registry import ParserRegistry, WriterRegistry
from preprimer.core.security import InputValidator, PathValidator
from preprimer.parsers.artic_parser import ARTICParser
from preprimer.parsers.varvamp_parser import VarVAMPParser


class TestParserBenchmarks:
    """Benchmark parser performance."""

    def create_varvamp_data(
        self, num_amplicons: int = 100, primers_per_amplicon: int = 4
    ) -> str:
        """Create benchmark VarVAMP data."""
        header = [
            "amplicon_name",
            "amplicon_length",
            "primer_name",
            "pool",
            "start",
            "stop",
            "seq",
            "size",
            "gc_best",
            "temp_best",
            "mean_gc",
            "mean_temp",
            "score",
        ]

        lines = ["\t".join(header)]

        for amp_id in range(num_amplicons):
            amp_name = f"amplicon_{amp_id}"
            amp_length = 300

            # Forward primers
            for i in range(primers_per_amplicon // 2):
                lines.append(
                    "\t".join(
                        [
                            amp_name,
                            str(amp_length),
                            f"FW_{amp_id}_{i}",
                            "1",
                            str(100 + i * 20),
                            str(120 + i * 20),
                            "ATCGATCGATCGATCGATCG",
                            "20",
                            "0.5",
                            "60.0",
                            "0.52",
                            "58.5",
                            "85.2",
                        ]
                    )
                )

            # Reverse primers
            for i in range(primers_per_amplicon // 2):
                lines.append(
                    "\t".join(
                        [
                            amp_name,
                            str(amp_length),
                            f"RW_{amp_id}_{i}",
                            "1",
                            str(380 - i * 20),
                            str(400 - i * 20),
                            "CGATCGATCGATCGATCGAT",
                            "20",
                            "0.5",
                            "60.0",
                            "0.52",
                            "58.5",
                            "85.2",
                        ]
                    )
                )

        return "\n".join(lines)

    def create_artic_data(self, num_amplicons: int = 100) -> str:
        """Create benchmark ARTIC data."""
        lines = []

        for amp_id in range(num_amplicons):
            # Forward primer
            lines.append(
                "\t".join(
                    [
                        "ref",
                        str(100 + amp_id * 400),
                        str(120 + amp_id * 400),
                        f"nCoV-2019_400_{amp_id}_LEFT_1",
                        "1",
                        "+",
                        "ATCGATCGATCGATCGATCG",
                    ]
                )
            )

            # Reverse primer
            lines.append(
                "\t".join(
                    [
                        "ref",
                        str(480 + amp_id * 400),
                        str(500 + amp_id * 400),
                        f"nCoV-2019_400_{amp_id}_RIGHT_1",
                        "1",
                        "-",
                        "CGATCGATCGATCGATCGAT",
                    ]
                )
            )

        return "\n".join(lines)

    def test_varvamp_parser_small_benchmark(self, benchmark):
        """Benchmark VarVAMP parser with small dataset."""
        data = self.create_varvamp_data(num_amplicons=10)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = benchmark(parser.parse, temp_path, "test")

            assert len(result) == 10  # 10 amplicons

        finally:
            temp_path.unlink(missing_ok=True)

    def test_varvamp_parser_medium_benchmark(self, benchmark):
        """Benchmark VarVAMP parser with medium dataset."""
        data = self.create_varvamp_data(num_amplicons=100)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = benchmark(parser.parse, temp_path, "test")

            assert len(result) == 100  # 100 amplicons

        finally:
            temp_path.unlink(missing_ok=True)

    def test_varvamp_parser_large_benchmark(self, benchmark):
        """Benchmark VarVAMP parser with large dataset."""
        data = self.create_varvamp_data(num_amplicons=1000)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = benchmark(parser.parse, temp_path, "test")

            assert len(result) == 1000  # 1000 amplicons

        finally:
            temp_path.unlink(missing_ok=True)

    def test_artic_parser_benchmark(self, benchmark):
        """Benchmark ARTIC parser."""
        data = self.create_artic_data(num_amplicons=100)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".bed", delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)

        try:
            parser = ARTICParser()
            result = benchmark(parser.parse, temp_path, "test")

            assert len(result) == 100  # 100 amplicons

        finally:
            temp_path.unlink(missing_ok=True)

    def test_parser_validation_benchmark(self, benchmark):
        """Benchmark parser file validation."""
        data = self.create_varvamp_data(num_amplicons=100)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(data)
            temp_path = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = benchmark(parser.validate_file, temp_path)

            assert result is True

        finally:
            temp_path.unlink(missing_ok=True)


class TestConfigurationBenchmarks:
    """Benchmark configuration operations."""

    def test_config_creation_benchmark(self, benchmark):
        """Benchmark configuration creation."""
        result = benchmark(EnhancedConfig)
        assert isinstance(result, EnhancedConfig)

    def test_config_from_dict_benchmark(self, benchmark):
        """Benchmark configuration creation from dictionary."""
        config_data = {
            "alignment": {
                "aligner": "blast",
                "threads": 8,
                "timeout": 600,
                "params": {"evalue": 0.001, "max_targets": 10},
            },
            "validation": {
                "enabled": True,
                "min_length": 15,
                "max_length": 35,
                "min_gc": 0.3,
                "max_gc": 0.7,
            },
            "output": {"formats": ["artic", "fasta", "bed"], "force_overwrite": False},
            "plugins": {
                "enabled": True,
                "config": {
                    "plugin1": {"setting1": "value1"},
                    "plugin2": {"setting2": "value2"},
                },
            },
        }

        result = benchmark(EnhancedConfig, **config_data)
        assert isinstance(result, EnhancedConfig)
        assert result.alignment.aligner == "blast"

    def test_config_serialization_benchmark(self, benchmark):
        """Benchmark configuration serialization."""
        config = EnhancedConfig()
        result = benchmark(config.model_dump)
        assert isinstance(result, dict)

    def test_config_file_save_benchmark(self, benchmark):
        """Benchmark configuration file saving."""
        config = EnhancedConfig()

        def save_config():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                temp_path = Path(f.name)
            try:
                config.save(temp_path, format="json")
                return temp_path.exists()
            finally:
                temp_path.unlink(missing_ok=True)

        result = benchmark(save_config)
        assert result is True

    def test_config_file_load_benchmark(self, benchmark):
        """Benchmark configuration file loading."""
        config_data = {
            "alignment": {"aligner": "blast", "threads": 4},
            "debug_mode": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            result = benchmark(EnhancedConfig.from_file, temp_path, merge_env=False)
            assert isinstance(result, EnhancedConfig)
            assert result.alignment.aligner == "blast"

        finally:
            temp_path.unlink(missing_ok=True)

    def test_config_manager_updates_benchmark(self, benchmark):
        """Benchmark configuration manager updates."""
        manager = ConfigManager()

        def update_config():
            for i in range(10):
                manager.update_partial(debug_mode=(i % 2 == 0))
            return manager.config.debug_mode

        result = benchmark(update_config)
        assert isinstance(result, bool)


class TestRegistryBenchmarks:
    """Benchmark registry operations."""

    def test_parser_registry_creation_benchmark(self, benchmark):
        """Benchmark parser registry creation and registration."""

        def create_registry():
            registry = ParserRegistry()
            registry.register(VarVAMPParser)
            registry.register(ARTICParser)
            return registry

        result = benchmark(create_registry)
        assert isinstance(result, ParserRegistry)
        assert len(result.list_formats()) >= 2

    def test_format_detection_benchmark(self, benchmark):
        """Benchmark format detection performance."""
        registry = ParserRegistry()
        registry.register(VarVAMPParser)
        registry.register(ARTICParser)

        # Create test files
        varvamp_data = self.create_varvamp_data(num_amplicons=10)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(varvamp_data)
            temp_path = Path(f.name)

        try:
            result = benchmark(registry.detect_format, temp_path)
            assert result == "varvamp"

        finally:
            temp_path.unlink(missing_ok=True)

    def create_varvamp_data(self, num_amplicons: int = 10) -> str:
        """Helper method to create VarVAMP data."""
        header = [
            "amplicon_name",
            "amplicon_length",
            "primer_name",
            "pool",
            "start",
            "stop",
            "seq",
            "size",
            "gc_best",
            "temp_best",
            "mean_gc",
            "mean_temp",
            "score",
        ]
        lines = ["\t".join(header)]

        for i in range(num_amplicons):
            lines.append(
                f"amp_{i}\t300\tFW_{i}\t1\t100\t120\tATCGATCGATCGATCGATCG\t20\t0.5\t60.0\t0.52\t58.5\t85.2"
            )
            lines.append(
                f"amp_{i}\t300\tRW_{i}\t1\t380\t400\tCGATCGATCGATCGATCGAT\t20\t0.5\t60.0\t0.52\t58.5\t85.2"
            )

        return "\n".join(lines)

    def test_parser_instantiation_benchmark(self, benchmark):
        """Benchmark parser instantiation."""
        registry = ParserRegistry()
        registry.register(VarVAMPParser)

        result = benchmark(registry.get_parser, "varvamp")
        assert isinstance(result, VarVAMPParser)


class TestSecurityBenchmarks:
    """Benchmark security operations."""

    def test_path_validation_benchmark(self, benchmark):
        """Benchmark path validation performance."""
        test_path = Path("/tmp/test/file.txt")

        result = benchmark(PathValidator.sanitize_path, test_path)
        assert isinstance(result, Path)

    def test_input_validation_benchmark(self, benchmark):
        """Benchmark input validation performance."""
        test_input = "This is a test input string with some content"

        result = benchmark(InputValidator.sanitize_string, test_input)
        assert isinstance(result, str)
        assert len(result) <= len(test_input)

    def test_batch_path_validation_benchmark(self, benchmark):
        """Benchmark batch path validation."""
        test_paths = [Path(f"/tmp/test/file_{i}.txt") for i in range(100)]

        def validate_batch():
            results = []
            for path in test_paths:
                try:
                    results.append(PathValidator.sanitize_path(path))
                except Exception:
                    pass
            return results

        result = benchmark(validate_batch)
        assert isinstance(result, list)

    def test_batch_input_sanitization_benchmark(self, benchmark):
        """Benchmark batch input sanitization."""
        test_inputs = [f"test_input_{i}" for i in range(100)]

        def sanitize_batch():
            results = []
            for inp in test_inputs:
                try:
                    results.append(InputValidator.sanitize_string(inp))
                except Exception:
                    pass
            return results

        result = benchmark(sanitize_batch)
        assert isinstance(result, list)
        assert len(result) <= len(test_inputs)


class TestDataStructureBenchmarks:
    """Benchmark data structure operations."""

    def test_primer_data_creation_benchmark(self, benchmark):
        """Benchmark PrimerData creation."""

        def create_primer():
            return PrimerData(
                name="test_primer",
                sequence="ATCGATCGATCGATCGATCG",
                start=100,
                stop=120,
                strand="+",
                direction="forward",
                pool=1,
                amplicon_id="test_amplicon",
                reference_id="test_ref",
                gc_content=0.5,
                tm=60.0,
                score=85.0,
            )

        result = benchmark(create_primer)
        assert isinstance(result, PrimerData)
        assert result.name == "test_primer"

    def test_amplicon_data_creation_benchmark(self, benchmark):
        """Benchmark AmpliconData creation."""
        primers = []
        for i in range(10):
            primer = PrimerData(
                name=f"primer_{i}",
                sequence="ATCGATCGATCGATCGATCG",
                start=100 + i * 30,
                stop=120 + i * 30,
                strand="+" if i % 2 == 0 else "-",
                direction="forward" if i % 2 == 0 else "reverse",
                pool=1,
                amplicon_id="test_amplicon",
                reference_id="test_ref",
            )
            primers.append(primer)

        def create_amplicon():
            return AmpliconData(
                amplicon_id="test_amplicon",
                primers=primers,
                length=400,
                reference_id="test_ref",
            )

        result = benchmark(create_amplicon)
        assert isinstance(result, AmpliconData)
        assert len(result.primers) == 10

    def test_large_amplicon_creation_benchmark(self, benchmark):
        """Benchmark large AmpliconData creation."""
        primers = []
        for i in range(1000):
            primer = PrimerData(
                name=f"primer_{i}",
                sequence="ATCGATCGATCGATCGATCG",
                start=100 + i * 30,
                stop=120 + i * 30,
                strand="+" if i % 2 == 0 else "-",
                direction="forward" if i % 2 == 0 else "reverse",
                pool=i % 10 + 1,
                amplicon_id=f"amplicon_{i // 100}",
                reference_id="test_ref",
            )
            primers.append(primer)

        # Group primers by amplicon
        amplicons_data = {}
        for primer in primers:
            amp_id = primer.amplicon_id
            if amp_id not in amplicons_data:
                amplicons_data[amp_id] = []
            amplicons_data[amp_id].append(primer)

        def create_amplicons():
            amplicons = []
            for amp_id, amp_primers in amplicons_data.items():
                amplicon = AmpliconData(
                    amplicon_id=amp_id,
                    primers=amp_primers,
                    length=400,
                    reference_id="test_ref",
                )
                amplicons.append(amplicon)
            return amplicons

        result = benchmark(create_amplicons)
        assert isinstance(result, list)
        assert len(result) == 10  # 1000 primers / 100 per amplicon = 10 amplicons


class TestConverterBenchmarks:
    """Benchmark converter operations."""

    def test_converter_creation_benchmark(self, benchmark):
        """Benchmark PrimerConverter creation."""
        result = benchmark(PrimerConverter)
        assert isinstance(result, PrimerConverter)

    def test_format_conversion_benchmark(self, benchmark):
        """Benchmark format conversion performance."""
        # Create test VarVAMP file
        varvamp_data = """amplicon_name	amplicon_length	primer_name	pool	start	stop	seq	size	gc_best	temp_best	mean_gc	mean_temp	score
amplicon_1	300	FW_1	1	100	120	ATCGATCGATCGATCGATCG	20	0.5	60.0	0.52	58.5	85.2
amplicon_1	300	RW_1	1	380	400	CGATCGATCGATCGATCGAT	20	0.5	60.0	0.52	58.5	85.2"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(varvamp_data)
            input_path = Path(f.name)

        output_dir = Path(tempfile.mkdtemp())

        try:
            converter = PrimerConverter()

            def convert_format():
                return converter.convert(
                    input_file=input_path,
                    output_dir=output_dir,
                    output_formats=["fasta"],
                    force=True,
                )

            result = benchmark(convert_format)
            assert isinstance(result, dict)
            assert "fasta" in result

        finally:
            input_path.unlink(missing_ok=True)
            # Clean up output directory
            shutil.rmtree(output_dir, ignore_errors=True)


# Benchmark configuration
def pytest_benchmark_group_stats(stats):
    """Custom benchmark grouping."""
    return {
        "name": stats["name"],
        "min": stats["min"],
        "max": stats["max"],
        "mean": stats["mean"],
        "stddev": stats["stddev"],
        "median": stats["median"],
        "iqr": stats["iqr"],
        "outliers": stats["outliers"],
        "rounds": stats["rounds"],
    }


if __name__ == "__main__":
    pytest.main([__file__, "--benchmark-only", "-v"])
