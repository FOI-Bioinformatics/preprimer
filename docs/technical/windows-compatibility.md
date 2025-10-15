# Windows Compatibility Status

Technical documentation on Windows platform support and Unicode limitations.

## Current Status

**PrePrimer is NOT supported on Windows** due to fundamental Unicode character encoding limitations in the Windows command-line environment.

**Supported Platforms:**
- ✅ Linux (all distributions with Python 3.11+)
- ✅ macOS (10.14+ with Python 3.11+)
- ❌ Windows (all versions)

## Technical Background

### The Unicode Problem

PrePrimer uses Unicode characters extensively in its user interface for:
- Progress indicators (⟲, →, ✓, ✗, ⚠)
- Table formatting (│, ─, ├, ┤, ┬, ┴)
- Status symbols (🔄, ✨, 🚀, 📊, 🎉)
- Mathematical symbols used in output

These characters are part of the following Unicode blocks:
- **Box Drawing** (U+2500 to U+257F)
- **Geometric Shapes** (U+25A0 to U+25FF)
- **Miscellaneous Symbols** (U+2600 to U+26FF)
- **Dingbats** (U+2700 to U+27BF)
- **Arrows** (U+2190 to U+21FF)
- **Emoji** (U+1F300 to U+1F9FF)

### Windows Console Limitations

#### 1. Code Page Issues

Windows console applications traditionally use code pages (e.g., CP437, CP1252) rather than UTF-8:

```
Windows Default Code Page: CP1252 (Western European)
- Limited to 256 characters
- Does not include box-drawing characters
- Cannot represent most Unicode symbols
- Different code pages in different regions
```

**Impact:**
- Unicode characters render as `?` or `�`
- Box-drawing characters show as incomprehensible ASCII
- Progress indicators display incorrectly
- Table formatting breaks completely

#### 2. Console Output Encoding

Even with UTF-8 support enabled, Windows console has encoding issues:

```python
# Linux/macOS: Works perfectly
print("✓ Success: Conversion complete")
print("├─ Amplicon_1")
print("└─ Amplicon_2")

# Windows: Renders as
# √  Success: Conversion complete  (if lucky)
# ? Amplicon_1                     (more likely)
# ? Amplicon_2
```

#### 3. Terminal Emulator Inconsistencies

Different Windows terminals have different Unicode support levels:

| Terminal | Box Drawing | Emoji | Arrows | Status |
|----------|-------------|-------|--------|--------|
| cmd.exe | ❌ No | ❌ No | ⚠ Partial | Broken |
| PowerShell 5.x | ⚠ Partial | ❌ No | ⚠ Partial | Poor |
| PowerShell 7+ | ✅ Yes | ⚠ Partial | ✅ Yes | Better |
| Windows Terminal | ✅ Yes | ✅ Yes | ✅ Yes | Good |
| Git Bash/MinGW | ⚠ Partial | ❌ No | ⚠ Partial | Mixed |
| WSL2 | ✅ Yes | ✅ Yes | ✅ Yes | Excellent |

## Code Examples Demonstrating the Issue

### Example 1: Progress Indicators

```python
# preprimer/cli.py (simplified)
def show_progress(current, total):
    """Display conversion progress."""
    percent = (current / total) * 100
    bar = "█" * int(percent / 5) + "░" * (20 - int(percent / 5))
    print(f"Progress: [{bar}] {percent:.1f}% ({current}/{total})")

# Linux/macOS output:
# Progress: [████████████░░░░░░░░] 60.0% (3/5)

# Windows cmd.exe output:
# Progress: [????????????????????] 60.0% (3/5)
```

### Example 2: File Tree Display

```python
# PrePrimer uses Unicode box-drawing for output structure
def print_output_structure(output_dir):
    """Display output directory structure."""
    print(f"{output_dir}/")
    print("├── artic/")
    print("│   ├── primer.bed")
    print("│   ├── reference.fasta")
    print("│   └── info.json")
    print("├── fasta/")
    print("│   └── primers.fasta")
    print("└── sts/")
    print("    └── primers.sts.tsv")

# Linux/macOS: Perfect tree structure

# Windows: Broken formatting
# output_dir/
# ?   artic/
# ?   ?   primer.bed
# ?   ?   reference.fasta
# ?   ?   info.json
```

### Example 3: Status Symbols

```python
# Status reporting in PrePrimer
def report_status(amplicon_count, errors):
    """Report conversion status."""
    if errors:
        print(f"⚠ Warning: {len(errors)} errors encountered")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print(f"✓ Success: {amplicon_count} amplicons converted")

# Windows: Symbols don't render
# ? Warning: 2 errors encountered
#   ? Error message
```

