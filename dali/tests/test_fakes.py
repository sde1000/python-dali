import unittest

from dali.tests import fakes
from dali import command, gear, device
from dali.address import DeviceShort, GearShort, GearBroadcast, InstanceNumber
from dali.gear.colour import QueryColourValueDTR
from dali.gear.sequences import SetDT8ColourValueTc, QueryDT8ColourValue


class TestFakeGear(unittest.TestCase):
    def setUp(self):
        """
        Creates four fake control gears, with addresses 0 to 3. Also has a
        control device, just there to make sure it stays silent.
        """
        self.bus = fakes.Bus(
            [
                fakes.Gear(GearShort(0), memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(GearShort(1), memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(GearShort(2), memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(GearShort(3), memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(
                    GearShort(4),
                    devicetypes=[8],
                    memory_banks=(fakes.FakeBank0,),
                ),
                fakes.Device(DeviceShort(0), memory_banks=(fakes.FakeBank0,)),
            ]
        )

    def test_fake_gear_dapc(self):
        # The level should initialise to 0
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 0)
        self.bus.send(gear.general.DAPC(GearShort(0), 128))
        # After DAPC the level should be 128
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 128)

    def test_fake_gear_recall_max(self):
        # The level should initialise to 0
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 0)
        self.bus.send(gear.general.RecallMaxLevel(GearShort(0)))
        # After RecallMaxLevel the level should be 254
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 254)

    def test_fake_gear_recall_min(self):
        # The level should initialise to 0
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 0)
        self.bus.send(gear.general.RecallMinLevel(GearShort(1)))
        # After RecallMaxLevel the level should be 1
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 1)

    def test_fake_gear_set_min(self):
        # Start with a level of 12
        self.bus.send(gear.general.DAPC(GearShort(0), 12))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 12)
        # Set minimum level to 22
        self.bus.send(gear.general.DTR0(22))
        self.bus.send(gear.general.SetMinLevel(GearShort(0)))
        # After SetMinLevel the level should be 22
        resp = self.bus.send(gear.general.QueryMinLevel(GearShort(0)))
        self.assertEqual(resp.value, 22)
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 22)
        # Level should not go below 22
        self.bus.send(gear.general.DAPC(GearShort(0), 12))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 22)

    def test_fake_gear_set_max(self):
        # Start with a level of 228
        self.bus.send(gear.general.DAPC(GearShort(1), 228))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 228)
        # Set maximum to 191
        self.bus.send(gear.general.DTR0(191))
        self.bus.send(gear.general.SetMaxLevel(GearShort(1)))
        # After SetMaxLevel the level should be 191
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 191)
        resp = self.bus.send(gear.general.QueryMaxLevel(GearShort(1)))
        self.assertEqual(resp.value, 191)
        # Level should not go above 191
        self.bus.send(gear.general.DAPC(GearShort(1), 228))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 191)

    def test_fake_gear_set_min_above_max(self):
        self.bus.send(gear.general.DTR0(188))
        self.bus.send(gear.general.SetMaxLevel(GearShort(0)))
        resp = self.bus.send(gear.general.QueryMinLevel(GearShort(0)))
        self.assertEqual(resp.value, 1)
        # Trying to set the minimum to larger than the maximum should result
        # in the minimum being set the same as the maximum
        self.bus.send(gear.general.DTR0(200))
        self.bus.send(gear.general.SetMinLevel(GearShort(0)))
        resp = self.bus.send(gear.general.QueryMinLevel(GearShort(0)))
        self.assertEqual(resp.value, 188)

    def test_fake_gear_set_max_below_min(self):
        self.bus.send(gear.general.DTR0(188))
        self.bus.send(gear.general.SetMinLevel(GearShort(0)))
        # Trying to set the maximum to less than the minimum should result in
        # the maximum being set the same as the minimum
        self.bus.send(gear.general.DTR0(127))
        self.bus.send(gear.general.SetMaxLevel(GearShort(0)))
        resp = self.bus.send(gear.general.QueryMaxLevel(GearShort(0)))
        self.assertEqual(resp.value, 188)

    def test_fake_gear_set_scene(self):
        # Initially all scenes are MASK
        resp = self.bus.send(gear.general.QuerySceneLevel(GearShort(0), 0))
        self.assertEqual(resp.value, "MASK")
        # Set some scene values
        self.bus.send(gear.general.DTR0(132))
        self.bus.send(gear.general.SetScene(GearShort(0), 0))
        self.bus.send(gear.general.DTR0(143))
        self.bus.send(gear.general.SetScene(GearShort(1), 0))
        self.bus.send(gear.general.DTR0(154))
        self.bus.send(gear.general.SetScene(GearShort(2), 0))
        self.bus.send(gear.general.DTR0(165))
        self.bus.send(gear.general.SetScene(GearShort(3), 0))
        # Outputs should be off
        for ad in range(0, 4):
            resp = self.bus.send(gear.general.QueryActualLevel(GearShort(ad)))
            self.assertEqual(resp.value, 0)
        # Activate the scene via broadcast
        self.bus.send(gear.general.GoToScene(GearBroadcast(), 0))
        # Outputs should be on now
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 132)
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(1)))
        self.assertEqual(resp.value, 143)
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(2)))
        self.assertEqual(resp.value, 154)
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(3)))
        self.assertEqual(resp.value, 165)

    def test_fake_gear_set_off(self):
        # Set a higher minimum value
        self.bus.send(gear.general.DTR0(22))
        self.bus.send(gear.general.SetMinLevel(GearShort(0)))
        self.bus.send(gear.general.DAPC(GearShort(0), 10))
        # Ensure minimum level
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 22)
        # Ensure DAPC of 0 still works
        self.bus.send(gear.general.DAPC(GearShort(0), 0))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 0)
        # Ensure Off works
        self.bus.send(gear.general.DAPC(GearShort(0), 10))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 22)
        self.bus.send(gear.general.Off(GearShort(0)))
        resp = self.bus.send(gear.general.QueryActualLevel(GearShort(0)))
        self.assertEqual(resp.value, 0)

    def test_fake_gear_dt8_extended_version(self):
        # Address 4 is a DT8 gear, it should respond
        resp = self.bus.send(
            gear.colour.QueryExtendedVersionNumber(GearShort(4))
        )
        self.assertIsInstance(resp, command.NumericResponse)
        self.assertEqual(resp.value, 2)
        # Address 0 is not, it should ignore this command
        resp = self.bus.send(
            gear.colour.QueryExtendedVersionNumber(GearShort(0))
        )
        self.assertIsInstance(resp, command.NumericResponse)
        self.assertIsNone(resp.raw_value)

    def test_fake_gear_dt8_tc_limits(self):
        addr = GearShort(4)

        resp = self.bus.run_sequence(
            QueryDT8ColourValue(
                addr, QueryColourValueDTR.ColourTemperatureTcWarmest
            )
        )
        self.assertEqual(resp, 370)

        resp = self.bus.run_sequence(
            QueryDT8ColourValue(
                addr, QueryColourValueDTR.ColourTemperatureTcCoolest
            )
        )
        self.assertEqual(resp, 153)

    def test_fake_gear_dt8_tc_set(self):
        addr = GearShort(4)

        self.bus.run_sequence(SetDT8ColourValueTc(addr, 202))

        resp = self.bus.run_sequence(
            QueryDT8ColourValue(
                addr, QueryColourValueDTR.ReportColourTemperatureTc
            )
        )
        self.assertEqual(resp, 202)


