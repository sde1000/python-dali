#!/usr/bin/env python3

import logging
import asyncio
from dali.driver.hid import tridonic, hasseb
from dali.gear.general import RecallMaxLevel, RecallMinLevel, QueryActualLevel, Off
from dali.address import Broadcast, Short

async def main(loop):
    # Edit to pick a device type.
    dev = tridonic("/dev/dali/daliusb-*", glob=True, loop=loop)
    #dev = hasseb("/dev/dali/hasseb-*", glob=True, loop=loop)
    dev.connect()
    print("Waiting to be connected...")
    await dev.connected.wait()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")

    print("Switch supply on...")
    await dev.power_supply(True)
    await asyncio.sleep(1)
    dev.disconnect()

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    loop.run_until_complete(main(loop))
    loop.close()
