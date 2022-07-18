"""
async-serial-luba.py - Example showing the usage of the LUBA driver


This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it under the terms of the GNU
Lesser General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.



This example shows how to use python-dali with a Lunatone RS232 LUBA protocol DALI interface.
LUBA is a protocol defined by Lunatone for use in their devices, they publish the specification on
their website: https://www.lunatone.com/wp-content/uploads/2021/04/LUBA_Protocol_EN.pdf

It is assumed that an appropriate RS232 interface device is connected between the machine running
python-dali and the Lunatone hardware, in writing this example an FTDI USB interface was used but
any other compatible device will also work.
"""
import asyncio
import logging

from dali.address import Broadcast, Short
from dali.driver.serial import DriverLubaRs232
from dali.exceptions import DALISequenceError
from dali.gear.general import DAPC, QueryControlGearPresent
from dali.sequences import QueryDeviceTypes, QueryGroups

# Define the path to the serial RS232 interface. The 'luba232' scheme tells the driver which
# protocol to use - so far only the LUBA protocol is implemented, but others may be added in the
# future
URI = "luba232:/dev/ttyUSB0"


async def listen_luba():
    logger = logging.getLogger("dali")
    log_handler = logging.StreamHandler()
    log_formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s")
    log_formatter.default_msec_format = "%s.%03d"
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel("INFO")

    driver = DriverLubaRs232(uri=URI)
    await driver.connect()

    print("\nSending DAPC(254) to broadcast address")
    await driver.send(DAPC(Broadcast(), 254))
    await asyncio.sleep(1.5)
    print("Sending DAPC(0) to broadcast address\n")
    await driver.send(DAPC(Broadcast(), 0))

    for ad in range(63):
        short = Short(ad)
        rsp = await driver.send(QueryControlGearPresent(short))
        if rsp:
            if rsp.value:
                print(f"\nFound control gear A{ad}")
                try:
                    dts = await driver.run_sequence(
                        QueryDeviceTypes(short), progress=print
                    )
                    print(f"  Device Types: {dts}")
                except DALISequenceError:
                    pass
                try:
                    gps = await driver.run_sequence(QueryGroups(short), progress=print)
                    print(f"  Group Memberships: {list(gps) if gps else 'None'}")
                except DALISequenceError:
                    pass

    print("\nListening for DALI commands on the bus...\n")
    rx_queue = driver.new_dali_rx_queue()
    while True:
        cmd = await rx_queue.get()
        print(cmd)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(listen_luba())
