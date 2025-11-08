from distutils.core import setup
from setuptools import find_packages
import pathlib
import re

root = pathlib.Path(__file__).parent
init = root / "steer_opencell_design" / "__init__.py"
version = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text()).group(1)

setup(
    name="steer-opencell-design",
    version=version,
    description="STEER OpenCell Design - A Python package for designing and modeling battery cells.",
    author="Nicholas Siemons",
    author_email="nsiemons@stanford.edu",
    url="https://github.com/stanford-developers/steer-opencell-design/",
    packages=find_packages(),
    install_requires=[
        "steer-core==0.1.24",
        "steer-materials==0.1.13",
        "pandas==2.1.4",
        "numpy==1.26.4",
        "datetime==5.5",
        "shapely==2.1.1",
        "plotly==6.2.0",
        "scipy==1.15.3"
    ],
    scripts=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)

