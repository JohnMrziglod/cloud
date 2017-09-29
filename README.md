# Cloud toolkit
These scripts are for handling cloud image data from the Pinocchio and Dumbo 
cameras.

## Installation
Simple checkout clone this branch to your local computer by using this command:

    git clone https://github.com/JohnMrziglod/cloud.git

Additionally, you will need the spareice_development branch by typhon (a python
module for atmospheric physics):

    git clone -b spareice_development https://github.com/JohnMrziglod/typhon.git
    cd typhon
    pip install --user --editable .
    
## Update
You can update your either the cloud toolkit or typhon by running this command 
either in the 'cloud' or 'typhon' directory:

    git pull
    
## Usage
This cloud toolkit contains several scripts:
*   **pinocchio_convert_raw_files.py**: Opens the raw files of the Pinocchio 
thermal cam, converts them either to PNG images or netcdf files and apply a 
image mask.
*   **pinocchio_calculate_cloud_parameters.py**: Calculates the cloud 
parameters (coverage, inhomgenity, etc.) from pinocchio netcdf thermal cam 
images.