from distutils.core import setup
from setuptools import find_packages

setup(
    name='SteerEnergyStorage',
    version="0.0.3", 
    description='Modelling energy storage from cell to site',
    author='Nicholas Siemons',
    author_email='nsiemons@stanford.edu',
    url="https://github.com/nicholas9182/SteerEnergyStorage/",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    scripts=[],
    classifiers=[ 
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'launch_dash_app=dash_app.app:run',
        ],
    }
)
