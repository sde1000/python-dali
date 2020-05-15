"""Commands and responses from IEC 62386 part 202."""

from dali import command
from dali.gear.general import _StandardCommand, QueryExtendedVersionNumberMixin


class _EmergencyLightingCommand(_StandardCommand):
    devicetype = 1


class _EmergencyLightingControlCommand(_EmergencyLightingCommand):
    """An emergency lighting control command as defined in section
    11.3.4.1 of IEC 62386-202:2009
    """
    sendtwice = True


class _EmergencyLightingConfigCommand(_EmergencyLightingCommand):
    """An emergency lighting configuration command as defined in section
    11.3.4.2 of IEC 62386-202:2009
    """
    sendtwice = True


class _EmergencyLightingQueryCommand(_EmergencyLightingCommand):
    """An emergency lighting query command as defined in section 11.3.4.3
    of IEC 62386-202:2009
    """
    response = command.Response


###############################################################################
# Commands from IEC 62386-202 section 11.3.4.1
###############################################################################

class Rest(_EmergencyLightingControlCommand):
    """If this command is received when the control gear is in emergency
    mode then the lamp shall be extinguished.

    Rest mode shall revert to normal mode in the event of restoration
    of normal supply, or on receipt of command "ReLightResetInhibit"
    if re-light in rest mode is supported.
    """
    _cmdval = 0xe0


class Inhibit(_EmergencyLightingControlCommand):
    """If the control gear is in normal mode on receipt of this command,
    bit 0 of the Emergency Status byte shall be set and the control
    gear shall go into inhibit mode.

    In inhibit mode, a 15 minute timer starts.  Normal mode is resumed
    on expiry of this timer, or on receipt of command
    "ReLightResetInhibit".

    If mains power is lost while in inhibit mode, rest mode will be entered.
    """
    _cmdval = 0xe1


class ReLightResetInhibit(_EmergencyLightingControlCommand):
    """This command cancels the inhibit timer.  If the control gear is in
    rest mode and re-light in rest mode is supported then the control
    gear will enter emergency mode.
    """
    _cmdval = 0xe2


class StartFunctionTest(_EmergencyLightingControlCommand):
    """The control gear is requested to perform a function test.  A
    function test is a brief test of the operation of the lamp, the
    battery and the changeover circuit.

    If a function test is already in progress then this command is
    ignored.

    If the function test cannot be started immediately then it will be
    set as pending until it can be performed.  Bit 4 of the Emergency
    Status byte will be set.
    """
    _cmdval = 0xe3


class StartDurationTest(_EmergencyLightingControlCommand):
    """The control gear is requested to perform a duration test.  A
    duration test tests that the lamp can be operated for the rated
    duration from the battery.

    If a duration test is already in progress then this command is
    ignored.

    If the duration test cannot be started immediately then it will be
    set as pending until it can be performed.  Bit 5 of the Emergency
    Status byte will be set.
    """
    _cmdval = 0xe4


class StopTest(_EmergencyLightingControlCommand):
    """Any running tests are stopped and any pending tests are cancelled.
    Bits 4 and 5 of the Emergency Status byte will be cleared.
    """
    _cmdval = 0xe5


class ResetFunctionTestDoneFlag(_EmergencyLightingControlCommand):
    """The "function test done and result valid" flag (bit 1 of the
    Emergency Status byte) shall be cleared.
    """
    _cmdval = 0xe6


class ResetDurationTestDoneFlag(_EmergencyLightingControlCommand):
    """The "duration test done and result valid" flag (bit 2 of the
    Emergency Status byte) shall be cleared.
    """
    _cmdval = 0xe7


class ResetLampTime(_EmergencyLightingControlCommand):
    """The lamp emergency time and lamp total operation time counters
    shall be reset.
    """
    _cmdval = 0xe8


###############################################################################
# Commands from IEC 62386-202 section 11.3.4.2
###############################################################################