class TestFakeDevice(unittest.TestCase):
    def setUp(self):
        """
        Creates four fake devices, with addresses 0 to 3.
        """
        self.bus = fakes.Bus(
            [
                fakes.Device(
                    DeviceShort(0), memory_banks=(fakes.FakeDeviceBank0,)
                ),
                fakes.Device(
                    DeviceShort(1), memory_banks=(fakes.FakeDeviceBank0,)
                ),
                fakes.Device(
                    DeviceShort(2), memory_banks=(fakes.FakeDeviceBank0,)
                ),
                fakes.Device(
                    DeviceShort(3), memory_banks=(fakes.FakeDeviceBank0,)
                ),
            ]
        )

    def test_fake_device_dtr012(self):
        self.bus.send(device.general.DTR0(128))
        self.bus.send(device.general.DTR1(1))
        resp = self.bus.send(device.general.DTR2(254))
        self.assertIsNone(resp)
        for addr_int in range(3):
            addr = DeviceShort(addr_int)
            resp = self.bus.send(device.general.QueryContentDTR0(addr))
            self.assertEqual(resp.value, 128)
            resp = self.bus.send(device.general.QueryContentDTR1(addr))
            self.assertEqual(resp.value, 1)
            resp = self.bus.send(device.general.QueryContentDTR2(addr))
            self.assertEqual(resp.value, 254)

    def test_fake_device_status(self):
        for addr_int in range(3):
            # Make sure QueryDeviceStatus works as expected
            resp = self.bus.send(
                device.general.QueryDeviceStatus(DeviceShort(addr_int))
            )
            self.assertIsInstance(
                resp, device.general.QueryDeviceStatusResponse
            )
            # Make sure each device has four instances which respond as expected
            for inst_num in range(4):
                resp = self.bus.send(
                    device.general.QueryInstanceEnabled(
                        DeviceShort(addr_int), InstanceNumber(inst_num)
                    )
                )
                self.assertIsInstance(resp, command.YesNoResponse)
                self.assertTrue(resp.value)


if __name__ == "__main__":
    unittest.main()
