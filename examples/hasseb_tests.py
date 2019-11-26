#!/usr/bin/env python3

import sys

from dali.driver import hasseb
from dali import bus

# Create hasseb USB DALI driver instance to handle messages
DALI_device = hasseb.SyncHassebDALIUSBDriver()
# Create DALI bus
DALI_bus = bus.Bus('hasseb DALI bus',   DALI_device)

# Print help if no arguments
if len(sys.argv) == 1:
    print("Give test number as an argument")
    print("1: Initialize bus")
    print("2: Scan bus")

# Make test if only one argument
elif len(sys.argv) == 2:
    # Initialize bus
    if sys.argv[1] == '1':
        print("Initializing bus...")
        DALI_bus.initialize_bus()
        print("Address | Random address | Groups | Device type")
        for i in range(len(DALI_bus._devices)):
            print(f"{DALI_bus._devices[i].address} | {DALI_bus._devices[i].randomAddress} | {DALI_bus._devices[i].groups} | {DALI_bus._devices[i].deviceType}")
    # Scan bus
    elif sys.argv[1] == '2':
        print("Scanning bus...")
        DALI_bus.assign_short_addresses()
        print("Address | Groups | Device type")
        for i in range(len(DALI_bus._devices)):
            print(f"{DALI_bus._devices[i].address} | {DALI_bus._devices[i].groups} | {DALI_bus._devices[i].deviceType}")
    else:
        print(f"Invalid argument {sys.argv[1]}")

# Print error if invalid argument
else:
    print("Give only one argument")