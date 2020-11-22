# ASCAM - Advanced Single Channel Analysis for Mac and more

ASCAM can be used to browse, organize and analyze episodic recordings of single ion channel currents.

## Installing 
Clone (with git, see below) or download the zip from this page.

Particularly on macOS (because of problems with ancient native Python) we recommend to use a clean environment. This can be achieved by installing miniconda and creating an environment called e.g. ASCAM.
`conda create --name ASCAM` 

Switch to this environment:
`conda activate ASCAM`

Install Python 3.7: 
`conda install python==3.7`

Then navigate to the folder you downloaded from this page (`ASCAM-master`) and issue: 
`pip install -e .`

This installation makes a shell script that lets you launch ASCAM with the command: 
`ascam`

For launch options:
`ascam --help`

### Further installation notes
If you also issue `conda install python.app` in your new environment then you can have a well-behaved Mac GUI with the following command from the parent directory of ASCAM:
`pythonw /ASCAM/src/ascam.py` 

required packages can be found in 'requirements.txt' and installed with 
`pip install -r requirements.txt`.

Note: Under python 3.9, axographio needs Numpy for setup, you can get around this by issuing the command `pip install numpy` before the general install command.

A straightforward installation can be achieved by first installing Anaconda or miniconda. At the time of writing, a working version for Mac is https://repo.anaconda.com/archive/Anaconda3-5.3.0-MacOSX-x86_64.pkg 

After successful installation of Anaconda, if you have Git installed, you can clone the ASCAM directory from Github onto your machine with the following command in the Terminal: *git clone https://github.com/AGPlested/ASCAM*. But if you had Git installed, you almost certainly knew that already. 

20-03-01: Note, with the migration to Qt, some problems may be encountered on the Mac if you already have installations of Qt4+. A fresh environment (e.g. can help. 

## Running ASCAM

There is an example raw data file of an AMPA receptor single channel patch in the ASCAM/data folder. This recording was sampled at 40 kHz.

You can remove the baseline, filter, and idealise data, or find the time of the first actvation. You can also page through episodes and mark them for later analysis or to be excluded from analysis. 

![macOS Screenshot](cuteSCAM.png)
