from setuptools import setup, find_packages
import pathlib
import re

# Read the contents of README file for long description
root = pathlib.Path(__file__).parent
readme_path = root / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

# Extract version from __init__.py
init = root / "steer_opencell_design" / "__init__.py"
version = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text()).group(1)

setup(
    name="steer-opencell-design",
    version=version,
    description="A Python library for battery cell design and analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nicholas Siemons",
    author_email="nsiemons@stanford.edu",
    url="https://github.com/stanford-developers/steer-opencell-design/",
    project_urls={
        "Source": "https://github.com/stanford-developers/steer-opencell-design/",
        "Documentation": "https://github.com/stanford-developers/steer-opencell-design/",
    },
    packages=find_packages(exclude=["test*", "build*"]),
    include_package_data=True,
    install_requires=[
        "steer-core==0.1.22",
        "steer-materials==0.1.13",
        "pandas>=2.1.4",
        "numpy>=1.26.4",
        "shapely>=2.1.1",
        "plotly>=6.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "isort",
            "flake8",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires="==3.10",
    zip_safe=False,
)
