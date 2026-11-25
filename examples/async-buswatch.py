#!/usr/bin/env python3

import logging
import asyncio
import sys
from dalidrivers.typed.hid import tridonic
import dali.gear
import dali.device
from dali.device.helpers import DeviceInstanceTypeMapper

def print_command_and_response(dev, command, response, config_command_error):
    if config_command_error:
        print(f"ERROR: failed config command: {command}")
    elif command and not response:
        print(f"{command}")
    else:
        print(f"{command} -> {response}")

async def main():
    dev_inst_map = DeviceInstanceTypeMapper()
    # On Linux, open the hidraw node named by examples/50-dali-hid.rules;
    # elsewhere hidapi finds the USB device.
    linux = sys.platform.startswith("linux")
    dev = tridonic("/dev/dali/daliusb-*" if linux else None, glob=True,
                   dev_inst_map=dev_inst_map)
    dev.bus_traffic.register(print_command_and_response)
    print("Waiting for device...")
    await dev.connect()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")
    print("Reading device instance map...")
    await dev.run_sequence(dev_inst_map.autodiscover())
    print("Device instance map read")
    print(dev_inst_map)
    print("Watching the bus, press Ctrl+C to stop")
    try:
        # Run until Ctrl+C.  asyncio.run() turns it into a cancellation of
        # this task on every platform (loop.add_signal_handler() is not
        # available on Windows).
        await asyncio.Event().wait()
    finally:
        dev.disconnect()

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
