try:
    from dali import address
    from dali import command
    from dali import commands
    from dali import frame
except:
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
    from dali import commands
    from dali import frame

import unittest

# Only test device types up to this number - if we went all the way to
# 255 the tests would take unnecessarily long!
max_devicetype = 10


class TestCommands(unittest.TestCase):
    def test_roundtrip(self):
        "all 16-bit frames survive command.from_frame()"
        for dt in xrange(0, max_devicetype):
            for d in xrange(0, 0x10000):
                f = frame.ForwardFrame(16, d)
                c = command.from_frame(f, dt)
                nf = c.frame
                self.assertEqual(
                    f, nf,"frame {} failed command round-trip; command {} "
                    "became {}".format(unicode(f), unicode(c), unicode(nf)))

    def test_unicode(self):
        "command objects return unicode from their __unicode__ method"
        for dt in xrange(0, max_devicetype):
            for d in xrange(0, 0x10000):
                f = frame.ForwardFrame(16, d)
                self.assertTrue(
                    isinstance(command.from_frame(f, dt).__unicode__(),
                               unicode),
                    "command {} unicode method didn't return unicode".\
                    format(f))

    def test_bad_command(self):
        "command.from_bytes() rejects invalid inputs"
        self.assertRaises(TypeError, command.from_bytes, 1)
        self.assertRaises(TypeError, command.from_bytes, "test")
        self.assertRaises(ValueError, command.from_bytes, (256, 0))
        self.assertRaises(ValueError, command.from_bytes, (0, 256))
        self.assertRaises(ValueError, command.from_bytes, (-1, 0))
        self.assertRaises(ValueError, command.from_bytes, (0, -1))

    def test_with_integer_destination(self):
        "commands accept integer destination"
        self.assertEqual(commands.ArcPower(5, 100).destination, address.Short(5))
        self.assertEqual(commands.Off(5).destination, address.Short(5))
        self.assertRaises(ValueError, commands.Off, -1)
        self.assertRaises(ValueError, commands.Off, 64)
        self.assertRaises(ValueError, commands.Off, None)


if __name__ == "__main__":
    unittest.main()