class StoreDTRAsEmergencyLevel(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Emergency Level."""
    _cmdval = 0xe9


class StoreTestDelayTimeHighByte(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the high byte of Test Delay Time.

    Test Delay Time is a 16-bit quantity in quarters of an hour.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xea


class StoreTestDelayTimeLowByte(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the low byte of Test Delay Time.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xeb


class StoreFunctionTestInterval(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Function Test Interval.  This is the
    number of days (1..255) between automatic function tests.  0
    disables automatic function tests.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xec


class StoreDurationTestInterval(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Duration Test Interval.  This is the
    number of weeks (1..97) between automatic duration tests.  0
    disables automatic duration tests.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xed


class StoreTestExecutionTimeout(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Test Execution Timeout.  This is
    defined in days (1..255).  A value of 0 means 15 minutes.

    The Test Execution Timeout period starts when a test becomes
    pending.  If the period expires without the test being finished,
    it shall be flagged as a failure in the Failure Status byte but
    the test shall remain pending.
    """
    _cmdval = 0xee


class StoreProlongTime(_EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Prolong Time.  This is defined in 30s
    units (0..255) and is used to determine the length of time the
    control gear will remain in emergency mode after mains power is
    restored.
    """
    _cmdval = 0xef


class StartIdentification(_EmergencyLightingConfigCommand):
    """The control gear shall start or restart a ten-second procedure
    intended to enable the operator to identify it.
    """
    _cmdval = 0xf0


###############################################################################
# Commands from IEC 62386-202 section 11.3.4.3
###############################################################################

class QueryBatteryCharge(_EmergencyLightingQueryCommand):
    """Query the actual battery charge level from 0 (the deep discharge
    point) to 254 (fully charged).  255 (MASK) indicates the value is
    unknown, possibly because the control gear has not performed a
    successful duration test.
    """
    _cmdval = 0xf1
    response = command.NumericResponseMask


class QueryTestTiming(_EmergencyLightingQueryCommand):
    """The answer depends on the content of DTR0:

    0 - time until the next function test in quarters of an hour (high byte)
    1 - time until the next function test in quarters of an hour (low byte)
    2 - time until the next duration test in quarters of an hour (high byte)
    3 - time until the next duration test in quarters of an hour (low byte)
    4 - function test interval time in days (or 0)
    5 - duration test interval time in weeks (or 0)
    6 - test execution timeout in days
    7 - prolong time in 30s intervals

    When the high byte of a 16-bit value is read, the low byte is
    placed in DTR1 to enable atomic reads.  If automatic testing is
    not supported then queries 0-3 will return 255 (MASK).
    """
    _cmdval = 0xf2


class QueryDurationTestResult(_EmergencyLightingQueryCommand):
    """Returns the duration test result in 120s (2min) units.  255 means
    the maximum value or longer.
    """
    _cmdval = 0xf3
    response = command.NumericResponse


class QueryLampEmergencyTime(_EmergencyLightingQueryCommand):
    """Returns the accumulated lamp functioning time with the battery as
    power source in hours.  255 means the maximum value or longer.
    """
    _cmdval = 0xf4
    response = command.NumericResponse


class QueryLampTotalOperationTime(_EmergencyLightingQueryCommand):
    """Returns the accumulated lamp total functioning time in 4-hour
    units.  255 means the maximum value of 1016h or longer.

    If the lamp is operated by another control device (for example
    where the emercency lighting control device does not support
    operating the lamp from the mains) this time may not include the
    time the lamp is operated by the other control device.
    """
    _cmdval = 0xf5
    response = command.NumericResponse


class QueryEmergencyLevel(_EmergencyLightingQueryCommand):
    """Return the Emergency Level, or MASK (255) if it is unknown."""
    _cmdval = 0xf6
    response = command.NumericResponseMask


class QueryEmergencyMinLevel(_EmergencyLightingQueryCommand):
    """Return the Emergency Min Level, or MASK (255) if it is unknown."""
    _cmdval = 0xf7
    response = command.NumericResponseMask


class QueryEmergencyMaxLevel(_EmergencyLightingQueryCommand):
    """Return the Emergency Max Level, or MASK (255) if it is unknown."""
    _cmdval = 0xf8
    response = command.NumericResponseMask


class QueryRatedDuration(_EmergencyLightingQueryCommand):
    """Return the rated duration in units of 2min.  255 means 510 min or
    longer.
    """
    _cmdval = 0xf9
    response = command.NumericResponse


class QueryEmergencyModeResponse(command.BitmapResponse):
    bits = ["rest mode", "normal mode", "emergency mode",
            "extended emergency mode", "function test", "duration test",
            "hardwired inhibit active", "hardwired switch on"]

    @property
    def mode(self):
        """Operating mode of the emergency control gear.  Only one of bits 0-5
        should be set at once, but we support returning a sensible
        response even when multiple bits are set.
        """
        v = self._value[5:0]
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return ",".join(l)


class QueryEmergencyMode(_EmergencyLightingQueryCommand):
    """Return the Emergency Mode Information byte."""
    _cmdval = 0xfa
    response = QueryEmergencyModeResponse


class QueryEmergencyFeaturesResponse(command.BitmapResponse):
    bits = ["integral emergency control gear", "maintained control gear",
            "switched maintained control gear", "auto test capability",
            "adjustable emergency level", "hardwired inhibit supported",
            "physical selection supported", "re-light in rest mode supported"]


class QueryEmergencyFeatures(_EmergencyLightingQueryCommand):
    """Return the Features information byte."""
    _cmdval = 0xfb
    response = QueryEmergencyFeaturesResponse


class QueryEmergencyFailureStatusResponse(command.BitmapResponse):
    bits = ["circuit failure", "battery duration failure", "battery failure",
            "emergency lamp failure", "function test max delay exceeded",
            "duration test max delay exceeded", "function test failed",
            "duration test failed"]


class QueryEmergencyFailureStatus(_EmergencyLightingQueryCommand):
    """Return the Failure Status information byte."""
    _cmdval = 0xfc
    response = QueryEmergencyFailureStatusResponse


class QueryEmergencyStatusResponse(command.BitmapResponse):
    bits = ["inhibit mode", "function test done and result valid",
            "duration test done and result valid", "battery fully charged",
            "function test pending", "duration test pending",
            "identification active", "physically selected"]


class QueryEmergencyStatus(_EmergencyLightingQueryCommand):
    """Return the Emergency Status information byte."""
    _cmdval = 0xfd
    response = QueryEmergencyStatusResponse


class PerformDTRSelectedFunction(_EmergencyLightingControlCommand):
    """Perform a function depending on the value in DTR0:

    0 - restore factory default settings
    """
    _cmdval = 0xfe

class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _EmergencyLightingCommand):
    pass
