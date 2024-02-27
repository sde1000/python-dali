#!/usr/bin/env python3

from dali.gear.general import (
    DAPC,
    QueryControlGearPresent,
    QueryGroupsZeroToSeven,
    QueryGroupsEightToFifteen,
    QueryActualLevel,
    Off,
    QueryMinLevel,
    QueryMaxLevel,
    QueryPhysicalMinimum,
)
from dali.driver.base import SyncDALIDriver
from dali.driver.atxled import SyncDaliHatDriver
from dali.address import GearShort

import logging


LOG = logging.getLogger("DaliHatTest")

class DaliHatTest:
    def __init__(self, driver: SyncDALIDriver):
        self.driver = driver

    def scan_devices(self):
        present_devices = []
        for address in range(0, 64):
            try:
                response = self.driver.send(QueryControlGearPresent(GearShort(address)))
                if response.value is True:
                    present_devices.append(address)
                    LOG.info(f"Device found at address: {address}")
                else:
                    LOG.info(f"Response from address {address}: {response.value}")

            except Exception as e:
                LOG.info(f"Error while querying address {address}: {e}")

        return present_devices

    def set_device_level(self, address, level, fade_time=0):
        try:
            self.driver.send(DAPC(GearShort(address), level))
            LOG.info(
                f"Set device at address {address} to level {level} with fade time {fade_time}"
            )
        except Exception as e:
            LOG.info(f"Error while setting level for address {address}: {e}")

    def query_device_info(self, address):
        current_command = None
        try:
            current_command = "QueryGroupsZeroToSeven"
            groups_0_7 = self.driver.send(
                QueryGroupsZeroToSeven(GearShort(address))
            ).value
            LOG.info(f"Device {address} groups 0-7: {groups_0_7}")

            current_command = "QueryGroupsEightToFifteen"
            groups_8_15 = self.driver.send(
                QueryGroupsEightToFifteen(GearShort(address))
            ).value
            LOG.info(f"Device {address} groups 8-15: {groups_8_15}")

            current_command = "QueryMinLevel"
            min_level = self.driver.send(QueryMinLevel(GearShort(address))).value
            LOG.info(f"Device {address} minimum level: {min_level}")

            current_command = "QueryMaxLevel"
            max_level = self.driver.send(QueryMaxLevel(GearShort(address))).value
            LOG.info(f"Device {address} maximum level: {max_level}")

            current_command = "QueryPhysicalMinimum"
            physical_minimum = self.driver.send(
                QueryPhysicalMinimum(GearShort(address))
            ).value
            LOG.info(f"Device {address} physical minimum: {physical_minimum}")

            current_command = "QueryActualLevel"
            actual_level = self.driver.send(QueryActualLevel(GearShort(address))).value
            LOG.info(f"Device {address} actual level: {actual_level}")

        except Exception as e:
            LOG.info(
                f"Error while querying device {address} with command '{current_command}': {e}"
            )

    def turn_off_device(self, address):
        try:
            self.driver.send(Off(GearShort(address)))
            LOG.info(f"Turned off device at address {address}")
        except Exception as e:
            LOG.info(f"Error while turning off device {address}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dali_driver = SyncDaliHatDriver()

    dali_test = DaliHatTest(dali_driver)
    found_devices = []

    found_devices = dali_test.scan_devices()
    LOG.info(f"Scanned and found {len(found_devices)} devices.")

    for device in found_devices:
        dali_test.query_device_info(device)
        dali_test.set_device_level(device, 128)
        dali_test.turn_off_device(device)

    dali_driver.close()
