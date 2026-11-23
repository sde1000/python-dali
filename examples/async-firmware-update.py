#!/usr/bin/env python3
"""async-firmware-update.py - transfer a firmware image over DALI

Firmware transfer (IEC 62386-105) uses 32-bit forward frames, which are
supported by the Tridonic DALI USB interface and by Lunatone LUBA RS232
interfaces.  The commands live in dali.firmware and the update
procedure in dali.firmware_sequences.

A firmware transfer frame addresses a bus unit without saying whether
it is control gear or a control device, so the same sequence updates
either.  This example scans for units that answer the firmware queries
and, for context, reports whether each short address also looks like
control gear or a control device - a short address on its own does not
tell you which.

    # See what could be updated, and change nothing
    ./async-firmware-update.py --uri luba232:/dev/ttyUSB0 --scan

    # Update one unit
    ./async-firmware-update.py --uri luba232:/dev/ttyUSB0 \
        --address 3 --image new-firmware.bin --block-size 48

The block size is a property of the target product and comes from its
firmware update documentation; there is no sensible default.  Read the
warnings in dali.firmware_sequences before pointing this at hardware
you care about - the order of the commands has been inferred from the
command set rather than taken from a copy of the standard.

This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program. If not, see
<https://www.gnu.org/licenses/>.
"""
import argparse
import asyncio
import sys

from dali.address import (
    DeviceShort,
    FirmwareBroadcast,
    FirmwareShort,
    GearShort,
)
from dali.device.general import QueryDeviceStatus
from dalidrivers.misc.hid import tridonic
from dalidrivers.typed.serial import DriverLubaRs232
from dali.firmware_sequences import FindFirmwareUpdateTargets, FirmwareUpdate
from dali.gear.general import QueryControlGearPresent


async def connect(uri):
    """Open either a LUBA serial interface or a Tridonic DALI USB one"""
    if uri.startswith(f"{DriverLubaRs232.uri_scheme}:"):
        driver = DriverLubaRs232(uri=uri)
        await driver.connect()
        return driver

    driver = tridonic(uri, glob="*" in uri)
    driver.connect()
    print("Waiting for device...")
    await driver.connected.wait()
    print(f"Connected, firmware={driver.firmware_version}, "
          f"serial={driver.serial}")
    return driver


async def describe(driver, short):
    """Say whether a short address looks like gear, a device, or both

    The two address spaces are separate, so both answers are possible
    and neither is what a firmware transfer frame addresses.
    """
    kinds = []
    gear = await driver.send(QueryControlGearPresent(GearShort(short)))
    if gear and gear.value:
        kinds.append("control gear")
    device = await driver.send(QueryDeviceStatus(DeviceShort(short)))
    if device and device.valid:
        kinds.append("control device")
    return " and ".join(kinds) or "not answering as gear or device"


async def scan(driver):
    targets = await driver.send(FindFirmwareUpdateTargets(), progress=print)
    if not targets:
        print("\nNo bus unit answered the firmware transfer queries")
        return targets
    print()
    for target in targets:
        kind = await describe(driver, target.address)
        print(f"A{target.address}: firmware update version "
              f"{target.version}, features {target.features:#04x} ({kind})")
    return targets


async def update(driver, destination, image, block_size, restart):
    print(f"\nUpdating {destination} with {len(image)} bytes")
    blocks = await driver.send(
        FirmwareUpdate(destination, image, block_size=block_size,
                       restart=restart),
        progress=print,
    )
    print(f"Transferred {blocks} blocks")


async def main(args):
    driver = await connect(args.uri)
    try:
        if args.scan or args.image is None:
            await scan(driver)
            return

        with open(args.image, "rb") as f:
            image = f.read()

        if args.broadcast:
            # Every unit on the bus gets the same image and none of them
            # can be asked whether it worked; only do this when the bus
            # holds nothing but the product being updated.
            destination = FirmwareBroadcast()
        else:
            destination = FirmwareShort(args.address)
            print(f"A{args.address} is {await describe(driver, args.address)}")

        await update(driver, destination, image, args.block_size,
                     not args.no_restart)
    finally:
        # Only the HID drivers have an explicit teardown
        if hasattr(driver, "disconnect"):
            driver.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--uri", default="/dev/dali/daliusb-*",
        help="LUBA serial URI (luba232:/dev/ttyUSB0) or a Tridonic DALI "
        "USB device path, which may be a glob")
    parser.add_argument(
        "--scan", action="store_true",
        help="list the bus units that support firmware transfer and exit")
    parser.add_argument("--image", help="firmware image to transfer")
    parser.add_argument(
        "--address", type=int, help="short address of the unit to update")
    parser.add_argument(
        "--broadcast", action="store_true",
        help="update every unit on the bus at once, without verification")
    parser.add_argument(
        "--block-size", type=int,
        help="block size in bytes, from the product documentation")
    parser.add_argument(
        "--no-restart", action="store_true",
        help="leave the unit running its old firmware after the transfer")
    args = parser.parse_args()

    if args.image and not args.scan:
        if args.block_size is None:
            parser.error("--block-size is required to transfer an image")
        if args.address is None and not args.broadcast:
            parser.error("--address or --broadcast is required")

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        sys.exit(1)
