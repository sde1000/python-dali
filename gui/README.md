hasseb USB DALI Master graphical user interface
===============================================

## Installing development environment and dependencies in Linux

To get python-dali working in fresh Linux Mint 19.2 installation, the following software and python dependencies need to be installed:

sudo apt-get install git  
git clone https://github.com/hasseb/python-dali.git  
sudo apt-get install python3-pip  
sudo apt install python3-distutils  
sudo pip3 install setuptools  
cd python-dali  
sudo python3 setup.py install  
sudo pip3 install PyQt5==5.14.0  
sudo pip3 install pyusb  

cd ..  

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

## Installing development environment and dependencies in Windows  

To get python-dali working in Windows 10, you need to have Python 3.7 or newer installed. The following software and python dependencies need to be installed as well:  

git clone https://github.com/hasseb/python-dali.git  
cd python-dali/  
python setup.py install  
pip install PyQt5  
pip install pyusb  
pip install hidapi

cd ..

To install pyhidapi:  
git clone https://github.com/awelkie/pyhidapi.git  
cd pyhidapi  
sudo python3 setup.py install  

To build the Windows installer package, you need to have NSIS installed in your Program Files folder.