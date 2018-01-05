# Cloud toolkit
These scripts are for handling cloud image data from the Pinocchio and Dumbo 
cameras.

## Installation
Simply clone this branch to your local computer by using this command:

    git clone https://github.com/JohnMrziglod/cloud.git

Additionally, you will need the typhon package (a python module for atmospheric
physics):

    git clone ttps://github.com/atmtools/typhon.git
    cd typhon
    pip install --user --editable .
    
and you will need other python packages:
* numpy
* scipy
* pandas
* matplotlib
* Pillow
* netcdf4

You can install them via:

    ﻿pip3 install --user numpy scipy pandas matplotlib netcdf4 Pillow

    
## Update
You can update the cloud toolkit (or typhon) by running this command in the 
'cloud' (or 'typhon') directory:

    git pull
    
## Usage
This cloud toolkit contains several scripts:
*   **processor.py**: Opens the raw files of the Pinocchio
thermal cam, converts them either to PNG images or netcdf files and apply a 
image mask. Then calculates the cloud parameters (coverage, inhomogeneity,
etc.) from pinocchio netcdf thermal cam images.
*   **monitor.py**: Displays the data from all selected sources and creates
plots.