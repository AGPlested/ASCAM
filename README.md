# ASCAM - Advanced Single Channel Analysis for Mac and more

ASCAM can be used to browse, organize and analyze episodic recordings of single ion channel currents.

## Installation
A straightforward installation can be achieved by first installing Anaconda or miniconda. At the time of writing, a working version for Mac is https://repo.anaconda.com/archive/Anaconda3-5.3.0-MacOSX-x86_64.pkg

After successful installation of Anaconda, if you have Git installed, you can clone the ASCAM directory from Github onto your machine with the following command in the Terminal:
`git clone https://github.com/AGPlested/ASCAM`

We recommend to use a clean environment. This can be achieved by installing miniconda and creating an environment called e.g. ASCAM. Note, with Big Sur, some adjustments are needed.
`conda create --name ASCAM python=3.10 && conda activate ASCAM`

By default conda does not install its own version of `pip`. (You can check which version is being used with `pip --version`.)
If it is not the correct one install it in your conda environment using:
`conda install pip`

Then navigate to the folder you downloaded from this page (`ASCAM-master`) and issue:
`pip install -e .`
Note: it might be necessary to install `numpy` separately before installing ASCAM (in this case, try `conda install numpy`).

Note2: On Windows, at time of writing, you need Microsoft C++ build tools 14.0 
https://visualstudio.microsoft.com/visual-cpp-build-tools/ and TICK THE BOX!

This installation makes a shell script that lets you launch ASCAM with the command:
`ascam`

For launch options:
`ascam --help`

### Further installation notes
If you also issue `conda install python.app` in your new environment then you can have a well-behaved Mac GUI with the following command from the parent directory of ASCAM:
`pythonw /ASCAM/src/ascam.py`

20-03-01: Note, with the migration to Qt, some problems may be encountered on the Mac if you already have installations of Qt4+. A fresh environment (e.g. can help.
21-05-25: Update to Big Sur - Pyqtgraph and PyQt need Python 3.8, PySide2 5.15 and the command export QT_MAC_WANTS_LAYER=1 must be issued in the Terminal.


Note: Tables in axograph and matlab have named columns ASCAM uses these names to determine what data is dealing with. Therefore the column containing the recorded current should contain either "current", "trace" or "Ipatch", the name of the column holding the recorded piezo voltage should contain the string "piezo" and the name of the command voltage column should contain "command".

There is an example raw data file of an AMPA receptor single channel patch in the ASCAM/data folder. This recording was sampled at 40 kHz.

You can remove the baseline, filter, and idealise data, or find the time of the first actvation. You can also page through episodes and mark them for later analysis or to be excluded from analysis.

![macOS Screenshot](cuteSCAM.png)

## Quick guide to ASCAM

* Load file by `File > Open file` from the menu bar and selecting the recording using the file browser. `.mat` and `.axgx` or `.axgd` files should open without a problem.
* Baseline correction: `Processing > Baseline correction` from the menu bar
    * You can choose between *methods* `Polynomial` or `Offset` to fit the baseline to a polynomial with a chosen degree or subtract a constant, respectively.
    * The *selection* allows you to put in where the baseline is. This can be *intervals* that you type in or determined by *piezo* trace automatically.
        * If you choose *piezo* and *active* is unchecked, the baseline is set to the time when the piezo voltage deviates from 0 by more than *deviation* percent.
        * If you choose *piezo* and *active* is checked, the baseline is set to the time when the piezo voltage is different from maximum piezo voltage by more than *deviation* percent.
        * If you choose *intervals* you can put in the start and end times of baseline interval. This needs to be formatted like a python list such as `[0, 15]`.
* Filter: `Processing > Filter` and choose between Gauss filter and Chung-Kennedy filter (Chung and Kennedy 1991). In both cases you need to alter needed parameters (corner frequency for Gauss and weights etc. for CK)
* Idealization: `Analysis > Idealize` for finding an idealization using threshold crossing method.
    * You need to put in the *amplitudes* separated by spaces and without any brackets, such as `0 0.7 1.2 1.8 2.2` (pA) for the sample data. You can also drag the drawn lines for the amplitude to adjust them.
    * Thresholds can be put in manually in *thresholds* or auto generated and set to the midpoint between each two amplitudes.
    * If you want to apply a resolution to remove shorter events, you can put in a resolution
    * You can also *interpolate* the signal with a cubic spline with an interpolation factor you choose. 
    * After clicking `Calculate idealization` you can show or export event table, or export the idealization. 
* First Activation Threshold: `Analysis > First Activation`. You can type the first activation threshold or make it *draggable* to adjust the line drawn on the trace and click `Set threshold`.
    * You can alternatively go through the episodes to mark the point of first activation manually.
