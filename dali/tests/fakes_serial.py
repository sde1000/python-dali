"""
fakes_serial.py - A mock implementation of a serial driver, for testing without
relying on hardware


This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.



DriverSerialDummy provides a basic mock DALI bus, with fake devices connected to
it. These fake devices can respond to a limited subset of DALI commands - useful
in testing logic of other parts of the library.

DriverSerialDummy instances are created using a path to a file, rather than a
real serial device. This file is used to log all of the DALI commands which
would be sent out over the DALI bus if using a "real" driver. During tests, the
log file can be read to verify the expected command was sent.

Three types of devices are emulated, DT6 LEDs, DT7 relays, and the Lunatone
OEM-specific "Jalousie" relay (used for controlling blinds). The number of each
dummy device to create is specified in a query string, after the path to the
logfile, using the keys 'led', 'relay', and 'cover'.

Example:
```
dummy = DriverSerialDummy(uri="dummy:/tmp/dali0.txt?led=2&cover=2&relay=4")
await dummy.connect()
```
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import ParseResult, parse_qs

from dali import command, gear, memory
from dali.device.helpers import DeviceInstanceTypeMapper
from dali.driver import trace_logging  # noqa: F401
from dali.driver.serial import DistributorQueue, DriverSerialBase
from dali.memory.location import MemoryBank
from dali.tests import fakes as dali_fakes

_LOG = logging.getLogger("dali.driver")


class DriverSerialDummy(DriverSerialBase):
    uri_scheme = "dummy"
    hardware_delay = 0.005

    class DummyBank0(dali_fakes.FakeMemoryBank):
        bank = memory.info.BANK_0
        initial_contents = [
            0x7F,
            None,
            0x00,  # Memory bank 0 is last accessible
            0x01,
            0x1F,
            0x71,
            0xF7,
            0x6B,
            0xB1,  # GTIN 1234567654321
            0x03,
            0x02,  # Firmware version 3.2
            0x00,
            0x00,
            0x00,
            0x00,
            0xAA,
            0xBB,
            0xCC,
            0xFF,  # Serial number
            0x02,
            0x01,  # Hardware version 2.1
            0x08,
            0x08,  # Parts 101 and 102 version 2.0
            0xFF,  # Part 103 not implemented
            0x00,  # 0 logical control device units
            0x01,  # 1 logical control gear unit
            0x00,  # This is control gear unit index 0
        ]

    class DummyJalousieBank0(dali_fakes.FakeMemoryBank):
        bank = MemoryBank(0, 0x10, has_lock=False)
        initial_contents = [
            0x7F,
            None,
            0x02,  # Memory bank 2 is last accessible
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # GTIN 0 (for some reason Lunatone don't support this)
            0x02,
            0x04,  # Firmware version 2.4
            0xCC,
            0xBB,
            0xAA,
            0x00,  # Serial number
            0x01,  # Gear Unit Count
            0x01,  # Gear Unit Index
            0x00,
            0x00,
            0x02,
            0x01,  # Hardware version 2.1
            0x08,
            0x01,  # The Jalousie uses DALI-1
            0x00,
        ]

    class DummyJalousieBank2(dali_fakes.FakeMemoryBank):
        bank = MemoryBank(2, 0x22, has_lock=False)
        initial_contents = [
            34,  # Length of memory bank
            None,
            None,
            76,  # Seems like this is the Lunatone DALI-1 identifier
            117,
            110,
            97,
            116,
            111,
            110,
            101,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            5,  # Specific part ID for Jalousie
            39,
            65,
            52,
            None,
        ]

    def __init__(
        self,
        uri: str | ParseResult,
        dev_inst_map: Optional[DeviceInstanceTypeMapper] = None,
    ):
        """
        The DriverSerialDummy class will 'magically' create pretend devices,
        based on the query string passed in through the URI. These dummy devices
        won't physically exist, but do provide a way of testing higher-level
        functions without needing physical hardware. Any interactions that would
        be sent to hardware are instead written to a logfile, created locally at
        the path provided in the URI.

        :param uri: A special URI (either string or ParseResult object) which
        tells the dummy driver where to save its logfile, and how many dummy
        devices to create.
        URI format example: "dummy:///path/to/logfile?led=4&cover=2&relay=2"
        """
        super().__init__(uri=uri, dev_inst_map=dev_inst_map)
        uri = self.uri

        self._log_path = uri.path
        query = parse_qs(uri.query, strict_parsing=True)
        self._num_leds = 0
        try:
            self._num_leds = int(query["led"][0])
        except (IndexError, KeyError):
            _LOG.info(f"URI query does not specify any LEDs: '{uri.query}'")
        self._num_covers = 0
        self._cover_addrs: set[int] = set()
        try:
            self._num_covers = int(query["cover"][0])
        except (IndexError, KeyError):
            _LOG.info(f"URI query does not specify any Covers: '{uri.query}'")
        self._num_relays = 0
        try:
            self._num_relays = int(query["relay"][0])
        except (IndexError, KeyError):
            _LOG.info(f"URI query does not specify any Relays: '{uri.query}'")

        _LOG.debug(
            f"Initialising dummy driver with logfile path '{self._log_path}'"
        )
        _LOG.info(
            f"Dummy instances to be created: {self._num_leds} LEDs, "
            f"{self._num_covers} covers, {self._num_relays} relays"
        )

        # Create dummy 'devices'. All are addressed sequentially.
        self._dummy_bus = dali_fakes.Bus([])
        new_ad = 0
        for _ in range(self._num_leds):
            self._dummy_bus.gear.append(
                dali_fakes.Gear(
                    new_ad,
                    devicetypes=[8],
                    memory_banks=(DriverSerialDummy.DummyBank0,),
                )
            )
            # Force the LSB of the device serial number to equal the address
            self._dummy_bus.gear[new_ad].memory_banks[0].contents[18] = new_ad
            new_ad += 1
        for _ in range(self._num_covers):
            new_cover = dali_fakes.Gear(
                new_ad,
                devicetypes=[0],
                memory_banks=(
                    DriverSerialDummy.DummyJalousieBank0,
                    DriverSerialDummy.DummyJalousieBank2,
                ),
            )
            # Emulating a Lunatone Jalousie, which uses scenes to control
            # movement up/down
            new_cover.scenes[1] = 254
            new_cover.scenes[3] = 253
            # The serial number has a different address for DALI-1 (0x0E
            # instead of 0x12)
            new_cover.memory_banks[0].contents[0x0E] = new_ad
            self._dummy_bus.gear.append(new_cover)
            # Keep track of addresses belonging to covers, for special handling
            self._cover_addrs.add(new_ad)
            new_ad += 1
        for _ in range(self._num_relays):
            self._dummy_bus.gear.append(
                dali_fakes.Gear(
                    new_ad,
                    devicetypes=[7],
                    memory_banks=(DriverSerialDummy.DummyBank0,),
                )
            )
            # Force the LSB of the device serial number to equal the address
            self._dummy_bus.gear[new_ad].memory_banks[0].contents[18] = new_ad
            new_ad += 1

        if new_ad >= 64:
            raise RuntimeError("Cannot have more than 64 devices on a DALI bus")

    @staticmethod
    def _get_date() -> str:
        return datetime.now().isoformat()

    def _set_level_off(self, addr: int):
        _LOG.info(f"Turning off A{addr}")
        self._dummy_bus.gear[addr].level = 0

    async def connect(self, *, scan_dev_inst: bool = False) -> None:
        if self.is_connected:
            _LOG.warning(
                "'connect()' called but dummy driver already connected"
            )
            return
        # The dummy driver doesn't actually do any real communication, all we
        # need to do is check that the path we've been given can be opened
        with open(self._log_path, mode="wt", encoding="utf-8") as log_file:
            log_file.write(
                f"\n{self._get_date()} Starting new DriverSerialDummy instance\n"
            )
        # The file will be automatically closed after the write is done, it's
        # not quite as efficient as it could be to open it each time, but it's
        # a bit safer and ensures a clean write

        self._connected.set()

        # Scan the bus for control devices, and create a mapping of addresses
        # to instance types
        if scan_dev_inst:
            _LOG.info("Scanning DALI bus for control devices")
            await self.run_sequence(self.dev_inst_map.autodiscover())
            _LOG.info(f"Found {len(self.dev_inst_map.mapping)} instances")

    async def send(
        self, msg: command.Command, in_transaction: bool = False
    ) -> Optional[command.Response]:
        """
        The 'send()' method for the DriverSerialDummy class doesn't actually
        communicate with anything external - it just tries to imitate hardware,
        at a very basic level. For now, all that is implemented is:
        * Short addressing (i.e. referring to a dummy directly by its address)
        * Broadcast addressing
        * Brightness/Power Level (DAPC, RecallMaxLevel, RecallMinLevel, Off)
        * Device Type

        :param msg: The DALI message to send
        :param in_transaction: Flag whether or not this 'send()' call is part
        of a transaction (i.e. if this call is coming from the 'run_sequence()'
        method). If the flag is set then the lock will not be acquired before
        sending.
        :return: If a command being sent expects a response, and the type is
        supported by DriverSerialDummy, then it will be returned by the 'send()'
        call. If more than one command generates a response then only the last
        response will be returned. Otherwise, None.
        """
        # Only send if the driver is connected
        if not self.is_connected:
            _LOG.critical(f"Cannot send, driver is not connected: {self}")
            raise IOError("Cannot send, driver is not connected")

        # If multiple responses are requested in a list of messages to send,
        # only the last response will be returned
        response = None

        # "Send" each message, one at a time, and figure out what the dummy
        # response should be
        if not in_transaction:
            await self.transaction_lock.acquire()
        try:
            with open(self._log_path, mode="at", encoding="utf-8") as log_file:
                # Write the message to the log file, emulating sending it over
                # a DALI bus
                log_file.write(f"{self._get_date()} {msg}\n")
                # Because writing to a log file is much faster than writing
                # over RS232, there is a short delay here to make the dummy act
                # a bit more like a real DALI device
                await asyncio.sleep(DriverSerialDummy.hardware_delay)
                # Get the response from the dummy bus
                response = self._dummy_bus.send(msg)

                # Special handling for a Lunatone Jalousie dummy device
                if hasattr(msg, "destination"):
                    if hasattr(msg.destination, "address"):
                        if isinstance(msg, gear.general.GoToScene):
                            dst = msg.destination.address
                            if dst in self._cover_addrs:
                                _LOG.info(
                                    f"Scheduling dummy call to turn off A{dst}"
                                )
                                asyncio.get_running_loop().call_later(
                                    delay=10.0,
                                    callback=lambda: self._set_level_off(
                                        addr=dst
                                    ),
                                )

        finally:
            if not in_transaction:
                self.transaction_lock.release()

        return response

    def new_dali_rx_queue(self) -> DistributorQueue:
        _LOG.warning(
            "'new_dali_rx_queue()' called on DriverSerialDummy, beware this "
            "will always be empty!"
        )
        return DistributorQueue()
