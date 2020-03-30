from setuptools import setup, find_packages
from os import path

from ascam.constants import VERSION

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ASCAM',
    version=VERSION,
    description='GUI for analysis of episodic single ion channel data.',
    long_description=long_description,
    url='https://github.com/AGPlested/ASCAM',
    author='Nikolai Zaki',
    author_email='kol@posteo.de',
    packages=find_packages(where='ASCAM'),
    python_requires='>=3.7',
    install_requires=[
        'pyqtgraph==0.11.0rc0',
        'PySide2>5',
        'numpy>1.18',
        'pandas',
        'scipy',
        'axographio',
        'nptyping',
        ],
    entry_points={  
            'console_scripts': [
                'ascam=run:main',
            ],
        },
)
