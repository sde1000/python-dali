"""Commands and responses from IEC 62386 part 206.

This part covers conversion from digital signal into DC voltage.
"""

from dali import command
from dali.gear.general import _StandardCommand, QueryExtendedVersionNumberMixin


class _ConversionCommand(_StandardCommand):
    devicetype = 5


class _ConversionConfigCommand(_ConversionCommand):
    """An incandescent lighting configuration command as defined in
    section 11.3.4.1 of IEC 62386-206:2009.
    """
    sendtwice = True


###############################################################################
# Commands from IEC 62386-206 section 11.3.4.1
###############################################################################

class SetOutputRange1To10V(_ConversionConfigCommand):
    """Set the output range to 1V - 10V

    Converters without this feature shall not react.
    """
    _cmdval = 224


class SetOutputRange0To10V(_ConversionConfigCommand):
    """Set the output range to 0V - 10V

    Converters without this feature shall not react.
    """
    _cmdval = 225


class SwitchOnInternalPullUp(_ConversionConfigCommand):
    """Switch on the internal pull-up resistor at the control voltage output

    Converters without this feature shall not react.
    """
    _cmdval = 226


class SwitchOffInternalPullUp(_ConversionConfigCommand):
    """Switch off the internal pull-up resistor at the control voltage output

    Converters without this feature shall not react.
    """
    _cmdval = 227


class StoreDtrAsPhysicalMinimum(_ConversionConfigCommand):
    """The physical minimum level shall be changed to the value given in the DTR"""
    _cmdval = 228


class SelectDimmingCurve(_ConversionConfigCommand):
    """Select Dimming Curve

    If DTR0 is 0 then selects the standard logarithmic curve

    If DTR0 is 1 then selects a linear dimming curve

    Other values of DTR0 are reserved and will not change the dimming
    curve.  The setting is stored in non-volatile memory and is not
    cleared by the Reset command.
    """
    _cmdval = 229


class ResetConverterSettings(_ConversionConfigCommand):
    """Reset parameters which are not affected by RESET

    All converter settings not influenced by the RESET command shall be set to the
    default values given in clause 10 of IEC 62386-206:2009.
    """
    _cmdval = 230


###############################################################################
# Commands from IEC 62386-205 section 11.3.4.2
###############################################################################

class QueryDimmingCurve(_ConversionCommand):
    """Query Dimming Curve

    0 = standard logarithmic
    1 = linear
    2-255 = reserved for future use
    """
    _cmdval = 238
    response = command.Response


class OutputLevelResponse(command.NumericResponse):
    def __str__(self):
        if isinstance(self.value, int):
            if self.value == 254:
                return "10.16V or more"
            elif self.value == 255:
                return "unknown"
            else:
                return f"{self.value * 0.04} V"
        return self.value


class QueryOutputLevel(_ConversionCommand):
    """Query the output level

    The answer shall be the analog output level in units of 0.04V, fiving a range of 0V to 10.16V.

    Raw value 254 maps to 10.16V or higher.
    Raw value of 255 means "the output level is not known".

    Converters without this feature shall not react.
    """
    _cmdval = 239
    response = OutputLevelResponse


class QueryConverterFeaturesResponse(command.BitmapResponse):
    bits = [
        "0V - 10V output selectable",
        "internal pull-up selectable",
        "detection of output fault selectable",
        "mains relay",
        "output level can be queried",
        "non-logarithmic dimming curve supported",
        "physical selection / lamp fail detection by loss out output supported",
        "physical selection switch supported",
    ]


class QueryConverterFeatures(_ConversionCommand):
    """Query hardware features of the converter"""
    _cmdval = 240
    response = QueryConverterFeaturesResponse


class QueryFailureStatusResponse(command.BitmapResponse):
    bits = [
        "output fault detected",
    ]


class QueryFailureStatus(_ConversionCommand):
    """Query failure status register"""
    _cmdval = 241
    response = QueryFailureStatusResponse


class QueryConverterStatusResponse(command.BitmapResponse):
    bits = [
        "0-10V operation",
        "internal pull-up on",
        "non-logarithmic dimming curve active",
    ]


class QueryConverterStatus(_ConversionCommand):
    """Query the current status of the converter"""
    _cmdval = 242
    response = QueryConverterStatusResponse


class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _ConversionCommand):
    pass
