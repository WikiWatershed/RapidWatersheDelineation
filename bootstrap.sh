#!/bin/bash

set -e

sudo apt-get update

# See: https://github.com/Toblerity/Fiona/issues/74
sudo apt-get install -y python-software-properties
sudo add-apt-repository ppa:ubuntugis/ppa
sudo apt-get update

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

pip install -U pip
pip install -r /vagrant/requirements.txt

git clone https://github.com/dtarb/TauDEM.git /opt/taudem
cd /opt/taudem
# make