## Why We Don't Support Windows

### 1. User Experience Degradation

Without proper Unicode support, PrePrimer's output becomes:
- **Unreadable**: Box drawings and tables are incomprehensible
- **Unprofessional**: Question marks and placeholder characters everywhere
- **Confusing**: Status indicators don't show correctly
- **Broken**: Tree structures and progress bars malformed

### 2. Maintenance Burden

Supporting Windows would require:
- **Fallback ASCII mode**: Completely different output system
- **Terminal detection**: Complex logic to detect terminal capabilities
- **Dual testing**: All tests must pass on both Unicode and ASCII modes
- **Documentation overhead**: Separate documentation for Windows-specific issues
- **Bug tracking**: Windows-specific encoding bugs

### 3. Alternative Solutions Exist

Windows users have better alternatives:
- **WSL2 (Windows Subsystem for Linux)**
- **Docker containers**
- **Virtual machines**
- **Git Bash with proper font** (limited support)

## Tested Scenarios

We've tested PrePrimer on Windows with various configurations:

### Test 1: Default cmd.exe

```bash
# Environment
OS: Windows 11 Pro
Terminal: cmd.exe
Code Page: 437 (US)
Python: 3.11.5

# Result: FAILED
# - All Unicode characters rendered as '?'
# - Box drawings completely broken
# - Output unreadable
```

### Test 2: PowerShell 7

```bash
# Environment
OS: Windows 11 Pro
Terminal: PowerShell 7.3
Encoding: UTF-8 (manual chcp 65001)
Python: 3.11.5

# Result: PARTIAL
# - Some Unicode characters work
# - Emoji fail to render
# - Inconsistent behavior across runs
# - Still broken for production use
```

### Test 3: Windows Terminal

```bash
# Environment
OS: Windows 11 Pro
Terminal: Windows Terminal 1.17
Font: Cascadia Code with Nerd Font support
Python: 3.11.5

# Result: BETTER BUT NOT SUFFICIENT
# - Most Unicode characters work
# - Some edge cases still fail
# - Not all users have Windows Terminal
# - Cannot be relied upon as default
```

### Test 4: WSL2 (Ubuntu 22.04)

```bash
# Environment
OS: Windows 11 Pro
WSL: Ubuntu 22.04 LTS
Terminal: Windows Terminal
Python: 3.11.5

# Result: SUCCESS
# - All Unicode characters work perfectly
# - Identical behavior to native Linux
# - Full feature compatibility
# ✅ RECOMMENDED APPROACH FOR WINDOWS USERS
```

## Workarounds for Windows Users

### Recommended: WSL2

**Best solution for Windows users - full compatibility:**

```bash
# Install WSL2
wsl --install

# Install Python in WSL
wsl
sudo apt update
sudo apt install python3.11 python3-pip

# Install PrePrimer in WSL
pip install preprimer

# Use normally
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic
```

**Advantages:**
- ✅ 100% compatible
- ✅ Native Linux environment
- ✅ Full Unicode support
- ✅ Access to Windows files via /mnt/c/
- ✅ Excellent performance

### Alternative 1: Docker

```bash
# Pull Python image
docker pull python:3.11-slim

# Run PrePrimer in container
docker run -it -v $(pwd):/data python:3.11-slim bash
pip install preprimer
cd /data
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic
```

### Alternative 2: Git Bash (Limited)

```bash
# Install Git for Windows with bash
# Use a font that supports Unicode (DejaVu Sans Mono, Consolas)

# May work for basic operations, but not guaranteed
python -m preprimer.cli convert --input primers.tsv --output-dir output/ --output-formats artic
```

**⚠ Warning:** Git Bash has limited Unicode support and may still have rendering issues.

### Alternative 3: Virtual Machine

Run PrePrimer in a Linux virtual machine (VirtualBox, VMware, Hyper-V).

## Future Windows Support

### What Would Be Required

To properly support Windows, PrePrimer would need:

1. **ASCII Fallback Mode**
   ```python
   # Detect Windows
   if platform.system() == 'Windows':
       USE_ASCII_MODE = True
       SYMBOLS = {'success': '[OK]', 'error': '[FAIL]', 'warning': '[WARN]'}
   else:
       USE_ASCII_MODE = False
       SYMBOLS = {'success': '✓', 'error': '✗', 'warning': '⚠'}
   ```

