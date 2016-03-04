#!/bin/bash
# step 1: install essential library
sudo apt-get install build-essential g++ 
sudo apt-get install build-essential python-all-dev
sudo apt-get install python-numpy
sudo apt-get install libgeos-dev
sudo apt-get install libproj-dev
sudo apt-get install libspatialite-dev libspatialite5 spatialite5-bin
wget http://download.osgeo.org/gdal/1.11.0/gdal-1.11.0.tar.gz
tar xvfz gdal-1.11.0.tar.gz
cd gdal-1.11.0
./configure --with-python --with-spatialite
make
sudo make install
cd ..
#Step 2:  Install OpenMpi
wget https://www.open-mpi.org/software/ompi/v1.8/downloads/openmpi-1.8.1.tar.gz
sudo apt-get install libibnetdisc-dev
tar -xvf openmpi-1.8.1.tar.gz
cd openmpi-1.8.1
./configure
make
sudo make install
cd ..
# Step 3:  Add to PATH
export PATH=/usr/bin:$PATH
export CPATH=/usr/local/include:$CPATH
export LIBRARY_PATH=/usr/local/lib:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Step 4: Install Python Packages for Rapid Watershed Delineation
sudo apt-get install python-pip
sudo pip install fiona 
sudo pip install pandas
sudo pip install shapely
sudo pip install pyshp

#Step 5: Compile TauDEM
sudo apt-get install git
git clone https://github.com/dtarb/TauDEM.git
cd TauDEM/src
make
cd ..




