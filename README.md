ASCAM can be used to browse, organize and analyze episodic recordings of single ion channel currents.

## Installing 
Particularly on macOS (because of problems with ancient native Python) we recommend to use a clean environment. This can be achieved by installing miniconda and creating an environment called e.g. SAFT.

In this environment, 
`conda install python==3.7`

Then navigate to the folder you downloaded from this page (`ASCAM-master`) and you can use 

`pip install -e .`

Finally, launch ASCAM with the command 
`ascam`

### further installation notes
required packages can be found in 'requirements.txt' and installed with 
`pip install -r requirements.txt`.

Note: Unfortunately both ASCAM and one of its dependencies require Numpy, this probably
means that numpy needs to be installed separately before ASCAM can be installed.

A straightforward installation can be achieved by first installing Anaconda or miniconda. At the time of writing, a working version for Mac is https://repo.anaconda.com/archive/Anaconda3-5.3.0-MacOSX-x86_64.pkg 

After successful installation of Anaconda, if you have Git installed, you can clone the ASCAM directory from Github onto your machine with the following command in the Terminal: *git clone https://github.com/AGPlested/ASCAM*. But if you had Git installed, you almost certainly knew that already. 

20-03-01: Note, with the migration to Qt, some problems may be encountered on the Mac if you already have installations of Qt4+. Our investigations so far suggest a fresh install of Anaconda can help. 

## Running

There is an example raw data file of an AMPA receptor single channel patch in the ASCAM/data folder. This recording was sampled at 40 kHz.

![macOS Screenshot](cuteSCAM.png)
