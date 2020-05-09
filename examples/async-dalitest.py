#!/usr/bin/env python3

import asyncio
import logging
from dali.address import *
from dali.gear.general import *
from dali.gear import emergency
from dali.gear import led
from dali.sequences import QueryDeviceTypes, DALISequenceError
from dali.driver.hid import tridonic, hasseb

def print_command_and_response(dev, command, response, config_command_error):
    # Note that these will be printed "late" because they are not
    # delivered until main() blocks on its next await call
    if config_command_error:
        print(f"ERROR: failed config command: {command}")
    elif command and not response:
        print(f"{command}")
    else:
        print(f"{command} -> {response}")

async def main(self):
    d = tridonic("/dev/dali/daliusb-*", glob=True, loop=loop)

    # This script fails with the hasseb dali master in several
    # circumstances, for example if any devices are present that have
    # multiple device types.

    #d = hasseb("/dev/dali/hasseb-*", glob=True, loop=loop)

    # Uncomment to show a dump of bus traffic
    #d.bus_traffic.register(print_command_and_response)

    # If there's a problem sending a command, keep trying
    d.exceptions_on_send = False

    d.connect()
    await d.connected.wait()

    for addr in range(0, 64):
        try:
            device_types = await d.run_sequence(QueryDeviceTypes(Short(addr)))
        except DALISequenceError:
            # The device isn't present; skip it
            continue
        print(f"{addr}: {device_types}")

        s = await d.send(QueryStatus(Short(addr)))
        if s.value is not None:
            print(f" -- {s}")
        if 1 in device_types:
            r = await d.send(emergency.QueryEmergencyMode(Short(addr)))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyFeatures(Short(addr)))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyFailureStatus(Short(addr)))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryEmergencyStatus(Short(addr)))
            print(f" -E- {r}")
            r = await d.send(emergency.QueryBatteryCharge(Short(addr)))
            print(f" -E- battery charge: {r}")
            r = await d.send(emergency.QueryRatedDuration(Short(addr)))
            print(f" -E- rated duration: {r} * 2")
        if 6 in device_types:
            r = await d.send(led.QueryGearType(Short(addr)))
            print(f" -LED- {r}")
            r = await d.send(led.QueryDimmingCurve(Short(addr)))
            print(f" -LED- dimming curve: {r.raw_value.as_integer}")
            r = await d.send(led.QueryPossibleOperatingModes(Short(addr)))
            print(f" -LED- {r}")
            r = await d.send(led.QueryFeatures(Short(addr)))
            print(f" -LED- {r}")
            r = await d.send(led.QueryFailureStatus(Short(addr)))
            print(f" -LED- {r}")
            r = await d.send(led.QueryOperatingMode(Short(addr)))
            print(f" -LED- {r}")


    # If we don't sleep here for a moment, the bus_watch task gets
    # killed before it delivers our most recent command.
    await asyncio.sleep(0.1)
    d.disconnect()

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    #loop.set_debug(True)
    loop.run_until_complete(main(loop))
    # The device driver may still be cleaning up from disconnect() -
    # wait for it to finish
    loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
    loop.close()
