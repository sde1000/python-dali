#!/usr/bin/env python3

import logging
import asyncio
from dali.driver.hid import tridonic
import signal

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

async def main(loop):
    dev = tridonic("/dev/dali/daliusb-*", glob=True, loop=loop)
    dev.bus_traffic.register(print_command_and_response)
    dev.connect()
    print("Waiting for device...")
    await dev.connected.wait()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")
    loop.add_signal_handler(signal.SIGINT, handle_sigint)
    await STOP.wait()
    dev.disconnect()
    loop.stop()

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    asyncio.ensure_future(main(loop))
    loop.run_forever()
    # The device driver may still be cleaning up from disconnect() -
    # wait for it to finish
    loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
    loop.close()
