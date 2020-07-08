import unittest

import dali
from dali import address
from dali import command
from dali import frame
from dali.device import general as generaldevice
from dali.gear import general as generalgear


def _test_pattern():
    # Control gear, device type zero
    for d in range(0, 0x10000):
        yield 16, d, 0
    # Control gear, device type non-zero, application extended commands only
    for dt in command.Command._supported_devicetypes:
        for a in range (1, 0x100, 2):
            for b in range (0xe0, 0x100):
                yield 16, (a, b), dt
    # Control devices, device commands only
    for a in range (0, 0x100):
        for b in range (0, 0x100):
            yield 24, (a, 0xfe, b), 0
    # Control devices, instance commands addressed to broadcast device addr
    for d in range(0, 0x10000):
        yield 24, 0xff0000 | d, 0
    # Control devices, special commands
    for c in range(0, 0x100):
        yield 24, (0xc1, c, 0x00), 0
    for c in (0xc5, 0xc7, 0xc9):
        yield 24, (c, 0x00, 0x00), 0


class TestCommands(unittest.TestCase):
    def assertHasAttr(self, obj, intendedAttr):
        testBool = hasattr(obj, intendedAttr)

        self.assertTrue(testBool, msg='obj lacking an attribute. obj: %s, '
                        'intendedAttr: %s' % (obj, intendedAttr))

    def test_test_coverage(self):
        """all command classes are covered by test pattern"""
        seen = {}
        for fs, d, dt in _test_pattern():
            c = command.from_frame(frame.ForwardFrame(fs, d), devicetype=dt)
            seen[c.__class__] = True
        for cls in command.Command._commands:
            self.assertTrue(
                cls in seen,
                'class {} not covered by tests'.format(cls.__name__)
            )

    def test_required_attributes(self):
        """all command classes support required attributes"""
        for cls in command.Command._commands:
            self.assertHasAttr(cls, "appctrl")
            self.assertIsInstance(cls.appctrl, bool)
            self.assertHasAttr(cls, "inputdev")
            self.assertIsInstance(cls.inputdev, bool)
            self.assertHasAttr(cls, "uses_dtr0")
            self.assertIsInstance(cls.uses_dtr0, bool)
            self.assertHasAttr(cls, "uses_dtr1")
            self.assertIsInstance(cls.uses_dtr1, bool)
            self.assertHasAttr(cls, "uses_dtr2")
            self.assertIsInstance(cls.uses_dtr2, bool)
            self.assertHasAttr(cls, "response")
            if cls.response != None:
                self.assertIsInstance(cls.response(None), command.Response)
            self.assertHasAttr(cls, "sendtwice")
            self.assertIsInstance(cls.sendtwice, bool)

    def test_roundtrip(self):
        """all frames survive command.from_frame()"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            nf = c.frame
            self.assertEqual(
                f, nf, 'frame {} failed command round-trip; command {} '
                'became {}'.format(str(f), str(c), str(nf)))

    def test_str(self):
        """command objects can be converted to strings"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            self.assertIsInstance(str(command.from_frame(f, dt)),
                                  str)

    def test_with_integer_destination(self):
        """commands accept integer destination"""
        self.assertEqual(
            generalgear.DAPC(5, 100).destination,
            address.Short(5)
        )
        self.assertEqual(generalgear.Off(5).destination, address.Short(5))
        self.assertRaises(ValueError, generalgear.Off, -1)
        self.assertRaises(ValueError, generalgear.Off, 64)
        self.assertRaises(ValueError, generalgear.Off, None)

    def test_response(self):
        """responses act sensibly"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            if c.response:
                self.assertRaises(TypeError, lambda: c.response('wibble'))
                self.assertHasAttr(
                    c.response(None), 'raw_value')

    def test_queryextendedversionnumber(self):
        """all gear types implement QueryExtendedVersionNumber"""
        # dali.gear.general.QueryExtendedVersionNumber is an oddity:
        # it is only used when preceded by EnableDeviceType with
        # devicetype != 0.  Ensure that there is an implementation of
        # this command for all supported device types.
        qevn_frame = generalgear.QueryExtendedVersionNumber(
            address.Broadcast()).frame
        for devicetype in command.Command._supported_devicetypes:
            qevn = command.from_frame(qevn_frame, devicetype=devicetype)
            self.assertIsNotNone(qevn)
            self.assertEqual(qevn.__class__.__name__,
                             'QueryExtendedVersionNumber')
            self.assertEqual(qevn.devicetype, devicetype)


if __name__ == '__main__':
    unittest.main()
