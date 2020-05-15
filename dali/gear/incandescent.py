"""Commands and responses from IEC 62386 part 205."""

from dali import command
from dali.gear.general import _StandardCommand, QueryExtendedVersionNumberMixin


class _IncandescentCommand(_StandardCommand):
    devicetype = 4


class _IncandescentConfigCommand(_IncandescentCommand):
    """An incandescent lighting configuration command as defined in
    section 11.3.4.1 of IEC 62386-205:2009.
    """
    sendtwice = True


###############################################################################
# Commands from IEC 62386-205 section 11.3.4.1
###############################################################################

class ReferenceSystemPower(_IncandescentConfigCommand):
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


class SelectDimmingCurve(_IncandescentConfigCommand):
    """Select Dimming Curve

    If DTR0 is 0 then selects the standard logarithmic curve

    If DTR0 is 1 then selects a linear dimming curve

    Other values of DTR0 are reserved and will not change the dimming
    curve.  The setting is stored in non-volatile memory and is not
    cleared by the Reset command.
    """
    _cmdval = 0xe1


###############################################################################
# Commands from IEC 62386-205 section 11.3.4.2
###############################################################################

class QueryDimmingCurve(_IncandescentCommand):
    """Query Dimming Curve

    0 = standard logarithmic
    1 = linear
    """
    _cmdval = 0xee
    response = command.Response


class DimmerStatusResponse(command.BitmapResponse):
    bits = ["leading edge mode running", "trailing edge mode running",
            "reference measurement running", None,
            "non-logarithmic dimming curve active"]


class QueryDimmerStatus(_IncandescentCommand):
    """Query Dimmer Status"""
    _cmdval = 0xef
    response = DimmerStatusResponse


class FeaturesByte1Response(command.BitmapResponse):
    bits = ["load over-current shutdown can be queried",
            "open circuit detection can be queried",
            "detection of load decrease can be queried",
            "detection of load increase can be queried",
            None,
            "thermal shutdown can be queried",
            "thermal overload with output level reduction can be queried",
            "physical selection supported"]


class FeaturesByte2Response(command.BitmapResponse):
    bits = ["temperature can be queried",
            "supply voltage can be queried",
            "supply frequency can be queried",
            "load voltage can be queried",
            "load current can be queried",
            "real load power can be queried",
            "load rating can be queried",
            "load current overload with output level reduction can be queried"]


class FeaturesByte3Response(command.BitmapResponse):
    bits = [None, None, None,
            "non-logarithmic dimming curve can be selected",
            None, None, None, "load unsuitable can be queried"]
    _dimming_methods = ["leading & trailing", "leading only",
                        "trailing only", "sine wave"]

    @property
    def dimming_method(self):
        if self._value:
            return self._dimming_methods[self._value[1:0]]


class QueryFeatures(_IncandescentCommand):
    """Query Features

    There are three bytes of feature information.  Byte 1 is the reply
    to this command.  Byte 2 is transferred to DTR0 and byte 3 is
    transferred to DTR1.
    """
    _cmdval = 0xf0
    uses_dtr0 = True
    uses_dtr1 = True
    response = FeaturesByte1Response


class FailureStatusByte1Response(command.BitmapResponse):
    bits = ["load over-current shutdown",
            "open circuit detected",
            "load decrease detected",
            "load increase detected",
            None,
            "thermal shutdown",
            "thermal overload with output level reduction",
            "reference measurement failed"]


class FailureStatusByte2Response(command.BitmapResponse):
    bits = ["load not suitable for selected dimming method",
            "supply voltage out of limits",
            "supply frequency out of limits",
            "load voltage out of limits",
            "load current overload with output level reduction"]


class QueryFailureStatus(_IncandescentCommand):
    """Query Failure Status

    Responds with byte 1 of the failure status information, and
    transfers byte 2 of the failure status into DTR1.

    Failure states which cause output level reduction shall only be
    reset by re-powering the control gear or by any command that
    causes the output to turn off.

    Failure states which cause shutdown shall only be reset by
    re-powering the control gear or using an optional reset switch on
    the control gear.
    """
    _cmdval = 0xf1
    uses_dtr1 = True
    response = FailureStatusByte1Response


class QueryDimmerTemperature(_IncandescentCommand):
    """Query Dimmer Temperature

    Returns the temperature of the dimmer with 1 degC resolution.
    Values of 0 to 254 represent temperatures of -40C to +214C.  Below
    -40C, 0 is returned.  Above 214C, 254 is returned.  A value of 255
    means "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf2
    # XXX add a temperature response class?
    response = command.Response


class VoltageResponse(command.Response):
    pass


class QueryRMSSupplyVoltage(_IncandescentCommand):
    """Query RMS Supply Voltage

    Returns the measured supply voltage.  Values of 0 to 254 represent
    0V to 508V RMS.  Voltages above 508V RMS shall be returned as 254.
    A value of 255 means "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf3
    response = VoltageResponse


class QuerySupplyFrequency(_IncandescentCommand):
    """Query Supply Frequency

    Returns the supply frequency with 0.5Hz resolution, so values of 0
    to 254 represent 0Hz to 127Hz.  Frequencies above 127Hz are
    returned as 254.  A value of 255 means "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf4
    response = command.Response


class QueryRMSLoadVoltage(_IncandescentCommand):
    """Query RMS Load Voltage

    Returns the measured load voltage.  Values of 0 to 254 represent
    0V to 508V RMS.  Voltages above 508V RMS shall be returned as 254.
    A value of 255 means "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf5
    response = VoltageResponse


class QueryRMSLoadCurrent(_IncandescentCommand):
    """Query RMS Load Current

    Returns the measured load current as a percentage of the rated
    load current given by the answer to QueryLoadRating, with 0.5%
    resolution.  Values of 0 to 254 represent 0% to 127%.  Higher
    currents shall be returned as 254.  A value of 255 means
    "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf6
    response = command.Response


class QueryRealLoadPower(_IncandescentCommand):
    """Query Real Load Power

    Returns the high byte of the real power supplied to the load.  The
    low byte is transferred to DTR0.  Values of 0 to 65534 represent
    powers from 0W to 16383.5W with a resolution of 0.25W.  Powers
    above this range are returned as 65534.  A value of 65535 means
    "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf7
    uses_dtr0 = True
    response = command.Response


class QueryLoadRating(_IncandescentCommand):
    """Query Load Rating

    Returns the maximum load current rating with 150mA resolution, so
    values of 0 to 254 represent 0A to 38.1A RMS.  Currents above
    38.1A shall be returned as 254.  A value of 255 means "unknown".

    Control gear without this feature shall not react.
    """
    _cmdval = 0xf8
    response = command.Response


class QueryReferenceRunning(_IncandescentCommand):
    """Query Reference Running

    Asks if the ReferenceSystemPower measurement is running.
    """
    _cmdval = 0xf9
    response = command.YesNoResponse


class QueryReferenceMeasurementFailed(_IncandescentCommand):
    """Query Reference Measurement Failed

    Asks if the reference measurement started by ReferenceSystemPower
    failed.
    """
    _cmdval = 0xfa
    response = command.YesNoResponse

class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _IncandescentCommand):
    pass
