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
    for i in range(3):
        print("Set max...")
        await dev.send(RecallMaxLevel(Broadcast()))
        await asyncio.sleep(1)
        response = await dev.send(QueryActualLevel(Broadcast()))
        print(f"Response was {response}")
        print("Set min...")
        await dev.send(RecallMinLevel(Broadcast()))
        await asyncio.sleep(1)
        response = await dev.send(QueryActualLevel(Broadcast()))
        print(f"Response was {response}")
    await dev.send(Off(Broadcast()))
    dev.disconnect()

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
