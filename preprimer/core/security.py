"""
Security utilities for PrePrimer.

This module provides security-focused utilities for safe file operations,
path validation, and input sanitization to prevent common security vulnerabilities
such as path traversal attacks and command injection.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Set, Union

from .exceptions import SecurityError


class PathValidator:
    """
    Provides secure path validation and sanitization utilities.

    This class implements defense against path traversal attacks and ensures
    that file operations remain within designated safe directories.
    """

    # Characters that are never allowed in filenames across platforms
    FORBIDDEN_CHARS: Set[str] = {
        "\x00",
        "<",
        ">",
        ":",
        '"',
        "|",
        "?",
        "*",
        "\x01",
        "\x02",
        "\x03",
        "\x04",
        "\x05",
        "\x06",
        "\x07",
        "\x08",
        "\x09",
        "\x0a",
        "\x0b",
        "\x0c",
        "\x0d",
        "\x0e",
        "\x0f",
        "\x10",
        "\x11",
        "\x12",
        "\x13",
        "\x14",
        "\x15",
        "\x16",
        "\x17",
        "\x18",
        "\x19",
        "\x1a",
        "\x1b",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x1f",
    }

    # Reserved names on Windows
    RESERVED_NAMES: Set[str] = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    @classmethod
    def validate_filename(cls, filename: str) -> None:
        """
        Validate that a filename is safe for use across platforms.

        Args:
            filename: The filename to validate

        Raises:
            SecurityError: If the filename contains unsafe characters or patterns
        """
        if not filename or filename.isspace():
            raise SecurityError("Filename cannot be empty or contain only whitespace")

        # Check for forbidden characters
        forbidden_found = cls.FORBIDDEN_CHARS.intersection(set(filename))
        if forbidden_found:
            raise SecurityError(
                f"Filename contains forbidden characters: {sorted(forbidden_found)}"
            )

        # Check for reserved names (case-insensitive)
        name_upper = filename.upper()
        if name_upper in cls.RESERVED_NAMES:
            raise SecurityError(f"Filename uses reserved name: {filename}")

        # Check for names that end with reserved names (Windows behavior)
        for reserved in cls.RESERVED_NAMES:
            if name_upper.startswith(reserved + "."):
                raise SecurityError(f"Filename uses reserved name: {filename}")

        # Check length constraints
        if len(filename.encode("utf-8")) > 255:
            raise SecurityError("Filename too long (>255 bytes in UTF-8)")

        # Check for leading/trailing periods or spaces (problematic on Windows)
        if filename.startswith(".") and filename.count(".") == len(filename):
            raise SecurityError("Filename cannot consist only of periods")

        if filename.endswith(" ") or filename.endswith("."):
            raise SecurityError("Filename cannot end with space or period")

    @classmethod
    def validate_path_components(cls, path: Union[str, Path]) -> None:
        """
        Validate all components of a path for security issues.

        Args:
            path: The path to validate

        Raises:
            SecurityError: If any path component is unsafe
        """
        path_obj = Path(path)

        for component in path_obj.parts:
            # Skip root components like '/' or 'C:\'
            if len(component) <= 3 and ":" in component:
                continue
            if component in ("/", "\\"):
                continue

            cls.validate_filename(component)

            # Additional checks for path traversal attempts
            if component in ("..", "."):
                raise SecurityError(f"Path traversal attempt detected: {component}")

    @classmethod
    def sanitize_path(
        cls, path: Union[str, Path], base_dir: Optional[Path] = None
    ) -> Path:
        """
        Sanitize and resolve a path to prevent directory traversal.

        Args:
            path: The path to sanitize
            base_dir: Optional base directory to restrict operations to

        Returns:
            A sanitized, resolved Path object

        Raises:
            SecurityError: If the path is unsafe or escapes the base directory
        """
        if not path:
            raise SecurityError("Path cannot be empty")

        # Convert to string for analysis
        path_str = str(path)

        # Block parent-directory traversal: ".." only when it stands as a full
        # path segment (adjacent to a separator or standing alone), covering
        # both POSIX "../" and Windows "..\" forms. Filenames that merely
        # contain a ".." substring (e.g. "sars..cov2.tsv") are allowed.
        if re.search(r"(^|[/\\])\.\.([/\\]|$)", path_str):
            raise SecurityError(f"Path traversal attempt detected: {path}")

        # Check for absolute paths to dangerous system directories when no base_dir is specified
        if base_dir is None:
            # Define dangerous system directories - be specific to avoid blocking legitimate temp dirs
            dangerous_dirs = [
                "/etc/",
                "/root/",
                "/bin/",
                "/sbin/",
                "/usr/bin/",
                "/usr/sbin/",
                "/boot/",
                "/dev/",
                "/proc/",
                "/sys/",
                "/var/mail/",
                "/var/log/",
                "/var/lib/",
                "/var/run/",
                "/var/spool/",
                "C:\\Windows\\System32\\",
                "C:\\Program Files\\",
                "C:\\Windows\\",
                "/home/root/",
                "/root/",
            ]

            # Allow legitimate temporary and user directories
            allowed_prefixes = [
                "/tmp/",
                "/var/tmp/",
                "/var/folders/",  # Common temp directories
                str(Path.home()),  # User home directory
            ]

            # Check if path is in an allowed temporary location
            is_allowed = any(
                path_str.startswith(allowed) for allowed in allowed_prefixes
            )

            if not is_allowed:
                # Check if path is in a dangerous directory
                for dangerous_dir in dangerous_dirs:
                    if path_str.startswith(dangerous_dir):
                        raise SecurityError(f"Access to system directory denied")

        # Convert to Path object and resolve
        try:
            path_obj = Path(path).expanduser()

            # Validate path components
            cls.validate_path_components(path_obj)

            # Resolve the path (this will resolve .. and . components)
            resolved_path = path_obj.resolve()

            # If base_dir is specified, ensure the path is within it
            if base_dir is not None:
                base_resolved = base_dir.resolve()
                try:
                    resolved_path.relative_to(base_resolved)
                except ValueError:
                    raise SecurityError(f"Path escapes base directory")

            return resolved_path

        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid path: {e}") from e

    @classmethod
    def is_safe_to_write(
        cls, path: Union[str, Path], base_dir: Optional[Path] = None
    ) -> bool:
        """
        Check if it's safe to write to the given path.

        Args:
            path: The path to check
            base_dir: Optional base directory to restrict operations to

        Returns:
            True if the path is safe to write to, False otherwise
        """
        try:
            sanitized_path = cls.sanitize_path(path, base_dir)

            # Additional checks for write safety
            if sanitized_path.is_dir():
                return False  # Don't write to directories

            # Check if parent directory exists or can be created
            parent_dir = sanitized_path.parent
            if not parent_dir.exists():
                # Verify we can create the parent directory safely
                cls.sanitize_path(parent_dir, base_dir)

            return True

        except SecurityError:
            return False

    # Default 100 MB cap, mirrors SecuritySettings.max_file_size.
    DEFAULT_MAX_FILE_SIZE: int = 100 * 1024 * 1024

    @classmethod
    def validate_file_size(
        cls, path: Union[str, Path], max_bytes: Optional[int] = None
    ) -> None:
        """
        Ensure a file does not exceed the maximum allowed size.

        Args:
            path: Path to the file to check.
            max_bytes: Maximum allowed size in bytes (defaults to
                ``DEFAULT_MAX_FILE_SIZE``).

        Raises:
            SecurityError: If the file is missing or exceeds the size limit.
        """
        if max_bytes is None:
            max_bytes = cls.DEFAULT_MAX_FILE_SIZE

        file_path = Path(path)
        try:
            size = file_path.stat().st_size
        except OSError as e:
            raise SecurityError(f"Cannot stat file '{file_path}': {e}") from e

        if size > max_bytes:
            raise SecurityError(
                f"File too large: {size} bytes exceeds limit of {max_bytes} bytes"
            )

    @classmethod
    def validate_output_directory(
        cls, directory: Union[str, Path], base_dir: Optional[Path] = None
    ) -> Path:
        """
        Validate (and sanitize) a directory intended for writing output.

        Args:
            directory: Directory path to validate.
            base_dir: Optional base directory to restrict operations to.

        Returns:
            The sanitized directory path.

        Raises:
            SecurityError: If the path is unsafe or points at an existing
                non-directory.
        """
        dir_path = cls.sanitize_path(directory, base_dir)

        if dir_path.exists() and not dir_path.is_dir():
            raise SecurityError(
                f"Output path exists and is not a directory: {dir_path}"
            )

        return dir_path


class SecureFileOperations:
    """
    Provides secure file operations with built-in path validation.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize secure file operations.

        Args:
            base_dir: Optional base directory to restrict all operations to
        """
        self.base_dir = base_dir.resolve() if base_dir else None
        self.validator = PathValidator()

    def safe_remove_tree(self, directory: Union[str, Path]) -> None:
        """
        Safely remove a directory tree with path validation.

        Args:
            directory: Directory to remove

        Raises:
            SecurityError: If the path is unsafe or escapes the base directory
        """
        dir_path = self.validator.sanitize_path(directory, self.base_dir)

        if not dir_path.exists():
            return  # Nothing to remove

        if not dir_path.is_dir():
            raise SecurityError(f"Path is not a directory: {dir_path}")

        # Additional safety check: ensure we're not removing system directories
        if self._is_system_directory(dir_path):
            raise SecurityError(f"Refusing to remove system directory: {dir_path}")

        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            raise SecurityError(f"Failed to remove directory '{dir_path}': {e}") from e

    def safe_create_directories(
        self, directory: Union[str, Path], mode: int = 0o755
    ) -> Path:
        """
        Safely create directories with path validation.

        Args:
            directory: Directory path to create
            mode: Directory permissions (default: 755)

        Returns:
            The created directory path

        Raises:
            SecurityError: If the path is unsafe
        """
        dir_path = self.validator.sanitize_path(directory, self.base_dir)

        try:
            dir_path.mkdir(parents=True, exist_ok=True, mode=mode)
            return dir_path
        except OSError as e:
            raise SecurityError(f"Failed to create directory '{dir_path}': {e}") from e

    def safe_open_file(self, file_path: Union[str, Path], mode: str = "r", **kwargs):
        """
        Safely open a file with path validation.

        Args:
            file_path: Path to the file
            mode: File open mode
            **kwargs: Additional arguments passed to open()

        Returns:
            File object

        Raises:
            SecurityError: If the path is unsafe
        """
        validated_path = self.validator.sanitize_path(file_path, self.base_dir)

        # For write modes, ensure parent directory exists
        if "w" in mode or "a" in mode:
            parent_dir = validated_path.parent
            if not parent_dir.exists():
                self.safe_create_directories(parent_dir)

        try:
            return open(validated_path, mode, **kwargs)
        except OSError as e:
            raise SecurityError(f"Failed to open file '{validated_path}': {e}") from e

    def _is_system_directory(self, path: Path) -> bool:
        """
        Check if a path points to a system directory that should not be removed.

        Args:
            path: Path to check

        Returns:
            True if the path is a system directory
        """
        # Convert to string for easier comparison
        path_str = str(path.resolve()).lower()

        # Common system directories to protect
        system_paths = {
            "/",
            "/bin",
            "/boot",
            "/dev",
            "/etc",
            "/lib",
            "/lib64",
            "/proc",
            "/root",
            "/sbin",
            "/sys",
            "/usr",
            "/var",
            "c:\\windows",
            "c:\\program files",
            "c:\\program files (x86)",
            "c:\\users\\default",
            "/system",
            "/applications",
        }

        # Check if path is or starts with any system path
        for sys_path in system_paths:
            if path_str == sys_path or path_str.startswith(sys_path + os.sep):
                return True

        # Check for common user directories that should be protected
        if any(part in path_str for part in ["/home", "/users", "documents"]):
            # Allow removal only if it's clearly within a temporary or project directory
            safe_patterns = ["temp", "tmp", "cache", "preprimer", "test"]
            if not any(pattern in path_str for pattern in safe_patterns):
                return True

        return False


class InputValidator:
    """
    Validates and sanitizes various types of user input.
    """

    # Pattern for valid primer sequences (IUPAC nucleotide codes)
    PRIMER_SEQUENCE_PATTERN = re.compile(r"^[ATCGRYSWKMBDHVNatcgryswkmbdhvn]+$")

    @classmethod
    def validate_primer_sequence(cls, sequence: str) -> None:
        """
        Validate a primer sequence contains only valid nucleotide characters.

        Args:
            sequence: The primer sequence to validate

        Raises:
            SecurityError: If the sequence contains invalid characters
        """
        if not sequence:
            raise SecurityError("Primer sequence cannot be empty")

        if not cls.PRIMER_SEQUENCE_PATTERN.match(sequence):
            invalid_chars = set(sequence) - set("ATCGRYSWKMBDHVNatcgryswkmbdhvn")
            raise SecurityError(
                f"Primer sequence contains invalid characters: {sorted(invalid_chars)}"
            )

        if len(sequence) > 1000:  # Reasonable upper limit
            raise SecurityError("Primer sequence is unreasonably long (>1000 bp)")

    @classmethod
    def validate_amplicon_name(cls, name: str) -> None:
        """
        Validate an amplicon name for safety.

        Args:
            name: The amplicon name to validate

        Raises:
            SecurityError: If the name is unsafe
        """
        if not name or name.isspace():
            raise SecurityError("Amplicon name cannot be empty")

        # Check for reasonable length
        if len(name) > 200:
            raise SecurityError("Amplicon name is too long (>200 characters)")

        # Check for potentially dangerous characters
        dangerous_chars = set(name) & {"<", ">", "&", '"', "'", "`", "$", ";", "|"}
        if dangerous_chars:
            raise SecurityError(
                f"Amplicon name contains potentially dangerous characters: {sorted(dangerous_chars)}"
            )

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string by removing or escaping dangerous characters.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            SecurityError: If the string cannot be safely sanitized
        """
        if not isinstance(value, str):
            raise SecurityError("Value must be a string")

        if len(value) > max_length:
            raise SecurityError(f"String too long (>{max_length} characters)")

        # Remove control characters except newline and tab
        sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")

        return sanitized.strip()


