# 💿 Installation Guide

Complete installation instructions for PrePrimer on all supported platforms.

## 🎯 **Prerequisites**

### **System Requirements**
- **Python**: 3.8 or later
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 512 MB RAM minimum (2 GB recommended for large files)
- **Storage**: 100 MB free space

### **Python Dependencies**
PrePrimer automatically installs these required packages:
- `biopython>=1.80` - Biological sequence analysis
- `pandas>=1.3.0` - Data manipulation and analysis

## 🚀 **Installation Methods**

### **Method 1: From Source (Recommended)**

This is the most up-to-date installation method:

```bash
# 1. Clone the repository
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# 2. Install in development mode
pip install -e .

# 3. Verify installation
preprimer --version
```

### **Method 2: Direct pip Install (Coming Soon)**

```bash
# When available on PyPI
pip install preprimer
```

### **Method 3: Conda Install (Future)**

```bash
# When available on conda-forge
conda install -c conda-forge preprimer
```

## 🔧 **Platform-Specific Instructions**

### **macOS Installation**

#### **Using Homebrew (Recommended)**
```bash
# Install Python if needed
brew install python

# Clone and install PrePrimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e .
```

#### **Using Conda**
```bash
# Install miniconda if needed
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh

# Create environment and install
conda create -n preprimer python=3.10
conda activate preprimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip install -e .
```

### **Linux Installation**

#### **Ubuntu/Debian**
```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip git

# Clone and install PrePrimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e .

# Add to PATH if needed
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

#### **CentOS/RHEL/Fedora**
```bash
# Install Python and pip
sudo yum install python3 python3-pip git  # CentOS/RHEL
sudo dnf install python3 python3-pip git  # Fedora

# Clone and install PrePrimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e .
```

### **Windows Installation**

#### **Using Windows Subsystem for Linux (WSL) - Recommended**
```bash
# 1. Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# 2. In WSL Ubuntu terminal:
sudo apt update && sudo apt install python3 python3-pip git
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e .
```

#### **Native Windows**
```powershell
# 1. Install Python from python.org or Microsoft Store
# 2. Install Git from git-scm.com
# 3. In PowerShell or Command Prompt:

git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip install -e .
```

## 🐍 **Virtual Environment Setup (Recommended)**

Using virtual environments prevents dependency conflicts:

### **Using venv**
```bash
# Create virtual environment
python3 -m venv preprimer-env

# Activate (Linux/macOS)
source preprimer-env/bin/activate

# Activate (Windows)
preprimer-env\Scripts\activate

# Install PrePrimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip install -e .
```

### **Using conda**
```bash
# Create conda environment
conda create -n preprimer python=3.10
conda activate preprimer

# Install PrePrimer
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip install -e .
```

## 🧪 **Development Installation**

For developers who want to contribute:

```bash
# Clone with development dependencies
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer

# Install with development extras
pip install -e ".[dev]"

# This includes:
# - pytest (testing)
# - pytest-cov (coverage)
# - black (code formatting)
# - flake8 (linting)
# - mypy (type checking)
```

## ✅ **Verify Installation**

### **Basic Verification**
```bash
# Check version
preprimer --version
# PrePrimer 0.2.0

# List supported formats
preprimer list
# Should show varvamp, artic, olivar formats

# Test with help
preprimer --help
# Should show command help
```

### **Comprehensive Test**
```bash
# Run test suite
python tests/test_parsers_unified.py

# Expected output:
# 🧪 Running harmonized parser tests...
# ✅ Testing VarVAMP parser...
# ✅ Testing ARTIC parser...
# ✅ Testing Olivar parser...
# 🎉 All harmonized tests passed!
```

### **Python API Test**
```python
# Test Python import
python -c "
import preprimer
from preprimer import convert_primers
print('✅ PrePrimer imported successfully')
print(f'Version: {preprimer.__version__}')
"
```

## 🔧 **Troubleshooting Installation**

### **Common Issues**

#### **Permission Errors**
```bash
# If you get permission errors, try:
pip install -e . --user

# Or use a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### **Python Version Issues**
```bash
# Check Python version
python --version
python3 --version

# PrePrimer requires Python 3.8+
# Update Python if needed
```

#### **Git Not Found**
```bash
# Install git first
# macOS: brew install git
# Ubuntu: sudo apt install git
# Windows: Download from git-scm.com
```

#### **Dependency Conflicts**
```bash
# Use virtual environment to isolate dependencies
python3 -m venv clean-env
source clean-env/bin/activate
pip install -e .
```

### **Platform-Specific Issues**

#### **macOS: Command Line Tools**
```bash
# Install Xcode command line tools if needed
xcode-select --install
```

#### **Linux: Missing Development Headers**
```bash
# Ubuntu/Debian
sudo apt install python3-dev build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel
```

#### **Windows: Microsoft Visual C++**
```powershell
# Install Microsoft C++ Build Tools if needed
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

## 🔄 **Updating PrePrimer**

### **From Source**
```bash
cd preprimer
git pull origin main
pip install -e . --upgrade
```

### **Verify Update**
```bash
preprimer --version
python tests/test_parsers_unified.py
```

## 🗑️ **Uninstalling PrePrimer**

### **Remove Package**
```bash
pip uninstall preprimer
```

### **Remove Source Directory**
```bash
# If installed from source
rm -rf /path/to/preprimer
```

### **Remove Virtual Environment**
```bash
# If using virtual environment
rm -rf preprimer-env  # or your environment name
```

## 🆘 **Getting Help**

If you encounter installation issues:

1. **Check Prerequisites**: Ensure Python 3.8+ is installed
2. **Use Virtual Environment**: Isolate dependencies
3. **Check GitHub Issues**: [Search existing issues](https://github.com/FOI-Bioinformatics/preprimer/issues)
4. **Report New Issues**: Include:
   - Operating system and version
   - Python version (`python --version`)
   - Full error message
   - Installation commands used

## 📋 **Installation Checklist**

- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] Virtual environment created (recommended)
- [ ] PrePrimer cloned and installed
- [ ] Installation verified with `preprimer --version`
- [ ] Test suite passed
- [ ] Python API import successful

**Once all items are checked, you're ready to use PrePrimer! 🎉**

---

## 🔗 **What's Next?**

- **[Quick Start Guide](quick-start.md)** - Your first conversion in 5 minutes
- **[Basic Usage](basic-usage.md)** - Essential commands and workflows
- **[Configuration](configuration.md)** - Customizing PrePrimer behavior

**Happy primer converting! 🧬✨**