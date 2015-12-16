#!/bin/bash

set -e

sudo apt-get update

# See: https://github.com/Toblerity/Fiona/issues/74
#sudo apt-get install -y python-software-properties
#sudo add-apt-repository ppa:ubuntugis/ppa
#sudo apt-get update

sudo apt-get install -y g++
sudo apt-get install -y git
sudo apt-get install -y gfortran
sudo apt-get install -y build-essential
sudo apt-get install -y python-pip
sudo apt-get install -y python-all-dev
sudo apt-get install -y python-gdal
sudo apt-get install -y gdal-bin
sudo apt-get install -y libgdal-dev
sudo apt-get install -y openmpi-bin
sudo apt-get install -y libopenmpi-dev
sudo apt-get install -y proj-bin
sudo apt-get install -y libtool
sudo apt-get install -y libgeos-dev
sudo apt-get install -y libblas-dev
sudo apt-get install -y liblapack-dev
sudo apt-get install -y libatlas-base-dev

# Seems to need 2GB of RAM to install pip dependencies
sudo pip install -U pip
sudo pip install -r /vagrant/requirements.txt

export PATH=/usr/local/bin:$PATH
# This line was modified to include gdal which was not mentioned in the
# Google Doc
export CPATH=/usr/local/include:/usr/include/gdal:$CPATH
export LIBRARY_PATH=/usr/local/lib:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

sudo mkdir /opt/taudem
sudo chmod 777 /opt/taudem
git clone https://github.com/dtarb/TauDEM.git /opt/taudem
cd /opt/taudem
make
export PATH=/opt/taudem/:$PATH
