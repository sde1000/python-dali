#!/usr/bin/env python3

import asyncio
import logging
import sys

from dali.address import GearGroup, GearShort
from dali.gear.colour import tc_kelvin_mirek, QueryColourValueDTR, QueryColourStatus, StoreColourTemperatureTcLimitDTR2
from dali.gear.general import QueryControlGearPresent, QueryActualLevel
from dali.gear.led import QueryDimmingCurve
from dali.gear.sequences import SetDT8ColourValueTc, SetDT8TcLimit, QueryDT8ColourValue
from dali.driver.hid import tridonic, hasseb
from dali.sequences import QueryDeviceTypes, DALISequenceError

def print_command_and_response(dev, command, response, config_command_error):
    # Note that these will be printed "late" because they are not
    # delivered until main() blocks on its next await call
    if config_command_error:
        print(f"ERROR: failed config command: {command}")
    elif command and not response:
        print(f"{command}")
    else:
        print(f"{command} -> {response}")

def show_usage():
    print(f'Usage: {sys.argv[0]} "show-all-gear" ["detailed"]')
    print(f'       {sys.argv[0]} ("address" / "group") <number> ("tc" / "physical-cool" / "physical-warm" / "cool" / "warm") <Tc>')
    sys.exit(1)

async def scan_control_gear(d, detailed):
    for addr in (GearShort(x) for x in range(64)):
        try:
            device_types = await d.run_sequence(QueryDeviceTypes(addr))
        except DALISequenceError:
            continue

        if 6 in device_types:
            curve = await d.send(QueryDimmingCurve(addr))
            arc_raw = await d.send(QueryActualLevel(addr))
            if curve.raw_value.as_integer == 0:
                if arc_raw.value >= 1:
                    arc_power = 10 ** (((arc_raw.value-1)/(253/3))-1)
                else:
                    arc_power = 0
            elif curve.raw_value.as_integer == 1:
                arc_power = arc_raw.value / 254
            else:
                arc_power = None

        if 8 in device_types:
            colour_status = await d.send(QueryColourStatus(addr))
            if colour_status.colour_type_colour_temperature_Tc_active:
                tc = await d.run_sequence(QueryDT8ColourValue(address=addr, query=QueryColourValueDTR.ColourTemperatureTC))
                if detailed:
                    tc_coolest = await d.run_sequence(QueryDT8ColourValue(address=addr, query=QueryColourValueDTR.ColourTemperatureTcCoolest))
                    tc_physical_coolest = await d.run_sequence(QueryDT8ColourValue(address=addr, query=QueryColourValueDTR.ColourTemperatureTcPhysicalCoolest))
                    tc_warmest = await d.run_sequence(QueryDT8ColourValue(address=addr, query=QueryColourValueDTR.ColourTemperatureTcWarmest))
                    tc_physical_warmest = await d.run_sequence(QueryDT8ColourValue(address=addr, query=QueryColourValueDTR.ColourTemperatureTcPhysicalWarmest))
                    tc_detailed_info = f" ({tc_kelvin_mirek(tc_warmest)}-{tc_kelvin_mirek(tc_coolest)}K, physical {tc_kelvin_mirek(tc_physical_warmest)}-{tc_kelvin_mirek(tc_physical_coolest)}K)"
                else:
                    tc_detailed_info = ""
                print(f"{addr}: {arc_power:.01f}%, Tc {tc_kelvin_mirek(tc)}K{tc_detailed_info}")

async def main():
    # d = tridonic("/dev/dali/daliusb-*", glob=True)
    d = hasseb("/dev/dali/hasseb-*", glob=True)

    if len(sys.argv) < 2:
        show_usage()

    if sys.argv[1] == 'show-all-gear':
        mode = 'show-all-gear'
        if len(sys.argv) >= 3 and sys.argv[2] == 'detailed':
            detailed = True
        else:
            detailed = False
    else:
        mode = None
        if len(sys.argv) < 4:
            show_usage()

        if sys.argv[1] == 'address':
            address = GearShort(int(sys.argv[2]))
        elif sys.argv[1] == 'group':
            address = GearGroup(int(sys.argv[2]))
        else:
            show_usage()

        if sys.argv[3] == 'physical-cool':
            setting_a_limit = StoreColourTemperatureTcLimitDTR2.TcPhysicalCoolest
        elif sys.argv[3] == 'physical-warm':
            setting_a_limit = StoreColourTemperatureTcLimitDTR2.TcPhysicalWarmest
        elif sys.argv[3] == 'cool':
            setting_a_limit = StoreColourTemperatureTcLimitDTR2.TcCoolest
        elif sys.argv[3] == 'warm':
            setting_a_limit = StoreColourTemperatureTcLimitDTR2.TcWarmest
        elif sys.argv[3] == 'tc':
            setting_a_limit = None
        else:
            show_usage()
        desired_kelvin = int(sys.argv[4])
        tc_mired = tc_kelvin_mirek(desired_kelvin)

    # Uncomment to show a dump of bus traffic
    # d.bus_traffic.register(print_command_and_response)

    # If there's a problem sending a command, keep trying
    d.exceptions_on_send = False

    d.connect()
    await d.connected.wait()

    if mode == 'show-all-gear':
        await scan_control_gear(d, detailed)
    else:
        if setting_a_limit is not None:
            command = SetDT8TcLimit(address=address, what_limit=setting_a_limit, tc_mired=tc_mired)
        else:
            command = SetDT8ColourValueTc(address=address, tc_mired=tc_mired)
        await d.run_sequence(command)

    # If we don't sleep here for a moment, the bus_watch task gets
    # killed before it delivers our most recent command.
    await asyncio.sleep(0.1)
    d.disconnect()

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
