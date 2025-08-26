"""
Setup configuration for preprimer.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="preprimer",
    version="0.2.0",
    author="PrePrimer Development Team",
    description="Convert and analyze tiled primer schemes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FOI-Bioinformatics/preprimer",
    
    packages=find_packages(),
    
    install_requires=[
        "biopython>=1.80",
    ],
    
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "align": [
            # Optional dependencies for alignment features
        ],
    },
    
    entry_points={
        "console_scripts": [
            "preprimer=preprimer.cli:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    
    python_requires=">=3.8",
    
    project_urls={
        "Bug Reports": "https://github.com/FOI-Bioinformatics/preprimer/issues",
        "Source": "https://github.com/FOI-Bioinformatics/preprimer",
        "Documentation": "https://github.com/FOI-Bioinformatics/preprimer/blob/main/README.md",
    },
)
