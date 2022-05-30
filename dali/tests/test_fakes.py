import unittest

from dali.tests import fakes
from dali import address
from dali.gear import general


class TestFakeGear(unittest.TestCase):
    def setUp(self):
        """
        Creates four fake devices, with addresses 0 to 3.
        """
        self.bus = fakes.Bus(
            [
                fakes.Gear(0, memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(1, memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(2, memory_banks=(fakes.FakeBank0,)),
                fakes.Gear(3, memory_banks=(fakes.FakeBank0,)),
            ]
        )

    def test_fake_gear_dapc(self):
        # The level should initialise to 0
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 0
        self.bus.send(general.DAPC(address.Short(0), 128))
        # After DAPC the level should be 128
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 128

    def test_fake_gear_recall_max(self):
        # The level should initialise to 0
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 0
        self.bus.send(general.RecallMaxLevel(address.Short(0)))
        # After RecallMaxLevel the level should be 254
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 254

    def test_fake_gear_recall_min(self):
        # The level should initialise to 0
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 0
        self.bus.send(general.RecallMinLevel(address.Short(1)))
        # After RecallMaxLevel the level should be 1
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 1

    def test_fake_gear_set_min(self):
        # Start with a level of 12
        self.bus.send(general.DAPC(address.Short(0), 12))
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 12
        # Set minimum level to 22
        self.bus.send(general.DTR0(22))
        self.bus.send(general.SetMinLevel(address.Short(0)))
        # After SetMinLevel the level should be 22
        resp = self.bus.send(general.QueryMinLevel(address.Short(0)))
        assert resp.value == 22
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 22
        # Level should not go below 22
        self.bus.send(general.DAPC(address.Short(0), 12))
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 22

    def test_fake_gear_set_max(self):
        # Start with a level of 228
        self.bus.send(general.DAPC(address.Short(1), 228))
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 228
        # Set maximum to 191
        self.bus.send(general.DTR0(191))
        self.bus.send(general.SetMaxLevel(address.Short(1)))
        # After SetMaxLevel the level should be 191
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 191
        resp = self.bus.send(general.QueryMaxLevel(address.Short(1)))
        assert resp.value == 191
        # Level should not go above 191
        self.bus.send(general.DAPC(address.Short(1), 228))
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 191

    def test_fake_gear_set_min_above_max(self):
        self.bus.send(general.DTR0(188))
        self.bus.send(general.SetMaxLevel(address.Short(0)))
        resp = self.bus.send(general.QueryMinLevel(address.Short(0)))
        assert resp.value == 1
        # Trying to set the minimum to larger than the maximum should result in the
        # minimum being set the same as the maximum
        self.bus.send(general.DTR0(200))
        self.bus.send(general.SetMinLevel(address.Short(0)))
        resp = self.bus.send(general.QueryMinLevel(address.Short(0)))
        assert resp.value == 188

    def test_fake_gear_set_max_below_min(self):
        self.bus.send(general.DTR0(188))
        self.bus.send(general.SetMinLevel(address.Short(0)))
        # Trying to set the maximum to less than the minimum should result in the
        # maximum being set the same as the minimum
        self.bus.send(general.DTR0(127))
        self.bus.send(general.SetMaxLevel(address.Short(0)))
        resp = self.bus.send(general.QueryMaxLevel(address.Short(0)))
        assert resp.value == 188

    def test_fake_gear_set_scene(self):
        # Initially all scenes are MASK
        resp = self.bus.send(general.QuerySceneLevel(address.Short(0), 0))
        assert resp.value == "MASK"
        # Set some scene values
        self.bus.send(general.DTR0(132))
        self.bus.send(general.SetScene(address.Short(0), 0))
        self.bus.send(general.DTR0(143))
        self.bus.send(general.SetScene(address.Short(1), 0))
        self.bus.send(general.DTR0(154))
        self.bus.send(general.SetScene(address.Short(2), 0))
        self.bus.send(general.DTR0(165))
        self.bus.send(general.SetScene(address.Short(3), 0))
        # Outputs should be off
        for ad in range(0, 4):
            resp = self.bus.send(general.QueryActualLevel(address.Short(ad)))
            assert resp.value == 0
        # Activate the scene via broadcast
        self.bus.send(general.GoToScene(address.Broadcast(), 0))
        # Outputs should be on now
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 132
        resp = self.bus.send(general.QueryActualLevel(address.Short(1)))
        assert resp.value == 143
        resp = self.bus.send(general.QueryActualLevel(address.Short(2)))
        assert resp.value == 154
        resp = self.bus.send(general.QueryActualLevel(address.Short(3)))
        assert resp.value == 165

    def test_fake_gear_set_off(self):
        # Set a higher minimum value
        self.bus.send(general.DTR0(22))
        self.bus.send(general.SetMinLevel(address.Short(0)))
        self.bus.send(general.DAPC(address.Short(0), 10))
        # Ensure minimum level
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 22
        # Ensure DAPC of 0 still works
        self.bus.send(general.DAPC(address.Short(0), 0))
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 0
        # Ensure Off works
        self.bus.send(general.DAPC(address.Short(0), 10))
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 22
        self.bus.send(general.Off(address.Short(0)))
        resp = self.bus.send(general.QueryActualLevel(address.Short(0)))
        assert resp.value == 0


if __name__ == "__main__":
    unittest.main()
