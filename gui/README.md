hasseb USB DALI Master graphical user interface
===============================================

## Installing development environment and dependencies

To get python-dali working in fresh Linux Mint 19.2 installation, the following software and python dependencies need to be installed:

sudo apt-get install git  
git clone https://github.com/hasseb/python-dali.git  
cd python-dali/  
sudo apt-get install python3-pip  
sudo apt install python3-distutils  
sudo pip3 install setuptools  
sudo python3 setup.py install  
sudo pip3 install PyQt5  
sudo pip3 install pyusb  

To install hidapi:  
sudo apt update  
sudo apt install g++  
git clone git://github.com/signal11/hidapi.git  
sudo apt-get install libudev-dev libusb-1.0-0-dev  
sudo apt-get install autotools-dev autoconf automake libtool  
cd hidapi  
./bootstrap  
./configure  
sudo make  
sudo make install  
sudo apt install libhidapi-libusb0  

cd ..

To install pyhidapi:  
git clone https://github.com/awelkie/pyhidapi.git  
cd pyhidapi  
sudo python3 setup.py install  
