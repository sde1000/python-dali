#!/usr/bin/env python3

import logging
import asyncio
import sys
from dalidrivers.typed.hid import tridonic, hasseb
from dali.gear.general import RecallMaxLevel, RecallMinLevel, QueryActualLevel, Off
from dali.address import Broadcast, Short

async def main():
    # Edit to pick a device type.  On Linux, open the hidraw node named by
    # examples/50-dali-hid.rules; elsewhere hidapi finds the USB device.
    linux = sys.platform.startswith("linux")
    dev = tridonic("/dev/dali/daliusb-*" if linux else None, glob=True)
    #dev = hasseb("/dev/dali/hasseb-*" if linux else None, glob=True)
    print("Waiting to be connected...")
    await dev.connect()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")

    print("Switch supply on...")
    await dev.power_supply(True)
    await asyncio.sleep(1)
    dev.disconnect()

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
