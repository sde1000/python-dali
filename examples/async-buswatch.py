#!/usr/bin/env python3

import logging
import asyncio
from dali.driver.hid import tridonic
import signal
import dali.gear
import dali.device
from dali.device.helpers import DeviceInstanceTypeMapper

STOP = asyncio.Event()

def handle_sigint():
    STOP.set()

def print_command_and_response(dev, command, response, config_command_error):
    if config_command_error:
        print(f"ERROR: failed config command: {command}")
    elif command and not response:
        print(f"{command}")
    else:
        print(f"{command} -> {response}")

async def main():
    dev_inst_map = DeviceInstanceTypeMapper()
    dev = tridonic("/dev/dali/daliusb-*", glob=True, dev_inst_map=dev_inst_map)
    dev.bus_traffic.register(print_command_and_response)
    dev.connect()
    print("Waiting for device...")
    await dev.connected.wait()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")
    print("Reading device instance map...")
    await dev.run_sequence(dev_inst_map.autodiscover())
    print("Device instance map read")
    print(dev_inst_map)
    asyncio.get_running_loop().add_signal_handler(signal.SIGINT, handle_sigint)
    await STOP.wait()
    dev.disconnect()

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