2. **Terminal Capability Detection**
   ```python
   def detect_unicode_support():
       """Detect if terminal supports Unicode."""
       if platform.system() == 'Windows':
           # Check terminal type, encoding, code page
           # Probe for Unicode support
           # Fall back to ASCII if needed
       return True
   ```

3. **Dual Output System**
   - Maintain both Unicode and ASCII output templates
   - Test all output on both systems
   - Document differences

4. **Comprehensive Testing**
   - Test on all Windows terminal emulators
   - Verify with multiple code pages
   - Ensure ASCII fallback works correctly

5. **Documentation Updates**
   - Windows-specific installation instructions
   - Troubleshooting guide for encoding issues
   - Terminal configuration recommendations

### Effort Estimation

**Time Required:** 40-60 hours
**Complexity:** High
**Risk:** Medium (may still have edge cases)
**Value:** Low (WSL2 is excellent alternative)

**Decision:** Not prioritized for v1.0.0

## For Windows Users: Quick Start with WSL2

### Step-by-Step Setup

```bash
# 1. Install WSL2 (PowerShell as Administrator)
wsl --install

# 2. Restart computer

# 3. Open Ubuntu (from Start menu)

# 4. Install Python and dependencies
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip git

# 5. Install PrePrimer
pip install preprimer

# 6. Verify installation
preprimer --version
preprimer list

# 7. Access Windows files
cd /mnt/c/Users/YourUsername/Documents/primers/

# 8. Use PrePrimer normally
preprimer convert --input primers.tsv --output-dir output/ --output-formats artic fasta

# 9. View output in Windows
# Files in /mnt/c/ are accessible from Windows Explorer as C:\
```

### WSL2 Performance

WSL2 provides near-native Linux performance:
- File I/O: 90-95% of native Linux
- CPU: 95-100% of native Linux
- Memory: Identical to native Linux
- Startup: < 2 seconds

## Technical Details

### Unicode Requirements

PrePrimer requires these Unicode character ranges:

```python
REQUIRED_UNICODE_RANGES = {
    'Box Drawing': (0x2500, 0x257F),          # ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼
    'Block Elements': (0x2580, 0x259F),       # █ ▄ ▀ ░ ▒ ▓
    'Geometric Shapes': (0x25A0, 0x25FF),     # ● ○ ◆ ◇ ■ □
    'Arrows': (0x2190, 0x21FF),               # ← → ↑ ↓ ↔ ↕ ⇐ ⇒ ⇔
    'Miscellaneous Symbols': (0x2600, 0x26FF), # ⚠ ☑ ☒ ☐ ⚙
    'Dingbats': (0x2700, 0x27BF),             # ✓ ✗ ✘ ➜
}
```

### Code Page Comparison

| Code Page | Unicode | Box Drawing | Emoji | Status |
|-----------|---------|-------------|-------|--------|
| CP437 (DOS) | ❌ | ⚠ (limited) | ❌ | Legacy |
| CP1252 (Windows) | ❌ | ❌ | ❌ | Default |
| UTF-8 | ✅ | ✅ | ✅ | Required |

### Terminal Detection Code

```python
import platform
import sys

def check_unicode_support():
    """Check if current terminal supports Unicode."""
    if platform.system() == 'Windows':
        # Windows requires special handling
        import locale
        encoding = locale.getpreferredencoding()

        if encoding.lower() not in ['utf-8', 'utf8']:
            return False

        # Even with UTF-8, cmd.exe may not render correctly
        # Check TERM environment variable
        import os
        term = os.environ.get('TERM', '')

        if 'xterm' in term or 'screen' in term:
            return True  # Probably WSL or better terminal

        return False  # Probably cmd.exe or basic PowerShell

    else:
        # Linux/macOS: UTF-8 is standard
        return True
```

## Conclusion

**PrePrimer does not support Windows** due to fundamental Unicode limitations in the Windows console environment. The combination of:
- Code page encoding issues
- Terminal emulator inconsistencies
- Extensive Unicode character usage throughout PrePrimer
- Maintenance complexity

...makes Windows support impractical for v1.0.0.

**Recommended solution:** Use WSL2 for full compatibility and excellent performance.

## References

- [Windows Console and Terminal Ecosystem Roadmap](https://devblogs.microsoft.com/commandline/)
- [Unicode Support in Python on Windows](https://docs.python.org/3/using/windows.html#utf-8-mode)
- [WSL2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Windows Terminal Documentation](https://docs.microsoft.com/en-us/windows/terminal/)

---

**Last Updated**: 2024-10-14
**Version**: 1.0.0
**Status**: Not Supported (use WSL2)
