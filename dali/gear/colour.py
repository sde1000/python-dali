"""
Commands and responses from IEC 62386 part 209, Device Type 8 Colour Control
gear
"""
from __future__ import annotations

from enum import IntEnum

from dali import command
from dali.gear.general import _StandardCommand


class QueryColourValueDTR(IntEnum):
    """
    Enum of all values from Part 209 Table 11 "Query Colour Value". See
    QueryColourValue() for further information.
    """

    XCoordinate = 0
    YCoordinate = 1
    ColourTemperatureTC = 2
    PrimaryNDimLevel0 = 3
    PrimaryNDimLevel1 = 4
    PrimaryNDimLevel2 = 5
    PrimaryNDimLevel3 = 6
    PrimaryNDimLevel4 = 7
    PrimaryNDimLevel5 = 8
    RedDimLevel = 9
    GreenDimLevel = 10
    BlueDimLevel = 11
    WhiteDimLevel = 12
    AmberDimLevel = 13
    FreecolourDimLevel = 14
    RGBWAFControl = 15
    XCoordinatePrimaryN0 = 64
    YCoordinatePrimaryN0 = 65
    TYPrimaryN0 = 66
    XCoordinatePrimaryN1 = 67
    YCoordinatePrimaryN1 = 68
    TYPrimaryN1 = 69
    XCoordinatePrimaryN2 = 70
    YCoordinatePrimaryN2 = 71
    TYPrimaryN2 = 72
    XCoordinatePrimaryN3 = 73
    YCoordinatePrimaryN3 = 74
    TYPrimaryN3 = 75
    XCoordinatePrimaryN4 = 76
    YCoordinatePrimaryN4 = 77
    TYPrimaryN4 = 78
    XCoordinatePrimaryN5 = 79
    YCoordinatePrimaryN5 = 80
    TYPrimaryN5 = 81
    NumberOfPrimaries = 82
    ColourTemperatureTcCoolest = 128
    ColourTemperatureTcPhysicalCoolest = 129
    ColourTemperatureTcWarmest = 130
    ColourTemperatureTcPhysicalWarmest = 131
    TemporaryXCoordinate = 192
    TemporaryYCoordinate = 193
    TemporaryColourTemperature = 194
    TemporaryPrimaryNDimLevel0 = 195
    TemporaryPrimaryNDimLevel1 = 196
    TemporaryPrimaryNDimLevel2 = 197
    TemporaryPrimaryNDimLevel3 = 198
    TemporaryPrimaryNDimLevel4 = 199
    TemporaryPrimaryNDimLevel5 = 200
    TemporaryRedDimLevel = 201
    TemporaryGreenDimLevel = 202
    TemporaryBlueDimLevel = 203
    TemporaryWhiteDimLevel = 204
    TemporaryAmberDimLevel = 205
    TemporaryFreecolourDimLevel = 206
    TemporaryRgbwafControl = 207
    TemporaryColourType = 208
    ReportXCoordinate = 224
    ReportYCoordinate = 225
    ReportColourTemperatureTc = 226
    ReportPrimaryNDimLevel0 = 227
    ReportPrimaryNDimLevel1 = 228
    ReportPrimaryNDimLevel2 = 229
    ReportPrimaryNDimLevel3 = 230
    ReportPrimaryNDimLevel4 = 231
    ReportPrimaryNDimLevel5 = 232
    ReportRedDimLevel = 233
    ReportGreenDimLevel = 234
    ReportBlueDimLevel = 235
    ReportWhiteDimLevel = 236
    ReportAmberDimLevel = 237
    ReportFreecolourDimLevel = 238
    ReportRgbwafControl = 239
    ReportColourType = 240


class _ColourCommand(_StandardCommand):
    devicetype = 0x08


