"""
Supplementary security tests covering edge branches not exercised by
test_security.py: file-size / output-directory validators, is_safe_to_write,
system-directory detection, amplicon-name validation, and secure subprocess
execution.
"""

import sys
from pathlib import Path

import pytest

from preprimer.core.exceptions import SecurityError
from preprimer.core.security import (
    InputValidator,
    PathValidator,
    SecureFileOperations,
    secure_subprocess_call,
)

# --- validate_file_size / validate_output_directory ------------------------


def test_validate_file_size_default_cap_allows_small(tmp_path):
    f = tmp_path / "small.tsv"
    f.write_text("data")
    PathValidator.validate_file_size(f)  # default cap, no raise


def test_validate_file_size_missing_file_raises(tmp_path):
    with pytest.raises(SecurityError):
        PathValidator.validate_file_size(tmp_path / "absent.tsv", max_bytes=1000)


def test_validate_output_directory_returns_sanitized(tmp_path):
    target = tmp_path / "outdir"
    result = PathValidator.validate_output_directory(target)
    assert result == target.resolve()


def test_validate_output_directory_rejects_non_directory(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("x")
    with pytest.raises(SecurityError):
        PathValidator.validate_output_directory(f)


# --- is_safe_to_write ------------------------------------------------------


def test_is_safe_to_write_true_for_new_file(tmp_path):
    assert PathValidator.is_safe_to_write(tmp_path / "new.txt") is True


def test_is_safe_to_write_false_for_directory(tmp_path):
    assert PathValidator.is_safe_to_write(tmp_path) is False


def test_is_safe_to_write_false_for_traversal():
    assert PathValidator.is_safe_to_write("../../etc/passwd") is False


# --- SecureFileOperations --------------------------------------------------


def test_safe_remove_tree_roundtrip(tmp_path):
    ops = SecureFileOperations(base_dir=tmp_path)
    sub = tmp_path / "scratch"
    sub.mkdir()
    (sub / "f.txt").write_text("x")
    ops.safe_remove_tree(sub)
    assert not sub.exists()


def test_safe_remove_tree_missing_is_noop(tmp_path):
    ops = SecureFileOperations(base_dir=tmp_path)
    ops.safe_remove_tree(tmp_path / "nope")  # no raise


def test_safe_remove_tree_rejects_file(tmp_path):
    ops = SecureFileOperations(base_dir=tmp_path)
    f = tmp_path / "f.txt"
    f.write_text("x")
    with pytest.raises(SecurityError):
        ops.safe_remove_tree(f)


def test_safe_create_and_open(tmp_path):
    ops = SecureFileOperations(base_dir=tmp_path)
    nested = tmp_path / "a" / "b"
    ops.safe_create_directories(nested)
    assert nested.is_dir()
    with ops.safe_open_file(nested / "c" / "out.txt", "w") as fh:
        fh.write("hello")
    assert (nested / "c" / "out.txt").read_text() == "hello"


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/usr", True),  # exact system path
        ("/usr/bin", True),  # under a system path
        ("/private/tmp/scratch/cache", False),  # safe pattern, not a system dir
    ],
)
def test_is_system_directory(path, expected):
    # Note: paths that are symlinks (e.g. /etc -> /private/etc on macOS) are
    # intentionally excluded as they resolve out of the system-paths set.
    ops = SecureFileOperations()
    assert ops._is_system_directory(Path(path)) is expected


# --- InputValidator.validate_amplicon_name ---------------------------------


def test_validate_amplicon_name_ok():
    InputValidator.validate_amplicon_name("SARS_CoV_2_400")  # no raise


@pytest.mark.parametrize("bad", ["", "   ", "a" * 201, "name;rm -rf", "x<y>"])
def test_validate_amplicon_name_rejects(bad):
    with pytest.raises(SecurityError):
        InputValidator.validate_amplicon_name(bad)


# --- secure_subprocess_call ------------------------------------------------


def test_secure_subprocess_call_success():
    result = secure_subprocess_call([sys.executable, "-c", "print(1)"])
    assert result.returncode == 0
    assert "1" in result.stdout


def test_secure_subprocess_call_rejects_non_list():
    with pytest.raises(SecurityError):
        secure_subprocess_call("echo hi")  # type: ignore[arg-type]


def test_secure_subprocess_call_rejects_dangerous_chars():
    with pytest.raises(SecurityError):
        secure_subprocess_call(["echo", "hi; rm -rf /"])


def test_secure_subprocess_call_rejects_non_str_arg():
    with pytest.raises(SecurityError):
        secure_subprocess_call(["echo", 123])  # type: ignore[list-item]


def test_secure_subprocess_call_with_cwd(tmp_path):
    result = secure_subprocess_call([sys.executable, "-c", "print(2)"], cwd=tmp_path)
    assert result.returncode == 0


def test_secure_subprocess_call_timeout():
    with pytest.raises(SecurityError):
        secure_subprocess_call(["sleep", "5"], timeout=1)


def test_secure_subprocess_call_oserror():
    with pytest.raises(SecurityError):
        secure_subprocess_call(["/nonexistent/binary/xyz"])


# --- validate_filename / sanitize_path edge branches -----------------------


@pytest.mark.parametrize(
    "name",
    [
        "...",  # only periods
        "CON.txt",  # reserved name with extension
        "trailingdot.",  # ends with period
        "trailing ",  # ends with space
        "x" * 256,  # too long (> 255 bytes)
        "",  # empty
    ],
)
def test_validate_filename_rejects(name):
    with pytest.raises(SecurityError):
        PathValidator.validate_filename(name)


def test_sanitize_path_empty_raises():
    with pytest.raises(SecurityError):
        PathValidator.sanitize_path("")


def test_validate_path_components_flags_dotdot():
    with pytest.raises(SecurityError):
        PathValidator.validate_path_components("a/../b")
