import unittest
from dali.tests import fakes
from dali import sequences
from dali import address

class TestSequences(unittest.TestCase):
    def test_querydevicetypes(self):
        testcases = [
            [1, 3, 6],
            [6],
            [],
            [252, 253],
        ]
        bus = fakes.Bus([fakes.Gear(shortaddr=a, devicetypes=dts)
                         for a, dts in enumerate(testcases)])
        for a, dts in enumerate(testcases):
            r = bus.run_sequence(sequences.QueryDeviceTypes(a))
            self.assertEqual(r, dts)

    def test_querydevicetypes_noresponse(self):
        bus = fakes.Bus([])
        self.assertRaises(sequences.DALISequenceError,
                          bus.run_sequence, sequences.QueryDeviceTypes(0))

    def test_querydevicetypes_out_of_order(self):
        bus = fakes.Bus([fakes.Gear(shortaddr=1, devicetypes=[3, 2, 1])])
        self.assertRaises(sequences.DALISequenceError,
                          bus.run_sequence, sequences.QueryDeviceTypes(0))

    def _check_addresses(self, gear, expected=None):
        if expected is None:
            expected = list(range(len(gear)))
        addresses = [g.shortaddr for g in gear]
        addresses.sort()
        self.assertEqual(addresses, expected)

    def test_commissioning(self):
        gear = [fakes.Gear() for x in range(10)]
        bus = fakes.Bus(gear)
        bus.run_sequence(sequences.Commissioning())
        self._check_addresses(gear)
        # Now add another 10 unaddressed devices to the bus, and
        # change the address of one of the original 10 to 30
        gear[5].shortaddr = 30
        for x in range(10):
            bus.gear.append(fakes.Gear())
        bus.run_sequence(sequences.Commissioning())
        self._check_addresses(gear, [x for x in range(19)] + [30])
        bus.run_sequence(sequences.Commissioning(readdress=True, dry_run=True))
        self._check_addresses(gear, [x for x in range(19)] + [30])
        bus.run_sequence(sequences.Commissioning(readdress=True))
        self._check_addresses(gear)

    def test_commissioning_clash(self):
        # (At least) one of the devices is going to pick the same
        # "random" number as another the first time around!
        randoms = list(range(0, 0xffffff, 0x82000))
        randoms[8] = randoms[4]
        gear = [fakes.Gear(random_preload=[x]) for x in randoms]
        bus = fakes.Bus(gear)
        bus.run_sequence(sequences.Commissioning())
        self._check_addresses(gear)

    def test_commissioning_high_random_address(self):
        # One of the devices is persistently going to pick 0xffffff as
        # its random address
        gear = [fakes.Gear() for x in range(9)]
        gear.append(fakes.Gear(random_preload=[0xffffff] * 10))
        bus = fakes.Bus(gear)
        bus.run_sequence(sequences.Commissioning())
        self._check_addresses(gear)

    def test_commissioning_restricted_addresses(self):
        # There aren't going to be enough addresses to go around
        gear = [fakes.Gear() for x in range(10)]
        bus = fakes.Bus(gear)
        available = range(10, 15)
        bus.run_sequence(sequences.Commissioning(available_addresses=available))
        missed = 0
        for g in gear:
            if g.shortaddr is None:
                missed += 1
            else:
                self.assertIn(g.shortaddr, available)
        self.assertEqual(missed, 5)

    def test_query_groups(self):
        gear = [fakes.Gear(shortaddr=x, groups={x}) for x in range(0, 16)]
        bus = fakes.Bus(gear)
        for i in range(0, 16):
            self.assertEqual(bus.run_sequence(sequences.QueryGroups(i)), {i})

    def test_set_groups(self):
        gear = [fakes.Gear(shortaddr=x, groups={x}) for x in range(0, 16)]
        bus = fakes.Bus(gear)
        tp = {1, 3, 5, 7, 8, 9, 10, 13}
        for i in range(0, 16):
            bus.run_sequence(sequences.SetGroups(i, tp))
            self.assertEqual(bus.run_sequence(sequences.QueryGroups(i)), tp)
        tp = {0, 4, 7}
        bus.run_sequence(sequences.SetGroups(address.Broadcast(), tp))
        for i in range(0, 16):
            bus.run_sequence(sequences.SetGroups(i, tp))
            self.assertEqual(bus.run_sequence(sequences.QueryGroups(i)), tp)

if __name__ == '__main__':
    unittest.main()
