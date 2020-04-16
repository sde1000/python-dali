"""Commands and responses from IEC 62386 part 207."""

from dali import command
from dali.gear.general import _StandardCommand, QueryExtendedVersionNumberMixin


class _LEDCommand(_StandardCommand):
    devicetype = 6


class _LEDConfigCommand(_LEDCommand):
    """A LED lighting configuration command as defined in section 11.3.4.1
    of IEC 62386-207:2009.
    """
    sendtwice = True


###############################################################################
# Commands from IEC 62386-207 section 11.3.4.1
###############################################################################

class ReferenceSystemPower(_LEDConfigCommand):
    """Reference System Power

    The control gear shall measure and store system power levels in
    order to detect load increase or load decrease.  The measurement
    may take up to 15 minutes.  Measured power levels will be stored
    in non-volatile memory, Commands received during the measuring
    period will be ignored except query commands and Terminate.

    The process will be aborted if dali.gear.general.Terminate is
    received.
    """
    _cmdval = 0xe0


class EnableCurrentProtector(_LEDConfigCommand):
    """Enables the current protector of the control gear.

    The current protector can become active after a successful
    reference measurement started by command ReferenceSystemPower().

    The default configuration of the gear is "current protector
    enabled".  The status of the current protector is stored in
    persistent memory.
    """
    _cmdval = 0xe1


class DisableCurrentProtector(_LEDConfigCommand):
    """Disables the current protector of the control gear."""
    _cmdval = 0xe2


class SelectDimmingCurve(_LEDConfigCommand):
    """Set the dimming curve in accordance with DTR0.

    0 - standard
    1 - linear
    """
    uses_dtr0 = True
    _cmdval = 0xe3


class StoreDTRAsFastFadeTime(_LEDConfigCommand):
    """Store DTR0 as the fast fade time.

    If DTR0 is in the range MIN FAST FADE TIME to 27 it is stored as
    the fast fade time.  If it is greater than 27 then 27 is stored as
    the fast fade time.
    """
    uses_dtr0 = True
    _cmdval = 0xe4


###############################################################################
# Commands from IEC 62386-207 section 11.3.4.2
###############################################################################

class LEDGearTypeResponse(command.BitmapResponse):
    bits = ["LED power supply integrated",
            "LED module integrated",
            "a.c. supply possible",
            "d.c. supply possible"]

class QueryGearType(_LEDCommand):
    response = LEDGearTypeResponse
    _cmdval = 0xed


class QueryDimmingCurve(_LEDCommand):
    """Query the dimming curve currently in use.

    0 - standard
    1 - linear
    """
    response = command.Response
    _cmdval = 0xee


class LEDOperatingModesResponse(command.BitmapResponse):
    bits = ["PWM mode is possible",
            "AM mode is possible",
            "output is current controlled",
            "high current pulse mode"]

class QueryPossibleOperatingModes(_LEDCommand):
    response = LEDOperatingModesResponse
    _cmdval = 0xef


class LEDFeaturesResponse(command.BitmapResponse):
    bits = ["short circuit detection can be queried",
            "open circuit detection can be queried",
            "detection of load decrease can be queried",
            "detection of load increase can be queried",
            "current protector is implemented and can be queried",
            "thermal shut down can be queried",
            "light level reduction due to over temperature can be queried",
            "physical selection supported"]

class QueryFeatures(_LEDCommand):
    response = LEDFeaturesResponse
    _cmdval = 0xf0


class LEDFailureStatusResponse(command.BitmapResponse):
    bits = ["short circuit",
            "open circuit",
            "load decrease",
            "load increase",
            "current protector active",
            "thermal shut down",
            "thermal overload with light level reduction",
            "reference measurement failed"]

class QueryFailureStatus(_LEDCommand):
    response = LEDFailureStatusResponse
    _cmdval = 0xf1


class QueryShortCircuit(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf2


class QueryOpenCircuit(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf3


class QueryLoadDecrease(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf4


class QueryLoadIncrease(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf5


class QueryCurrentProtectorActive(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf6


class QueryThermalShutDown(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf7


class QueryThermalOverload(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf8


class QueryReferenceRunning(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xf9


class QueryReferenceMeasurementFailed(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xfa


class QueryCurrentProtectorEnabled(_LEDCommand):
    response = command.YesNoResponse
    _cmdval = 0xfb


class LEDOperatingModeResponse(command.BitmapResponse):
    bits = ["PWM mode active",
            "AM mode active",
            "output is current controlled",
            "high current pulse mode is active",
            "non-logarithmic dimming curve active"]

class QueryOperatingMode(_LEDCommand):
    response = LEDOperatingModeResponse
    _cmdval = 0xfc


class QueryFastFadeTime(_LEDCommand):
    response = command.Response
    _cmdval = 0xfd


class QueryMinFastFadeTime(_LEDCommand):
    response = command.Response
    _cmdval = 0xfe

class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _LEDCommand):
    pass
