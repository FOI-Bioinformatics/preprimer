# Directory structure:
# preprimer/
# ├── setup.py
# ├── README.md
# ├── preprimer/
# │   ├── __init__.py
# │   ├── __main__.py
# │   ├── convert.py
# │   ├── align.py
# │   ├── utils.py
# │   └── parsers/
# │       ├── __init__.py
# │       ├── varvamp.py
# │       └── artic.py

from setuptools import setup, find_packages

setup(
    name="preprimer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "biopython",
    ],
    entry_points={
        "console_scripts": [
            "preprimer=preprimer.main:main",
        ],
    },
)
