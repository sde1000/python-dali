from typing import Iterable, Any
import unittest
import enum
from dali import address
from dali import command
from dali import frame
from dali import exceptions
from dali.gear import general as generalgear


def _test_pattern() -> Iterable[tuple[int, int | Iterable[int], int]]:
    # Control gear, device type zero
    for d in range(0, 0x10000):
        yield 16, d, 0
    # Control gear, device type non-zero, application extended commands only
    for dt in command.Command._supported_devicetypes:
        for a in range(1, 0x100, 2):
            for b in range(0xe0, 0x100):
                yield 16, (a, b), dt
    # Control devices, device commands only
    for a in range(0, 0x100):
        for b in range(0, 0x100):
            yield 24, (a, 0xfe, b), 0
    # Control devices, instance commands addressed to broadcast device addr
    for d in range(0, 0x10000):
        yield 24, 0xff0000 | d, 0
    # Control devices, special commands
    for c in range(0, 0x100):
        yield 24, (0xc1, c, 0x00), 0
    for c in (0xc5, 0xc7, 0xc9):
        yield 24, (c, 0x00, 0x00), 0
    # Control devices, event messages for push buttons (part 301)
    for e in (0, 1, 2, 5, 9, 11, 12, 14, 15):
        yield 24, (0xc2, 0x04, e), 0
    # Control devices, QueryEventFilter
    for o in (0x90, 0x91, 0x92):
        yield 24, (0x03, 0x00, o), 0
    # Control devices, events for occupancy sensors (part 303)
    for e in range(16):
        yield 24, (0x86, 0xFC, e), 0


class TrialEnum(enum.IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


class TrialEnumResponse(command.EnumResponse):
    enumerator = TrialEnum


class TestResponses(unittest.TestCase):
    # XXX add more response class tests here!

    def test_enum_response(self) -> None:
        # Test a valid response
        trial = TrialEnumResponse(frame.BackwardFrame(1))
        self.assertTrue(trial.valid)
        self.assertFalse(trial.missing)
        self.assertFalse(trial.error)
        self.assertEqual(trial.value, TrialEnum.ONE)

        # Test a response with an invalid value
        trial = TrialEnumResponse(frame.BackwardFrame(4))
        self.assertFalse(trial.valid)
        self.assertFalse(trial.missing)
        self.assertFalse(trial.error)
        self.assertRaises(ValueError, getattr, trial, "value")

        # Test a response with an error value
        trial = TrialEnumResponse(frame.BackwardFrameError(2))
        self.assertFalse(trial.valid)
        self.assertFalse(trial.missing)
        self.assertTrue(trial.error)
        self.assertRaises(exceptions.ResponseError, getattr, trial, "value")

        # Test a missing response
        trial = TrialEnumResponse(None)
        self.assertFalse(trial.valid)
        self.assertTrue(trial.missing)
        self.assertFalse(trial.error)
        self.assertRaises(exceptions.MissingResponse, getattr, trial, "value")


class TestCommands(unittest.TestCase):
    # assertHasAttr is new in Python 3.14; while we are supporting
    # earlier versions we must define it here to use it
    def assertHasAttr(self, obj: object, name: str, msg: Any = None) -> None:
        testBool = hasattr(obj, name)

        self.assertTrue(testBool, msg='obj lacking an attribute. obj: %s, '
                        'name: %s, msg: %s' % (obj, name, msg))

    def test_test_coverage(self) -> None:
        """all command classes are covered by test pattern"""
        seen: set[type[command.Command]] = set()
        all_commands = set(command.Command._commands)
        # The set of commands does not normally include the base
        # Command class, but we will be seeing that for frames that
        # don't resolve to a Command
        all_commands.add(command.Command)
        for fs, d, dt in _test_pattern():
            c = command.from_frame(
                frame.ForwardFrame(fs, d), devicetype=dt)
            self.assertIsNotNone(c, f'frame {fs} did not resolve to a command')
            if c is not None:
                seen.add(c.__class__)
        self.assertSetEqual(seen, all_commands)

    def test_required_attributes(self) -> None:
        """all command classes support required attributes"""
        for cls in command.Command._commands:
            print(f"working on {cls}")
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
            if cls.response is not None:
                self.assertIsInstance(cls.response(None), command.Response)
            self.assertHasAttr(cls, "sendtwice")
            self.assertIsInstance(cls.sendtwice, bool)

    def test_roundtrip(self) -> None:
        """all frames survive command.from_frame()"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            self.assertIsNotNone(c)
            assert c is not None  # for mypy
            nf = c.frame
            self.assertEqual(
                f, nf, 'frame {} failed command round-trip; command {} '
                'became {}'.format(str(f), str(c), str(nf)))

    def test_str(self) -> None:
        """command objects can be converted to strings"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            self.assertIsInstance(str(command.from_frame(f, dt)),
                                  str)

    def test_with_integer_destination(self) -> None:
        """commands accept integer destination"""
        self.assertEqual(
            generalgear.DAPC(5, 100).destination,
            address.Short(5)
        )
        self.assertEqual(generalgear.Off(5).destination, address.Short(5))
        self.assertRaises(ValueError, generalgear.Off, -1)
        self.assertRaises(ValueError, generalgear.Off, 64)
        self.assertRaises(ValueError, generalgear.Off, None)

    def test_response(self) -> None:
        """responses act sensibly"""
        for fs, d, dt in _test_pattern():
            f = frame.ForwardFrame(fs, d)
            c = command.from_frame(f, dt)
            assert c is not None  # for mypy
            if c.response:
                response = c.response
                self.assertIsNot(
                    c.response, command.Response,
                    msg=f"{c} has a bare Response class as its response type")
                self.assertRaises(
                    TypeError,
                    lambda: response('wibble'))  # type: ignore[arg-type]
                self.assertHasAttr(
                    response(None), 'raw_value',
                    msg=f"{c} response missing raw_value attribute")
                self.assertIsInstance(
                    str(response(None)), str,
                    msg=f"{c} str(response(None)) failed")
                self.assertIsInstance(
                    str(response(frame.BackwardFrame(0))), str,
                    msg=f"{c} str(response(BackwardFrame(0))) failed")
                self.assertIsInstance(
                    str(response(frame.BackwardFrameError(0))), str,
                    msg=f"{c} str(response(BackwardFrameError(0))) failed")

    def test_queryextendedversionnumber(self) -> None:
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
            assert qevn is not None  # for mypy
            self.assertEqual(qevn.__class__.__name__,
                             'QueryExtendedVersionNumber')
            self.assertEqual(qevn.devicetype, devicetype)


if __name__ == '__main__':
    unittest.main()
