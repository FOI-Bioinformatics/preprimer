"""
Comprehensive tests for the CLI module.

Tests all CLI functions, argument parsing, command routing, and error handling
to achieve complete coverage of the CLI module.
"""

import argparse
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from preprimer.cli import (
    cmd_convert,
    cmd_info,
    cmd_list,
    create_parser,
    main,
    setup_logging,
)
from preprimer.core.config import PrePrimerConfig
from preprimer.core.exceptions import PrePrimerError


class TestSetupLogging:
    """Test logging setup functionality."""

    @patch('preprimer.cli.logging.basicConfig')
    def test_setup_logging_default(self, mock_basic_config):
        """Test default logging setup."""
        setup_logging()
        
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @patch('preprimer.cli.logging.basicConfig')
    def test_setup_logging_debug(self, mock_basic_config):
        """Test DEBUG logging setup."""
        setup_logging("DEBUG")
        
        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @patch('preprimer.cli.logging.basicConfig')
    def test_setup_logging_warning(self, mock_basic_config):
        """Test WARNING logging setup."""
        setup_logging("WARNING")
        
        mock_basic_config.assert_called_once_with(
            level=logging.WARNING,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @patch('preprimer.cli.logging.basicConfig')
    def test_setup_logging_error(self, mock_basic_config):
        """Test ERROR logging setup."""
        setup_logging("ERROR")
        
        mock_basic_config.assert_called_once_with(
            level=logging.ERROR,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    @patch('preprimer.cli.logging.basicConfig')
    def test_setup_logging_invalid_level(self, mock_basic_config):
        """Test logging setup with invalid level defaults to INFO."""
        setup_logging("INVALID")
        
        mock_basic_config.assert_called_once_with(
            level=logging.INFO,  # Should default to INFO
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class TestCreateParser:
    """Test argument parser creation."""

    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert "PrePrimer" in parser.description
        assert parser._option_string_actions["--version"].version == "PrePrimer 0.2.0"

    def test_parser_version_argument(self):
        """Test version argument."""
        parser = create_parser()
        
        # Test that version argument exists and has correct value
        version_action = parser._option_string_actions.get("--version")
        assert version_action is not None
        assert version_action.version == "PrePrimer 0.2.0"

    def test_parser_log_level_argument(self):
        """Test log-level argument."""
        parser = create_parser()
        
        log_level_action = parser._option_string_actions.get("--log-level")
        assert log_level_action is not None
        assert log_level_action.choices == ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert log_level_action.default == "INFO"

    def test_parser_config_argument(self):
        """Test config argument."""
        parser = create_parser()
        
        config_action = parser._option_string_actions.get("--config")
        assert config_action is not None
        assert config_action.type == Path

    def test_parser_subcommands_exist(self):
        """Test that all expected subcommands exist."""
        parser = create_parser()
        
        # Get subparser actions
        subparsers_actions = [
            action for action in parser._actions 
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert len(subparsers_actions) == 1
        
        subparser_choices = subparsers_actions[0].choices
        assert "convert" in subparser_choices
        assert "list" in subparser_choices
        assert "info" in subparser_choices

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.writer_registry')
    def test_parser_convert_subcommand(self, mock_writer_reg, mock_parser_reg):
        """Test convert subcommand arguments."""
        mock_parser_reg.list_formats.return_value = ["artic", "varvamp"]
        mock_writer_reg.list_formats.return_value = ["artic", "fasta", "sts"]
        
        parser = create_parser()
        
        # Parse convert command with required arguments
        args = parser.parse_args([
            "convert", 
            "--input", "test.bed", 
            "--output-dir", "output/"
        ])
        
        assert args.command == "convert"
        assert args.input == Path("test.bed")
        assert args.output_dir == Path("output/")
        assert args.output_formats == ["artic"]  # default
        assert args.prefix == "primers"  # default
        assert args.force is False  # default
        assert args.validate_only is False  # default

    def test_parser_list_subcommand(self):
        """Test list subcommand arguments."""
        parser = create_parser()
        
        # Test list with --parsers
        args = parser.parse_args(["list", "--parsers"])
        assert args.command == "list"
        assert args.parsers is True
        assert args.writers is False
        assert args.all is False

        # Test list with --writers  
        args = parser.parse_args(["list", "--writers"])
        assert args.command == "list"
        assert args.parsers is False
        assert args.writers is True
        assert args.all is False

        # Test list with --all
        args = parser.parse_args(["list", "--all"])
        assert args.command == "list"
        assert args.parsers is False
        assert args.writers is False
        assert args.all is True

    def test_parser_info_subcommand(self):
        """Test info subcommand arguments."""
        parser = create_parser()
        
        args = parser.parse_args(["info", "test.bed"])
        
        assert args.command == "info"
        assert args.file == Path("test.bed")


class TestCmdConvert:
    """Test convert command handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PrePrimerConfig()
        self.mock_args = Mock()
        self.mock_args.force = False
        self.mock_args.validate_only = False
        self.mock_args.input_format = None
        self.mock_args.input = Path("test.bed")
        self.mock_args.output_dir = Path("output/")
        self.mock_args.output_formats = ["artic"]
        self.mock_args.prefix = "test"
        self.mock_args.reference = None

    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_success(self, mock_converter_class):
        """Test successful conversion."""
        mock_converter = mock_converter_class.return_value
        mock_converter.convert.return_value = {"artic": Path("output/artic.bed")}
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 0
        mock_converter.convert.assert_called_once()
        mock_logger.info.assert_called()

    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_with_force(self, mock_converter_class):
        """Test conversion with force flag."""
        self.mock_args.force = True
        mock_converter = mock_converter_class.return_value
        mock_converter.convert.return_value = {"artic": Path("output/artic.bed")}
        
        result = cmd_convert(self.mock_args, self.config)
        
        assert result == 0
        assert self.config.force_overwrite is True

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_validate_only_with_format(self, mock_converter_class, mock_registry):
        """Test validation-only mode with specified input format."""
        self.mock_args.validate_only = True
        self.mock_args.input_format = "artic"
        
        # Create realistic mock primers with direction attribute
        mock_primer1 = Mock()
        mock_primer1.direction = "forward"
        mock_primer2 = Mock()
        mock_primer2.direction = "reverse"
        
        # Create realistic mock amplicons with primers property
        mock_amplicon1 = Mock()
        mock_amplicon1.amplicon_id = "amplicon_1"
        mock_amplicon1.primers = [mock_primer1, mock_primer2]
        mock_amplicon1.forward_primers = [mock_primer1]
        mock_amplicon1.reverse_primers = [mock_primer2]
        
        mock_amplicon2 = Mock()
        mock_amplicon2.amplicon_id = "amplicon_2"
        mock_amplicon2.primers = [mock_primer1, mock_primer2]
        mock_amplicon2.forward_primers = [mock_primer1]
        mock_amplicon2.reverse_primers = [mock_primer2]
        
        mock_amplicons = [mock_amplicon1, mock_amplicon2]
        
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_amplicons
        mock_registry.get_parser.return_value = mock_parser
        
        mock_converter = mock_converter_class.return_value
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 0
        mock_parser.parse.assert_called_once_with(self.mock_args.input, self.mock_args.prefix)
        mock_converter._validate_amplicons.assert_called_once_with(mock_amplicons)
        mock_logger.info.assert_called()

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_validate_only_auto_detect(self, mock_converter_class, mock_registry):
        """Test validation-only mode with auto-detection."""
        self.mock_args.validate_only = True
        self.mock_args.input_format = None
        
        # Create realistic mock primers with direction attribute
        mock_primer1 = Mock()
        mock_primer1.direction = "forward"
        mock_primer2 = Mock()
        mock_primer2.direction = "reverse"
        
        # Create realistic mock amplicons with primers property
        mock_amplicon1 = Mock()
        mock_amplicon1.amplicon_id = "amplicon_1"
        mock_amplicon1.primers = [mock_primer1, mock_primer2]
        mock_amplicon1.forward_primers = [mock_primer1]
        mock_amplicon1.reverse_primers = [mock_primer2]
        
        mock_amplicon2 = Mock()
        mock_amplicon2.amplicon_id = "amplicon_2"
        mock_amplicon2.primers = [mock_primer1, mock_primer2]
        mock_amplicon2.forward_primers = [mock_primer1]
        mock_amplicon2.reverse_primers = [mock_primer2]
        
        mock_amplicons = [mock_amplicon1, mock_amplicon2]
        
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_amplicons
        mock_registry.get_parser.return_value = mock_parser
        mock_registry.detect_format.return_value = "artic"
        
        mock_converter = mock_converter_class.return_value
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 0
        mock_registry.detect_format.assert_called_once_with(self.mock_args.input)
        mock_registry.get_parser.assert_called_with("artic")

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_validate_only_unknown_format(self, mock_converter_class, mock_registry):
        """Test validation-only mode with unknown format."""
        self.mock_args.validate_only = True
        self.mock_args.input_format = None
        
        mock_registry.detect_format.return_value = None
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 1
        mock_logger.error.assert_called_with("Could not detect input format")

    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_preprimer_error(self, mock_converter_class):
        """Test handling of PrePrimerError."""
        mock_converter = mock_converter_class.return_value
        mock_converter.convert.side_effect = PrePrimerError("Test error")
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 1
        mock_logger.error.assert_called_with("❌ Test error")

    @patch('preprimer.cli.PrimerConverter')
    def test_cmd_convert_unexpected_error(self, mock_converter_class):
        """Test handling of unexpected exceptions."""
        mock_converter = mock_converter_class.return_value
        mock_converter.convert.side_effect = ValueError("Unexpected error")
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_convert(self.mock_args, self.config)
        
        assert result == 1
        mock_logger.error.assert_any_call("❌ Unexpected error: Unexpected error")
        mock_logger.debug.assert_called_with("Full traceback:", exc_info=True)


class TestCmdList:
    """Test list command handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_args = Mock()
        self.mock_args.parsers = False
        self.mock_args.writers = False  
        self.mock_args.all = False

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.writer_registry')
    def test_cmd_list_parsers_only(self, mock_writer_reg, mock_parser_reg):
        """Test listing parsers only."""
        self.mock_args.parsers = True
        
        mock_parser_reg.list_formats.return_value = ["artic", "varvamp"]
        mock_parser_reg.list_extensions.side_effect = [
            [".bed"], [".tsv"]
        ]
        
        with patch('builtins.print') as mock_print:
            result = cmd_list(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call("📥 Available input formats:")
        mock_print.assert_any_call("  artic: .bed")
        mock_print.assert_any_call("  varvamp: .tsv")

    @patch('preprimer.cli.parser_registry')  
    @patch('preprimer.cli.writer_registry')
    def test_cmd_list_writers_only(self, mock_writer_reg, mock_parser_reg):
        """Test listing writers only."""
        self.mock_args.writers = True
        
        mock_writer_reg.list_formats.return_value = ["artic", "fasta"]
        mock_writer1 = Mock()
        mock_writer1.file_extension = ".bed"
        mock_writer2 = Mock()
        mock_writer2.file_extension = ".fasta"
        mock_writer_reg.get_writer.side_effect = [mock_writer1, mock_writer2]
        
        with patch('builtins.print') as mock_print:
            result = cmd_list(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call("📤 Available output formats:")
        mock_print.assert_any_call("  artic: .bed")
        mock_print.assert_any_call("  fasta: .fasta")

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.writer_registry')
    def test_cmd_list_all(self, mock_writer_reg, mock_parser_reg):
        """Test listing all formats."""
        self.mock_args.all = True
        
        # Setup mocks
        mock_parser_reg.list_formats.return_value = ["artic"]
        mock_parser_reg.list_extensions.return_value = [".bed"]
        mock_writer_reg.list_formats.return_value = ["fasta"]
        mock_writer = Mock()
        mock_writer.file_extension = ".fasta"
        mock_writer_reg.get_writer.return_value = mock_writer
        
        with patch('builtins.print') as mock_print:
            result = cmd_list(self.mock_args)
        
        assert result == 0
        # Should show both parsers and writers
        mock_print.assert_any_call("📥 Available input formats:")
        mock_print.assert_any_call("📤 Available output formats:")

    @patch('preprimer.cli.cmd_list')
    def test_cmd_list_default_shows_all(self, mock_cmd_list_recursive):
        """Test that default behavior shows all formats."""
        # First call returns the mock_args, second call should be the recursive call
        mock_cmd_list_recursive.side_effect = [0, 0]  # Return success on recursive call
        
        result = cmd_list(self.mock_args)
        
        assert result == 0
        # Should make recursive call with parsers=True, writers=True, all=False
        expected_args = argparse.Namespace(parsers=True, writers=True, all=False)
        mock_cmd_list_recursive.assert_called_with(expected_args)


class TestCmdInfo:
    """Test info command handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_args = Mock()

    @patch('preprimer.cli.parser_registry')
    def test_cmd_info_file_not_found(self, mock_registry):
        """Test info command with non-existent file."""
        mock_file = Mock()
        mock_file.exists.return_value = False
        self.mock_args.file = mock_file
        
        with patch('preprimer.cli.logger') as mock_logger:
            result = cmd_info(self.mock_args)
        
        assert result == 1
        mock_logger.error.assert_called_with(f"File not found: {mock_file}")

    @patch('preprimer.cli.parser_registry')
    def test_cmd_info_unknown_format(self, mock_registry):
        """Test info command with unknown format."""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 1024
        self.mock_args.file = mock_file
        
        mock_registry.detect_format.return_value = None
        mock_registry.list_formats.return_value = ["artic", "varvamp"]
        
        with patch('builtins.print') as mock_print:
            result = cmd_info(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call(f"📁 File: {mock_file}")
        mock_print.assert_any_call("📏 Size: 1,024 bytes")
        mock_print.assert_any_call("❓ Format: Unknown/unsupported")
        mock_print.assert_any_call("   Supported formats: artic, varvamp")

    @patch('preprimer.cli.parser_registry')
    def test_cmd_info_successful_parsing(self, mock_registry):
        """Test info command with successful file parsing."""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 2048
        self.mock_args.file = mock_file
        
        # Mock amplicon data
        mock_amplicon1 = Mock()
        mock_amplicon1.amplicon_id = "amplicon_1"
        mock_amplicon1.primers = [Mock(), Mock(), Mock()]  # 3 primers
        mock_amplicon1.forward_primers = [Mock(), Mock()]  # 2 forward
        mock_amplicon1.reverse_primers = [Mock()]  # 1 reverse
        
        mock_amplicon2 = Mock()
        mock_amplicon2.amplicon_id = "amplicon_2"
        mock_amplicon2.primers = [Mock(), Mock()]  # 2 primers
        mock_amplicon2.forward_primers = [Mock()]  # 1 forward
        mock_amplicon2.reverse_primers = [Mock()]  # 1 reverse
        
        mock_amplicons = [mock_amplicon1, mock_amplicon2]
        
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_amplicons
        
        mock_registry.detect_format.return_value = "artic"
        mock_registry.get_parser.return_value = mock_parser
        
        with patch('builtins.print') as mock_print:
            result = cmd_info(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call(f"📁 File: {mock_file}")
        mock_print.assert_any_call("📏 Size: 2,048 bytes")
        mock_print.assert_any_call("🔍 Detected format: artic")
        mock_print.assert_any_call("🧬 Amplicons: 2")
        mock_print.assert_any_call("🔬 Primers: 5")  # Total: 3 + 2 = 5
        mock_print.assert_any_call("\n📊 Amplicon details:")
        mock_print.assert_any_call("  amplicon_1: 2F + 1R")
        mock_print.assert_any_call("  amplicon_2: 1F + 1R")

    @patch('preprimer.cli.parser_registry')
    def test_cmd_info_parsing_error(self, mock_registry):
        """Test info command when parsing fails."""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 512
        self.mock_args.file = mock_file
        
        mock_parser = Mock()
        mock_parser.parse.side_effect = ValueError("Parsing failed")
        
        mock_registry.detect_format.return_value = "artic"
        mock_registry.get_parser.return_value = mock_parser
        
        with patch('builtins.print') as mock_print:
            result = cmd_info(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call(f"📁 File: {mock_file}")
        mock_print.assert_any_call("🔍 Detected format: artic")
        mock_print.assert_any_call("⚠️  Could not parse file: Parsing failed")

    @patch('preprimer.cli.parser_registry')
    def test_cmd_info_many_amplicons(self, mock_registry):
        """Test info command with many amplicons (> 5)."""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 4096
        self.mock_args.file = mock_file
        
        # Create 8 mock amplicons
        mock_amplicons = []
        for i in range(8):
            mock_amplicon = Mock()
            mock_amplicon.amplicon_id = f"amplicon_{i}"
            mock_amplicon.primers = [Mock(), Mock()]  # 2 primers each
            mock_amplicon.forward_primers = [Mock()]  # 1 forward each
            mock_amplicon.reverse_primers = [Mock()]  # 1 reverse each
            mock_amplicons.append(mock_amplicon)
        
        mock_parser = Mock()
        mock_parser.parse.return_value = mock_amplicons
        
        mock_registry.detect_format.return_value = "varvamp"
        mock_registry.get_parser.return_value = mock_parser
        
        with patch('builtins.print') as mock_print:
            result = cmd_info(self.mock_args)
        
        assert result == 0
        mock_print.assert_any_call("🧬 Amplicons: 8")
        mock_print.assert_any_call("🔬 Primers: 16")  # 8 amplicons * 2 primers each
        # Should show "... and 3 more amplicons" (8 - 5 = 3)
        mock_print.assert_any_call("  ... and 3 more amplicons")


class TestMain:
    """Test main entry point function."""

    def test_main_no_arguments(self):
        """Test main with no arguments shows help."""
        test_argv = ["preprimer"]
        
        with patch.object(sys, 'argv', test_argv):
            with patch('preprimer.cli.create_parser') as mock_create_parser:
                mock_parser = Mock()
                mock_create_parser.return_value = mock_parser
                
                result = main()
                
                assert result == 0
                mock_parser.print_help.assert_called_once()

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    @patch('preprimer.cli.cmd_convert')
    def test_main_convert_command(self, mock_cmd_convert, mock_config_class, mock_setup_logging):
        """Test main with convert command."""
        test_argv = ["preprimer", "convert", "--input", "test.bed", "--output-dir", "out/"]
        
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_cmd_convert.return_value = 0
        
        with patch.object(sys, 'argv', test_argv):
            result = main()
        
        assert result == 0
        mock_setup_logging.assert_called_once_with("INFO")
        mock_cmd_convert.assert_called_once()

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    @patch('preprimer.cli.cmd_list')
    def test_main_list_command(self, mock_cmd_list, mock_config_class, mock_setup_logging):
        """Test main with list command."""
        test_argv = ["preprimer", "list", "--parsers"]
        
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_cmd_list.return_value = 0
        
        with patch.object(sys, 'argv', test_argv):
            result = main()
        
        assert result == 0
        mock_setup_logging.assert_called_once_with("INFO")
        mock_cmd_list.assert_called_once()

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    @patch('preprimer.cli.cmd_info')
    def test_main_info_command(self, mock_cmd_info, mock_config_class, mock_setup_logging):
        """Test main with info command."""
        test_argv = ["preprimer", "info", "test.bed"]
        
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_cmd_info.return_value = 0
        
        with patch.object(sys, 'argv', test_argv):
            result = main()
        
        assert result == 0
        mock_setup_logging.assert_called_once_with("INFO")
        mock_cmd_info.assert_called_once()

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    def test_main_with_config_file(self, mock_config_class, mock_setup_logging):
        """Test main with custom config file."""
        test_argv = ["preprimer", "--config", "config.json", "list"]
        
        mock_config = Mock()
        mock_config_class.from_file.return_value = mock_config
        
        with patch.object(sys, 'argv', test_argv):
            with patch('preprimer.cli.cmd_list') as mock_cmd_list:
                with patch('preprimer.cli.logger') as mock_logger:
                    mock_cmd_list.return_value = 0
                    
                    result = main()
        
        assert result == 0
        mock_config_class.from_file.assert_called_once_with(Path("config.json"))

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    def test_main_config_error(self, mock_config_class, mock_setup_logging):
        """Test main with configuration error."""
        test_argv = ["preprimer", "--config", "bad_config.json", "list"]
        
        mock_config_class.from_file.side_effect = ValueError("Bad config")
        
        with patch.object(sys, 'argv', test_argv):
            with patch('preprimer.cli.logger') as mock_logger:
                result = main()
        
        assert result == 1
        mock_logger.error.assert_called_with("Configuration error: Bad config")

    @patch('preprimer.cli.setup_logging')
    @patch('preprimer.cli.PrePrimerConfig')
    def test_main_custom_log_level(self, mock_config_class, mock_setup_logging):
        """Test main with custom log level."""
        test_argv = ["preprimer", "--log-level", "DEBUG", "list"]
        
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        with patch.object(sys, 'argv', test_argv):
            with patch('preprimer.cli.cmd_list') as mock_cmd_list:
                mock_cmd_list.return_value = 0
                result = main()
        
        assert result == 0
        mock_setup_logging.assert_called_once_with("DEBUG")

    def test_main_unknown_command(self):
        """Test main with no recognized command shows help."""
        test_argv = ["preprimer", "unknown"]
        
        with patch.object(sys, 'argv', test_argv):
            with patch('preprimer.cli.create_parser') as mock_create_parser:
                mock_parser = Mock()
                mock_parser.parse_args.return_value = Mock(command=None)
                mock_create_parser.return_value = mock_parser
                
                with patch('preprimer.cli.setup_logging'):
                    with patch('preprimer.cli.PrePrimerConfig'):
                        result = main()
                
                assert result == 0
                mock_parser.print_help.assert_called_once()


class TestCliIntegration:
    """Integration tests for CLI functionality."""

    @patch('preprimer.cli.parser_registry')
    @patch('preprimer.cli.writer_registry')
    def test_full_convert_workflow(self, mock_writer_reg, mock_parser_reg):
        """Test complete convert workflow integration."""
        # Setup registry mocks
        mock_parser_reg.list_formats.return_value = ["artic", "varvamp"]
        mock_writer_reg.list_formats.return_value = ["artic", "fasta"]
        
        # Create parser and test convert command parsing
        parser = create_parser()
        args = parser.parse_args([
            "convert",
            "--input", "test.bed",
            "--output-dir", "output/",
            "--input-format", "artic",
            "--output-formats", "fasta", "artic",
            "--prefix", "test_scheme",
            "--force"
        ])
        
        assert args.command == "convert"
        assert args.input == Path("test.bed")
        assert args.output_dir == Path("output/")
        assert args.input_format == "artic"
        assert args.output_formats == ["fasta", "artic"]
        assert args.prefix == "test_scheme"
        assert args.force is True

    def test_full_list_workflow(self):
        """Test complete list workflow integration."""
        parser = create_parser()
        
        # Test different list combinations
        args_parsers = parser.parse_args(["list", "--parsers"])
        assert args_parsers.parsers is True
        
        args_writers = parser.parse_args(["list", "--writers"])
        assert args_writers.writers is True
        
        args_all = parser.parse_args(["list", "--all"])
        assert args_all.all is True

    def test_full_info_workflow(self):
        """Test complete info workflow integration."""
        parser = create_parser()
        args = parser.parse_args(["info", "test.bed"])
        
        assert args.command == "info"
        assert args.file == Path("test.bed")