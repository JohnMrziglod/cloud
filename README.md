# Cloud toolkit
These scripts are for handling cloud image data from the Pinocchio and Dumbo 
cameras.

## Installation
Simply checkout clone this branch to your local computer by using this command:

    git clone https://github.com/JohnMrziglod/cloud.git

Additionally, you will need the typhon package (a python module for atmospheric
physics):

    git clone ttps://github.com/atmtools/typhon.git
    cd typhon
    pip install --user --editable .
    
## Update
You can update the cloud toolkit (or typhon) by running this command in the 
'cloud' (or 'typhon') directory:

    git pull
    
## Usage
This cloud toolkit contains several scripts:
*   **pinocchio_workflow.py**: Opens the raw files of the Pinocchio
thermal cam, converts them either to PNG images or netcdf files and apply a 
image mask. Then calculates the cloud parameters (coverage, inhomogeneity,
etc.) from pinocchio netcdf thermal cam images.
*   **monitor.py**: Displays the data from all selected sources and creates
plots.