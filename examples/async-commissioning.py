#!/usr/bin/env python3

# Script to address (extend) or readdress a DALI lighting system.

# Warning!  If run in readdressing mode on an existing system, the
# short addresses of all the control gear will be changed!

# Example usage:
# async-commissioning.py --device /dev/dali/hasseb-* --driver hasseb --extend --dry-run

import argparse
import asyncio
from dali.driver.hid import tridonic, hasseb
from dali.address import Short, Broadcast
from dali.gear.general import *
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

async def find_next(d, low, high):
    """Find the ballast with the lowest random address.

    The caller guarantees that there are no ballasts with an address
    lower than 'low'.

    If found, returns the random address.  SearchAddr will be set to
    this address in all ballasts.  The ballast is not withdrawn.

    If not found, returns None.
    """
    await d.send(SetSearchAddrH((high >> 16) & 0xff))
    await d.send(SetSearchAddrM((high >> 8) & 0xff))
    await d.send(SetSearchAddrL(high & 0xff))

    if low == high:
        response = await d.send(Compare())
        if response.value is True:
            return low
        return None
    response = await d.send(Compare())
    if response.value is True:
        midpoint = (low + high) // 2
        return await find_next(d, low, midpoint) \
            or await find_next(d, midpoint + 1, high)

async def main(args, loop):
    driver = drivers[args.driver]
    d = driver(args.device, loop=loop)
    if args.debug:
        d.bus_traffic.register(print_command_and_response)
    if not d.connect():
        log.error("Unable to open device %s with %s driver", args.device, args.driver)
        d.disconnect()
        return
    await d.connected.wait()
    log.info("Connected to device %s with %s driver", args.device, args.driver)

    available_addresses = list(range(0, 64))
    if args.mode != "readdress":
        # Work out which short addresses are in use
        for a in range(0, 64):
            in_use = await d.send(QueryControlGearPresent(Short(a)))
            if in_use.value:
                available_addresses.remove(a)

    log.info("Addresses available for allocation: %s", available_addresses)

    if args.mode == "readdress":
        if args.dry_run:
            log.info("Not deleting existing addresses because --dry-run")
        else:
            await d.send(DTR0(255))
            await d.send(SetShortAddress(Broadcast()))

    await d.send(Terminate())
    await d.send(Initialise(broadcast=True if args.mode == "readdress" else False))
    await d.send(Randomise())
    # Randomise can take up to 100ms
    await asyncio.sleep(0.1)
    low = 0
    high = 0xffffff
    while low is not None:
        low = await find_next(d, low, high)
        if low is not None:
            if available_addresses:
                new_addr = available_addresses.pop(0)
                if args.dry_run:
                    log.info("Not programming short address %s because --dry-run", new_addr)
                else:
                    log.info("Programming short address %s", new_addr)
                    await d.send(ProgramShortAddress(new_addr))
                    r = await d.send(VerifyShortAddress(new_addr))
                    if r.value is not True:
                        log.error("Device did not accept short address %s", new_addr)
            else:
                log.info("Device found but no short addresses remaining")
            await d.send(Withdraw())
            low = low + 1
    await d.send(Terminate())
    log.info("Addressing complete")
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