class SetTemporaryXCoordinate(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    _cmdval = 224


class SetTemporaryYCoordinate(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    _cmdval = 225


class Activate(_ColourCommand):
    _cmdval = 226


class XCoordinateStepUp(_ColourCommand):
    _cmdval = 227


class XCoordinateStepDown(_ColourCommand):
    _cmdval = 228


class YCoordinateStepUp(_ColourCommand):
    _cmdval = 229


class YCoordinateStepDown(_ColourCommand):
    _cmdval = 230


class SetTemporaryColourTemperature(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    _cmdval = 231


class ColourTemperatureTcStepCooler(_ColourCommand):
    _cmdval = 232


class ColourTemperatureTcStepWarmer(_ColourCommand):
    _cmdval = 233


class SetTemporaryPrimaryNDimLevel(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    _cmdval = 234


class SetTemporaryRGBDimLevel(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    _cmdval = 235


class SetTemporaryWAFDimLevel(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    _cmdval = 236


class SetTemporaryRGBWAFControl(_ColourCommand):
    uses_dtr0 = True
    _cmdval = 237


class CopyReportToTemporary(_ColourCommand):
    _cmdval = 238


class StoreTYPrimaryN(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    _cmdval = 240


class StoreXYCoordinatePrimaryN(_ColourCommand):
    uses_dtr2 = True
    _cmdval = 241


class StoreColourTemperatureTcLimit(_ColourCommand):
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    _cmdval = 242


class StoreGearFeaturesStatus(_ColourCommand):
    uses_dtr0 = True
    _cmdval = 243


class AssignColourToLinkedChannel(_ColourCommand):
    uses_dtr0 = True
    _cmdval = 245


class StartAutoCalibration(_ColourCommand):
    _cmdval = 246


class QueryGearFeaturesStatusResponse(command.BitmapResponse):
    """
    Gear Features Status for a DT8 control gear, as defined in Part 209
    section 11.3.4.3, Command 247 "QUERY GEAR FEATURES/STATUS".
    """

    bits = [
        "auto activation enabled",
        "reserved 1",
        "reserved 2",
        "reserved 3",
        "reserved 4",
        "reserved 5",
        "auto calibration supported",
        "auto calibration recovery supported",
    ]


class QueryGearFeaturesStatus(_ColourCommand):
    _cmdval = 247
    response = QueryGearFeaturesStatusResponse


class QueryColourStatusResponse(command.BitmapResponse):
    """
    Colour Status for a DT8 control gear, as defined in Part 209 section
    11.3.4.3, Command 248 "QUERY COLOUR STATUS".
    """

    bits = [
        "xy colour point out of range",
        "colour temperature Tc out of range",
        "auto calibration running",
        "auto calibration successful",
        "colour type xy active",
        "colour type colour temperature Tc active",
        "colour type primary N active",
        "colour type RGBWAF active",
    ]


class QueryColourStatus(_ColourCommand):
    _cmdval = 248
    response = QueryColourStatusResponse


class QueryColourTypeFeaturesResponse(command.BitmapResponse):
    """
    Colour Type Features for a DT8 control gear, as defined in Part 209
    section 11.3.4.3, Command 249 "QUERY COLOUR TYPE FEATURES".
    """

    bits = [
        "xy capable",
        "Tc capable",
        "primary N bit 0",
        "primary N bit 1",
        "primary N bit 2",
        "RGBWAF channels bit 0",
        "RGBWAF channels bit 1",
        "RGBWAF channels bit 2",
    ]

    @property
    def primary_n(self) -> int:
        """
        Returns the number of primaries supported by the control gear
        """
        count = self.primary_N_bit_2 << 2
        count += self.primary_N_bit_1 << 1
        count += self.primary_N_bit_0
        return count

    @property
    def RGBWAF_channels(self) -> int:
        """
        Returns the number of RGBWAF channels supported by the control gear
        """
        count = self.RGBWAF_channels_bit_2 << 2
        count += self.RGBWAF_channels_bit_1 << 1
        count += self.RGBWAF_channels_bit_0
        return count


class QueryColourTypeFeatures(_ColourCommand):
    _cmdval = 249
    response = QueryColourTypeFeaturesResponse


class QueryColourValue(_ColourCommand):
    """
    The answer to QueryColourValue depends on the DTR Value. (see
    QueryColourValueDTR enum). Most responses involve a 16-bit number,
    in such cases the reponse is the MSB and LSB is loaded into DTR0. See
    Part 209 Table 11 and Table 15 for full details.

    Note: A control device should always use QueryActualLevel to update the
    reported colour setting before querying.
    """

    _cmdval = 250
    response = command.NumericResponseMask


class QueryRBGWAFControlResponse(command.BitmapResponse):
    bits = [
        "channel 0 red",
        "channel 1 green",
        "channel 2 blue",
        "channel 3 white",
        "channel 4 amber",
        "channel 5 freecolour",
        "control type bit 0",
        "control type bit 1",
    ]

    @property
    def control_type(self) -> str:
        """
        Returns the "Control Type" for the RGBWAF function, one of:
        * channel control
        * colour control
        * normalised colour control
        """
        count = self.control_type_bit_1 << 1
        count += self.control_type_bit_0
        if count == 0:
            return "channel control"
        elif count == 1:
            return "colour control"
        elif count == 2:
            return "normalised colour control"
        else:
            return "(error)"


class QueryRBGWAFControl(_ColourCommand):
    _cmdval = 251
    response = QueryRBGWAFControlResponse


class AssignedColour(IntEnum):
    """
    Enum of all values from Part 209 Table 12 "Query Assigned Colour"
    """

    not_assigned = 0
    red = 1
    green = 2
    blue = 3
    white = 4
    amber = 5
    freecolour = 6


class QueryAssignedColourResponse(command.EnumResponse):
    """
    Assigned colour for a given channel (as specified in DTR0). Refer to Part
    209 section 11.3.4.3, Command 252 "QUERY ASSIGNED COLOUR".

    Note that a response may indicate an assigned channel, or could also be
    "MASK" if the queried channel is not supported or is invalid.
    """

    enumerator = AssignedColour

    @property
    def value(self):
        if self.raw_value is None:
            return None
        _value = self.raw_value.as_integer
        if 6 < _value < 255:
            return "(error)"
        elif _value == 255:
            return "MASK"
        else:
            return super().value


class QueryAssignedColour(_ColourCommand):
    """
    The answer shall be the number of the assigned colour (see AssignedColour
    class) of the output channel given by the DTR. The DTR shall contain one of
    the channel numbers 0 to 5. For all other values of DTR and unsupported
    channel numbers the answer shall be “MASK”.
    """

    uses_dtr0 = True
    _cmdval = 252
    response = QueryAssignedColourResponse


class QueryExtendedVersionNumber(_ColourCommand):
    _cmdval = 255
    response = command.NumericResponse
