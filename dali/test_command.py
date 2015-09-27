try:
    from dali import address
    from dali import command
    from dali import frame
    from dali.gear import general
    from dali.gear import emergency
    from dali.gear import incandescent
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
    from dali.gear import general
    from dali.gear import emergency
    from dali.gear import incandescent

import unittest

# Only test device types up to this number - if we went all the way to
# 255 the tests would take unnecessarily long!
max_devicetype = 10

def _test_pattern_16bit():
    for d in xrange(0, 0x10000):
        yield d, 0
    for dt in xrange (1, max_devicetype):
        for a in xrange (1, 0x100, 2):
            for b in xrange (0xe0, 0x100):
                yield (a, b), dt

class TestCommands(unittest.TestCase):

    def test_test_coverage(self):
        "all command classes are covered by test pattern"
        seen = {}
        for d, dt in _test_pattern_16bit():
            c = command.from_frame(frame.ForwardFrame(16, d), devicetype=dt)
            seen[c.__class__] = True
        for cls in command.Command._commands:
            self.assertTrue(cls in seen,
                            "class {} not covered by tests".format(cls.__name__))

    def test_roundtrip(self):
        "all 16-bit frames survive command.from_frame()"
        for d, dt in _test_pattern_16bit():
            f = frame.ForwardFrame(16, d)
            c = command.from_frame(f, dt)
            nf = c.frame
            self.assertEqual(
                f, nf, "frame {} failed command round-trip; command {} "
                "became {}".format(unicode(f), unicode(c), unicode(nf)))

    def test_unicode(self):
        "command objects return unicode from their __unicode__ method"
        for d, dt in _test_pattern_16bit():
            f = frame.ForwardFrame(16, d)
            self.assertTrue(
                isinstance(command.from_frame(f, dt).__unicode__(),
                           unicode),
                "command {} unicode method didn't return unicode".\
                format(unicode(f)))

    def test_with_integer_destination(self):
        "commands accept integer destination"
        self.assertEqual(general.DAPC(5, 100).destination, address.Short(5))
        self.assertEqual(general.Off(5).destination, address.Short(5))
        self.assertRaises(ValueError, general.Off, -1)
        self.assertRaises(ValueError, general.Off, 64)
        self.assertRaises(ValueError, general.Off, None)

    def test_response(self):
        "responses act sensibly"
        for d, dt in _test_pattern_16bit():
            f = frame.ForwardFrame(16, d)
            c = command.from_frame(f, dt)
            if c._response:
                self.assertTrue(
                    isinstance(c._response(None).__unicode__(), unicode),
                    "cmd {} unicode(response(None)) didn't return unicode".\
                    format(unicode(f)))
                self.assertRaises(TypeError, lambda: c._response("wibble"))
                self.assertTrue(
                    isinstance(c._response(frame.BackwardFrame(0xff)).\
                               __unicode__(), unicode),
                    "cmd {} unicode(response(0xff)) didn't return unicode".\
                    format(unicode(f)))

if __name__ == "__main__":
    unittest.main()
