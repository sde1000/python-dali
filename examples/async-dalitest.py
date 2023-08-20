#!/usr/bin/env python3

import asyncio
import logging
from dali.address import GearShort, GearBroadcast, \
    DeviceShort, DeviceBroadcast, InstanceNumber
import dali.gear.general as gg
import dali.device.general as dg
import dali.device.sequences as ds
from dali.gear import emergency
from dali.gear import led
from dali.sequences import QueryDeviceTypes, DALISequenceError
from dali.driver.hid import tridonic, hasseb
from dali.memory import *

def print_command_and_response(dev, command, response, config_command_error):
    # Note that these will be printed "late" because they are not
    # delivered until main() blocks on its next await call
    if config_command_error:
        print(f"ERROR: failed config command: {command}")
    elif command and not response:
        print(f"{command}")
    else:
        print(f"{command} -> {response}")

async def scan_control_gear(d):
    for addr in (GearShort(x) for x in range(64)):
        try:
            device_types = await d.run_sequence(QueryDeviceTypes(addr))
        except DALISequenceError:
            # The device isn't present; skip it
            continue
        print(f"{addr}: {device_types}")

        s = await d.send(gg.QueryStatus(addr))
        if s.value is not None:
            print(f" -- {s}")
        if 1 in device_types:
            r = await d.send(emergency.QueryEmergencyMode(addr))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyFeatures(addr))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyFailureStatus(addr))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyStatus(addr))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryBatteryCharge(addr))
            print(f" -E- battery charge: {r}")
            r = await d.send(emergency.QueryRatedDuration(addr))
            print(f" -E- rated duration: {r} * 2")
        if 6 in device_types:
            r = await d.send(led.QueryGearType(addr))
            print(f" -LED- {r}")
            r = await d.send(led.QueryDimmingCurve(addr))
            print(f" -LED- dimming curve: {r.raw_value.as_integer}")
            r = await d.send(led.QueryPossibleOperatingModes(addr))
            print(f" -LED- {r}")
            r = await d.send(led.QueryFeatures(addr))
            print(f" -LED- {r}")
            r = await d.send(led.QueryFailureStatus(addr))
            print(f" -LED- {r}")
            r = await d.send(led.QueryOperatingMode(addr))
            print(f" -LED- {r}")
        # Read memory banks
        v = await d.send(gg.QueryVersionNumber(addr))
        bank0 = info.BANK_0_legacy if v.value == 1 else info.BANK_0
        for b in (bank0, oem.BANK_1, energy.BANK_202,
                  energy.BANK_203, energy.BANK_204,
                  diagnostics.BANK_205, diagnostics.BANK_206,
                  maintenance.BANK_207):
            try:
                r = await d.run_sequence(b.read_all(addr))
            except location.MemoryLocationNotImplemented:
                continue
            print(f" -MEM- Bank {b.address}: {r}")

async def scan_control_devices(d):
    for addr in (DeviceShort(x) for x in range(64)):
        s = await d.send(dg.QueryDeviceStatus(addr))
        if s.raw_value is None:
            continue
        print(f"{addr}: {s}")
        print(f" -- capabilities: {await d.send(dg.QueryDeviceCapabilities(addr))}")
        instances = await d.send(dg.QueryNumberOfInstances(addr))
        print(f" -- instances: {instances}")
        for instance in (InstanceNumber(x) for x in range(instances.value)):
            print(f" -{instance}- enabled: {await d.send(dg.QueryInstanceEnabled(addr, instance))}")
            print(f" -{instance}- type: {await d.send(dg.QueryInstanceType(addr, instance))}")
            resolution = await d.send(dg.QueryResolution(addr, instance))
            print(f" -{instance}- resolution: {resolution}")
            print(f" -{instance}- value: {await d.run_sequence(ds.query_input_value(addr, instance, resolution.value))}")
            print(f" -{instance}- feature type: {await d.send(dg.QueryFeatureType(addr, instance))}")
        #for b in (info.BANK_0, oem.BANK_1):
        #    try:
        #        r = await d.run_sequence(b.read_all(addr))
        #    except location.MemoryLocationNotImplemented:
        #        continue
        #    print(f" -MEM- Bank {b.address}: {r}")


async def main():
    d = tridonic("/dev/dali/daliusb-*", glob=True)

    # This script fails with the hasseb dali master in several
    # circumstances, for example if any devices are present that have
    # multiple device types.

    # d = hasseb("/dev/dali/hasseb-*", glob=True)

    # Uncomment to show a dump of bus traffic
    # d.bus_traffic.register(print_command_and_response)

    # If there's a problem sending a command, keep trying
    d.exceptions_on_send = False

    d.connect()
    await d.connected.wait()

    # Is any control gear present?
    #gp = await d.send(gg.QueryControlGearPresent(GearBroadcast()))
    #if gp.value:
    #    await scan_control_gear(d)

    # Control devices present?
    dc = await d.send(dg.QueryDeviceCapabilities(DeviceBroadcast()))
    if dc.raw_value is not None:
        await scan_control_devices(d)

    # If we don't sleep here for a moment, the bus_watch task gets
    # killed before it delivers our most recent command.
    await asyncio.sleep(0.1)
    d.disconnect()

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
