from setuptools import setup, find_packages
from os import path

VERSION = 0.1

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ASCAM",
    version=VERSION,
    description="Analysis of episodic single ion channel data.",
    long_description=long_description,
    url="https://github.com/AGPlested/ASCAM",
    author="Nikolai Zaki",
    author_email="kol@posteo.de",
    packages=find_packages(where=here),
    python_requires=">=3.10",
    install_requires=[
        "pyqtgraph>=0.14",
        #"PySide2==5.15.2.1", ### Swap this back in for systems without pyside6 compatibility  
	"PySide6",
        "numpy",
        "pandas",
        "scipy",
        "axographio==0.3.2",
        "pyobjc-framework-Cocoa==6.2.2;sys_platform=='Darwin'",
	"cython",
	"setuptools<=80.10.2"
    ],
    entry_points={"console_scripts": ["ascam=src.ascam:main"]},
)
