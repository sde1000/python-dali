try:
    from dali import address
    from dali import command
    from dali import frame
    from dali.gear import general as generalgear
    from dali.gear import emergency
    from dali.gear import incandescent
    from dali.gear import led
    from dali.device import general as generaldevice
except ImportError:
    # Realign paths, and try import again
    # Since pyCharm's unittest runner fails on relative imports
    import os
    import sys

    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(
        os.path.realpath(os.path.join(os.getcwd(),
                         os.path.expanduser(__file__))))
    sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

    from dali import address
    from dali import command
    from dali import frame
    from dali.gear import general as generalgear
    from dali.gear import emergency
    from dali.gear import incandescent
    from dali.gear import led
    from dali.device import general as generaldevice
import unittest
import sys

if sys.version_info[0] == 3:
    xrange = range

# Only test device types up to this number - if we went all the way to
# 255 the tests would take unnecessarily long!
max_devicetype = 10

def _test_pattern():
    # Control gear, device type zero
    for d in xrange(0, 0x10000):
        yield 16, d, 0
    # Control gear, device type non-zero, application extended commands only
    for dt in xrange (1, max_devicetype):
        for a in xrange (1, 0x100, 2):
            for b in xrange (0xe0, 0x100):
                yield 16, (a, b), dt
    # Control devices, device commands only
    for a in xrange (0, 0x100):
        for b in xrange (0, 0x100):
            yield 24, (a, 0xfe, b), 0
    # Control devices, instance commands addressed to broadcast device addr
    for d in xrange(0, 0x10000):
        yield 24, 0xff0000 | d, 0
    # Control devices, special commands
    for c in xrange(0, 0x100):
        yield 24, (0xc1, c, 0x00), 0
    for c in (0xc5, 0xc7, 0xc9):
        yield 24, (c, 0x00, 0x00), 0

class TestCommands(unittest.TestCase):

    def test_test_coverage(self):
        "all command classes are covered by test pattern"
        seen = {}
        for fs, d, dt in _test_pattern():
            c = command.from_frame(frame.ForwardFrame(fs, d), devicetype=dt)
            seen[c.__class__] = True
        for cls in command.Command._commands:
            self.assertTrue(cls in seen,
                            "class {} not covered by tests".format(cls.__name__))

    def test_roundtrip(self):
        "all frames survive command.from_frame()"
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            nf = c.frame
            self.assertEqual(
                f, nf, "frame {} failed command round-trip; command {} "
                "became {}".format(str(f), str(c), str(nf)))

    def test_unicode(self):
        "command objects return unicode from their __unicode__ method"
        # Python 2 only
        if sys.version_info[0] == 2:
            for fs, d, dt in _test_pattern():
                f = frame.ForwardFrame(fs, d)
                self.assertIsInstance(command.from_frame(f, dt).__unicode__(),
                                      unicode)

    def test_str(self):
        "command objects can be converted to strings"
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            self.assertIsInstance(str(command.from_frame(f, dt)),
                                  str)

    def test_with_integer_destination(self):
        "commands accept integer destination"
        self.assertEqual(generalgear.DAPC(5, 100).destination, address.Short(5))
        self.assertEqual(generalgear.Off(5).destination, address.Short(5))
        self.assertRaises(ValueError, generalgear.Off, -1)
        self.assertRaises(ValueError, generalgear.Off, 64)
        self.assertRaises(ValueError, generalgear.Off, None)

    def test_response(self):
        "responses act sensibly"
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            if c._response:
                if sys.version_info[0] == 2:
                    self.assertIsInstance(c._response(None).__unicode__(), unicode)
                self.assertRaises(TypeError, lambda: c._response("wibble"))
                if sys.version_info[0] == 2:
                    self.assertIsInstance(c._response(frame.BackwardFrame(0xff))\
                                          .__unicode__(), unicode)

if __name__ == "__main__":
    unittest.main()
