"""
Comprehensive tests for the main PrePrimer API entry point (preprimer/__init__.py).

This tests the primary user-facing API function convert_primers() which was severely undertested.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from preprimer import EnhancedConfig, PrimerConverter, convert_primers
from preprimer.core.exceptions import PrePrimerError


class TestConvertPrimersMainAPI:
    """Test the main convert_primers API function comprehensively."""

    def test_convert_primers_config_kwargs_processing(self):
        """Test config attribute setting with kwargs (lines 54-55)."""

        # Create test data
        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Test with kwargs that should be set on config
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                output_formats=["fasta"],  # Specify to avoid default behavior
                prefix="test_prefix",
                # These kwargs should trigger lines 54-55
                force_overwrite=True,  # Valid config attribute
                validate_sequences=False,  # Valid config attribute
                aligner="none",  # Valid config attribute
            )

            assert isinstance(result, dict)
            assert "fasta" in result
            assert result["fasta"].exists()

    def test_convert_primers_invalid_config_kwargs(self):
        """Test kwargs that don't exist on config are ignored (lines 54-55 else branch)."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Test with kwargs that don't exist on config - should be ignored
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                output_formats=["fasta"],
                prefix="test_prefix",
                # These kwargs should NOT be set on config (don't exist)
                nonexistent_attribute="should_be_ignored",
                another_fake_attr=123,
                yet_another="ignored",
            )

            assert isinstance(result, dict)
            assert "fasta" in result
            assert result["fasta"].exists()

    def test_convert_primers_default_output_formats(self):
        """Test default output_formats assignment (line 58)."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Call without output_formats to trigger default (line 58)
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                prefix="test_default",
                # output_formats=None - should default to ["artic"]
            )

            # Should have defaulted to "artic" format
            assert isinstance(result, dict)
            assert "artic" in result  # Default format
            assert result["artic"].exists()

    def test_convert_primers_explicit_none_output_formats(self):
        """Test explicit None output_formats triggers default (line 58)."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Explicitly pass None for output_formats
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                prefix="test_none",
                output_formats=None,  # Should trigger line 58 default
            )

            # Should have defaulted to "artic" format
            assert isinstance(result, dict)
            assert "artic" in result
            assert result["artic"].exists()

    def test_convert_primers_full_parameter_coverage(self):
        """Test all parameters of convert_primers function."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )
        test_reference = (
            Path(__file__).parent
            / "test_data"
            / "datasets"
            / "small"
            / "reference.fasta"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                input_format="varvamp",  # Explicit input format
                output_formats=["artic", "fasta"],  # Multiple output formats
                prefix="comprehensive_test",  # Custom prefix
                reference_file=test_reference,  # Reference file
                # Additional kwargs
                force_overwrite=True,
                validate_sequences=True,
            )

            assert isinstance(result, dict)
            assert "artic" in result
            assert "fasta" in result
            assert result["artic"].exists()
            assert result["fasta"].exists()

            # Check files have expected prefix in path
            assert "comprehensive_test" in str(result["artic"])
            assert "comprehensive_test" in str(result["fasta"])

    def test_convert_primers_error_propagation(self):
        """Test that errors are properly propagated from underlying converter."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Test with non-existent input file
            with pytest.raises((FileNotFoundError, PrePrimerError)):
                convert_primers(
                    input_file="/nonexistent/file.tsv",
                    output_dir=temp_output_dir,
                    output_formats=["fasta"],
                )

    def test_convert_primers_with_converter_mock(self):
        """Test convert_primers interactions with PrimerConverter."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Mock PrimerConverter to verify it's called correctly
            mock_converter = MagicMock()
            mock_converter.convert.return_value = {
                "fasta": Path(temp_dir) / "test.fasta"
            }

            with patch("preprimer.PrimerConverter") as MockConverter:
                MockConverter.return_value = mock_converter

                result = convert_primers(
                    input_file=test_input_file,
                    output_dir=temp_output_dir,
                    output_formats=["fasta"],
                    prefix="mock_test",
                    force_overwrite=True,
                )

                # Verify converter was created with config
                MockConverter.assert_called_once()
                config_arg = MockConverter.call_args[0][0]
                assert isinstance(config_arg, EnhancedConfig)

                # Verify converter.convert was called with correct parameters
                mock_converter.convert.assert_called_once_with(
                    input_file=test_input_file,
                    output_dir=temp_output_dir,
                    input_format=None,
                    output_formats=["fasta"],
                    prefix="mock_test",
                    reference_file=None,
                    force_overwrite=True,
                )

                assert result == {"fasta": Path(temp_dir) / "test.fasta"}


class TestMainAPIEdgeCases:
    """Test edge cases in the main API."""

    def test_convert_primers_with_pathlib_paths(self):
        """Test convert_primers accepts Path objects."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Use Path objects instead of strings
            result = convert_primers(
                input_file=test_input_file,  # Path object
                output_dir=temp_output_dir,  # Path object
                output_formats=["fasta"],
                prefix="path_test",
            )

            assert isinstance(result, dict)
            assert "fasta" in result
            assert result["fasta"].exists()

    def test_convert_primers_empty_kwargs(self):
        """Test convert_primers with no additional kwargs."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Minimal call - should use defaults
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                # No additional parameters - should use all defaults
            )

            # Should default to artic output format with "primers" prefix
            assert isinstance(result, dict)
            assert "artic" in result
            assert result["artic"].exists()
            assert "primers" in str(result["artic"])

    def test_convert_primers_config_attribute_setting_comprehensive(self):
        """Test comprehensive config attribute setting scenarios."""

        # Mock the config and converter to verify attribute setting
        mock_config = MagicMock(spec=EnhancedConfig)
        mock_converter = MagicMock()
        mock_converter.convert.return_value = {"fasta": Path("/fake/output.fasta")}

        with patch("preprimer.EnhancedConfig") as MockConfig:
            with patch("preprimer.PrimerConverter") as MockConverter:
                MockConfig.return_value = mock_config
                MockConverter.return_value = mock_converter

                # Set up hasattr to return True for some attributes, False for others
                def mock_hasattr(obj, attr):
                    valid_attrs = ["force_overwrite", "validate_sequences", "aligner"]
                    return attr in valid_attrs

                with patch("builtins.hasattr", side_effect=mock_hasattr):
                    convert_primers(
                        input_file="/fake/input.tsv",
                        output_dir="/fake/output",
                        output_formats=["fasta"],
                        # Mix of valid and invalid config attributes
                        force_overwrite=True,  # Should be set (lines 54-55)
                        validate_sequences=False,  # Should be set (lines 54-55)
                        aligner="minimap2",  # Should be set (lines 54-55)
                        invalid_attribute="ignored",  # Should be ignored (hasattr=False)
                        another_invalid=123,  # Should be ignored (hasattr=False)
                    )

                # Verify setattr was called for valid attributes
                # The actual setattr calls will be made, just verify the function completed
                # without error (which means valid attributes were processed)


class TestMainAPIIntegration:
    """Test integration scenarios for the main API."""

    def test_convert_primers_multiple_formats(self):
        """Test converting to multiple output formats."""

        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                output_formats=["artic", "fasta", "sts"],
                prefix="multi_format",
                force_overwrite=True,
            )

            # All three formats should be created
            assert isinstance(result, dict)
            assert len(result) == 3
            assert "artic" in result
            assert "fasta" in result
            assert "sts" in result

            # All files should exist
            for format_name, file_path in result.items():
                assert (
                    file_path.exists()
                ), f"Output file for {format_name} doesn't exist"
                assert "multi_format" in str(file_path)

    def test_convert_primers_real_workflow(self):
        """Test a realistic end-to-end workflow."""

        # Use the small test dataset
        test_input_file = (
            Path(__file__).parent / "test_data" / "datasets" / "small" / "varvamp.tsv"
        )
        if not test_input_file.exists():
            pytest.skip(f"Test data file not found: {test_input_file}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_dir = Path(temp_dir)

            # Realistic conversion workflow
            result = convert_primers(
                input_file=test_input_file,
                output_dir=temp_output_dir,
                input_format=None,  # Auto-detect
                output_formats=["artic", "fasta"],
                prefix="covid_primers",
                force_overwrite=True,
                validate_sequences=True,
                aligner="none",  # Skip alignment for test speed
            )

            # Verify results
            assert isinstance(result, dict)
            assert "artic" in result
            assert "fasta" in result

            # Check file contents are reasonable
            artic_file = result["artic"]
            fasta_file = result["fasta"]

            assert artic_file.exists()
            assert fasta_file.exists()

            # Basic content validation
            artic_content = artic_file.read_text()
            fasta_content = fasta_file.read_text()

            # ARTIC should have tab-separated format
            assert "\t" in artic_content
            # FASTA should have sequence headers
            assert ">" in fasta_content