def secure_subprocess_call(
    command: List[str], cwd: Optional[Path] = None, timeout: int = 300
) -> subprocess.CompletedProcess:
    """
    Execute a subprocess with security constraints.

    Args:
        command: Command and arguments as a list
        cwd: Working directory for the subprocess
        timeout: Maximum execution time in seconds

    Returns:
        CompletedProcess object

    Raises:
        SecurityError: If the command or arguments are unsafe
    """
    if not command or not isinstance(command, list):
        raise SecurityError("Command must be a non-empty list")

    # Validate command components
    for i, arg in enumerate(command):
        if not isinstance(arg, str):
            raise SecurityError(f"Command argument {i} must be a string")

        # Check for command injection attempts
        dangerous_chars = {";", "&", "|", "`", "$", "<", ">", '"', "'"}
        if any(char in arg for char in dangerous_chars):
            raise SecurityError(
                f"Command argument contains dangerous characters: {arg}"
            )

    # Validate working directory
    if cwd is not None:
        cwd = PathValidator.sanitize_path(cwd)

    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Let caller handle return codes
        )
    except subprocess.TimeoutExpired as e:
        raise SecurityError(f"Command timed out after {timeout}s") from e
    except OSError as e:
        raise SecurityError(f"Failed to execute command: {e}") from e
