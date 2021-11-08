#!/usr/bin/env python3

# Script to address (extend) or readdress a DALI lighting system.

# Warning!  If run in readdressing mode on an existing system, the
# short addresses of all the control gear will be changed!

# Example usage:
# async-commissioning.py --device /dev/dali/hasseb-* --driver hasseb --extend --dry-run

import argparse
import asyncio
from dali.driver.hid import tridonic, hasseb
from dali.sequences import Commissioning

import logging

log = logging.getLogger("commissioning")

drivers = {
    'tridonic': tridonic,
    'hasseb': hasseb,
}

def print_command_and_response(dev, command, response, config_command_error):
    if config_command_error:
        log.info(f"ERROR: failed config command: {command}")
    elif command and not response:
        log.info(f"{command}")
    else:
        log.info(f"{command} -> {response}")

def print_progress(p):
    if p.message:
        log.info(p.message)
    if p.completed and p.size:
        log.info(f"Progress: {p.completed*100/p.size:.1f}%")

async def main(args, loop):
    driver = drivers[args.driver]
    d = driver(args.device, loop=loop)
    if args.debug:
        d.bus_traffic.register(print_command_and_response)
    if not d.connect():
        log.error("Unable to open device %s with %s driver",
                  args.device, args.driver)
        d.disconnect()
        return
    await d.connected.wait()
    log.info("Connected to device %s with %s driver", args.device, args.driver)

    await d.run_sequence(
        Commissioning(readdress=args.mode=="readdress",
                      dry_run=args.dry_run),
        progress=print_progress)

    d.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add short addresses to a DALI lighting system")
    parser.add_argument('--device', '-d', type=str, required=True,
                        help="device file to open")
    parser.add_argument('--driver', '-r', type=str, required=True,
                        choices=drivers.keys(), help="device driver")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--extend', dest="mode", action="store_const", const="extend",
                            help="Add addresses to gear that is currently unaddressed")
    mode_group.add_argument('--readdress', dest="mode", action="store_const",
                            const="readdress", help="Clear short addresses and start again")
    parser.add_argument('--dry-run', '-n', action="store_true",
                        help="Don't actually change anything")
    parser.add_argument('--debug', dest="debug", action="store_true",
                        help="Output all DALI commands that are sent")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args, loop))
    loop.close()
