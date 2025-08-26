# Windows Compatibility

## Current Status: Not Supported

PrePrimer does not currently support native Windows installations due to Unicode character encoding limitations in the Windows command prompt and PowerShell environments.

## Technical Details

The issue stems from Windows using the cp1252 codec by default, which cannot encode the Unicode emoji characters used throughout PrePrimer's user interface and test output. Specifically:

- Test runner emojis: 🧪 (U+1F9EA), ✅ (U+2705), 🎉 (U+1F389)
- CLI output emojis used for better user experience
- Unicode characters in documentation and help text

## Recommended Solution for Windows Users

**Use Windows Subsystem for Linux (WSL2)** which provides full Linux compatibility:

```bash
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# In WSL Ubuntu terminal:
sudo apt update && sudo apt install python3 python3-pip git
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e .
```

## Future Windows Support

To add native Windows support in the future, one would need to:

1. Replace all Unicode emojis with ASCII alternatives or make them optional
2. Add proper Windows console encoding handling
3. Test extensively on Windows environments
4. Update CI/CD to include Windows testing

However, this would compromise the user experience on Unix-like systems where Unicode works properly.

## Alternative Solutions

Other potential workarounds for Windows users:

1. **Docker Container**: Run PrePrimer in a Linux container
2. **Virtual Machine**: Use a Linux VM
3. **Git Bash/MSYS2**: May work but not officially tested
4. **Windows Terminal with UTF-8**: May resolve encoding issues but not guaranteed

## Current Platform Support

- ✅ **Linux**: Full support (tested on Ubuntu, CentOS, Debian)
- ✅ **macOS**: Full support (tested on Intel and Apple Silicon)
- ❌ **Windows**: Not supported (use WSL2 instead)