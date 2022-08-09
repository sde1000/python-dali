"""
test_dummy.py - A pytest test suite for the 'dummy' serial driver class


This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import os.path
from typing import NamedTuple

import py
import pytest

from dali.driver.serial import DriverSerialBase, DriverLubaRs232, drivers_map
from dali.tests.fakes_serial import DriverSerialDummy
from dali import address, gear
from dali.sequences import QueryDeviceTypes


class DummyDriverFixtureParts(NamedTuple):
    # The type hint for 'log' seems odd, but is correct - refer to this doc
    # page:
    # https://docs.pytest.org/en/latest/reference/reference.html?highlight=tmpdir#tmpdir
    log: py._path.local.LocalPath
    uri: str
    driver: DriverSerialDummy


@pytest.fixture
def make_dummy_driver(tmpdir):
    """
    A test fixture for creating an instance of a dummy driver
    """

    def _dummy_driver(
        suffix: str = "0", led: int = 6, cover: int = 4, relay: int = 2
    ) -> DummyDriverFixtureParts:
        log = tmpdir.join(f"dummylog_{suffix}.txt")
        uri = f"dummy://{log}?led={led}&cover={cover}&relay={relay}"
        driver = DriverSerialDummy(uri=uri)

        return DummyDriverFixtureParts(log=log, uri=uri, driver=driver)

    return _dummy_driver


@pytest.fixture
def dummy_driver(make_dummy_driver) -> DummyDriverFixtureParts:
    """
    A test fixture that creates a basic instance of a test driver,
    using make_dummy_driver
    """
    return make_dummy_driver()


def test_base_init_block():
    """
    Makes sure that the DriverSerialBase class cannot be initialised as a
    standalone object. It needs to be used as a subclass.
    """
    with pytest.raises(RuntimeError):
        DriverSerialBase(uri="")


def test_drivers_map():
    """
    Tests the mapping from URI schemes to driver classes
    """
    drivers = drivers_map()
    assert drivers["dummy"] == DriverSerialDummy
    assert drivers["luba232"] == DriverLubaRs232


def test_dummy_init_good(tmp_path):
    """
    Tests a dummy driver is initialised with the correct dummy devices
    """
    log = os.path.join(tmp_path, "dummylog.txt")
    test_uri = f"dummy://{log}?led=2&cover=2&relay=4"
    dummy_driver = DriverSerialDummy(uri=test_uri)

    assert dummy_driver._num_leds == 2
    assert dummy_driver._num_covers == 2
    assert dummy_driver._num_relays == 4


def test_dummy_init_bad_scheme(tmp_path):
    """
    Tests a dummy driver cannot be initialised with a bad URI scheme
    """
    log = os.path.join(tmp_path, "dummylog.txt")
    test_uri = f"dmy://{log}?led=2&cover=2&relay=4"
    with pytest.raises(TypeError):
        DriverSerialDummy(uri=test_uri)


def test_dummy_init_no_led(tmp_path):
    """
    Tests a dummy driver can be initialised without any dummy LEDs
    """
    log = os.path.join(tmp_path, "dummylog.txt")
    test_uri = f"dummy://{log}logfile?cover=2&relay=4"
    dummy_driver = DriverSerialDummy(uri=test_uri)

    assert dummy_driver._num_leds == 0
    assert dummy_driver._num_covers == 2
    assert dummy_driver._num_relays == 4


def test_dummy_init_no_cover(tmp_path):
    """
    Tests a dummy driver can be initialised without any dummy covers
    """
    log = os.path.join(tmp_path, "dummylog.txt")
    test_uri = f"dummy://{log}?led=2&relay=4"
    dummy_driver = DriverSerialDummy(uri=test_uri)

    assert dummy_driver._num_leds == 2
    assert dummy_driver._num_covers == 0
    assert dummy_driver._num_relays == 4


def test_dummy_init_no_relay(tmp_path):
    """
    Tests a dummy driver can be initialised without any dummy relays
    """
    log = os.path.join(tmp_path, "dummylog.txt")
    test_uri = f"dummy://{log}?cover=2&led=4"
    dummy_driver = DriverSerialDummy(uri=test_uri)

    assert dummy_driver._num_leds == 4
    assert dummy_driver._num_covers == 2
    assert dummy_driver._num_relays == 0


@pytest.mark.asyncio
async def test_dummy_write_1(dummy_driver):
    await dummy_driver.driver.connect()
    await dummy_driver.driver.send(gear.general.DAPC(address.GearShort(1), 254))
    assert "ArcPower(<address (control gear) 1>,254)" in dummy_driver.log.read()


@pytest.mark.asyncio
async def test_dummy_write_2(dummy_driver):
    await dummy_driver.driver.connect()
    await dummy_driver.driver.send(
        gear.general.DAPC(address.GearBroadcast(), 127)
    )
    assert "ArcPower(<broadcast (control gear)>,127)" in dummy_driver.log.read()


@pytest.mark.asyncio
async def test_dummy_write_3(dummy_driver):
    await dummy_driver.driver.connect()
    await dummy_driver.driver.send(
        gear.general.GoToScene(address.GearShort(1), 11)
    )
    assert "GoToScene(<address (control gear) 1>,11)" in dummy_driver.log.read()


@pytest.mark.asyncio
async def test_dummy_sequence_device_types(dummy_driver):
    await dummy_driver.driver.connect()
    # The default of dummy_driver has 12 addressed control gears
    for ad in range(11):
        short = address.GearShort(ad)
        dev_types = await dummy_driver.driver.run_sequence(
            QueryDeviceTypes(short)
        )
        # Colour Temperature LEDs, DT8, are created first by the dummy driver
        if ad in range(0, 5):
            assert len(dev_types) == 1
            assert dev_types[0] == 8
        # Next is the custom Lunatone Jalousie cover, DT0
        elif ad in range(6, 9):
            assert len(dev_types) == 1
            assert dev_types[0] == 0
        # Finally the relays, DT7, are created
        elif ad in range(10, 11):
            assert len(dev_types) == 1
            assert dev_types[0] == 7
