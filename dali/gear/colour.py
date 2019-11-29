"""Commands and responses from IEC 62386 part 208."""

from __future__ import unicode_literals
from dali import command
from dali.gear.general import _StandardCommand
from enum import Enum


class QueryColourValueVariables(Enum):
    XCoordinate = 0
    YCoordinate = 1
    ColourTemperatureTC = 2
    RedDimLevel = 9
    GreenDimLevel = 10
    BlueDimLevel = 11
    WhiteDimLevel = 12
    AmberDimLevel = 13
    FreecolourDimLevel = 14
    RGBWAFControl = 15

    @property
    def dtrVal(self) -> int:
        return self.value


class _ColourCommand(_StandardCommand):
    _devicetype = 0x08


class SetTemporaryXCoordinate(_ColourCommand):
    _cmdval = 0xE0


class SetTemporaryYCoordinate(_ColourCommand):
    _cmdval = 0xE1


class SetTemporaryRGBDimLevel(_ColourCommand):
    _cmdval = 0xEB


class SetTemporaryWAFDimLevel(_ColourCommand):
    _cmdval = 0xEC


class SetTemporaryRGBWAFControl(_ColourCommand):
    _cmdval = 0xED


class Activate(_ColourCommand):
    _cmdval = 0xE2


class QueryGearFeaturesStatusResponse(command.BitmapResponseBitDict):
    """Retrive gear feature/status info byte from the gear:
    Bit 0: automatic ativation; 0 = NO
    Bit 1..5: reserved
    Bit 6: automatic callibration supported; 0 = NOT SUPPORTED
    Bit 7: automatic callibration recovery supported; 0 = NOT SUPPORTED
    """
    bits = {0: "auto activation enabled", 6: "auto calibration supported", 7: "auto calibration recovery supported"}


class QueryGearFeaturesStatus(_ColourCommand):
    _cmdval = 0xF7
    _response = QueryGearFeaturesStatusResponse


class QueryColourStatusResponse(command.BitmapResponse):
    """Retrive gear colour status information:
    Bit 0: xy-coordinate colour point out of range; 0 = NO
    Bit 1: colour temperature Tc out of range; 0 = NO
    Bit 2: auto calibration running; 0 = NO
    Bit 3: auto calibration successful; 0 = NO
    Bit 4: colour type xy-coordinate active; 0 = NO
    Bit 5: colour type colour temperature Tc active; 0 = NO
    Bit 6: colour type primary N active; 0 = NO
    Bit 7: colour type RGBWAF active; 0 = NO
    """
    bits = ["xy-coord point out of range", "Tc temperature out of range", "Auto calibration running",
            "type xy-coord active", "type Tc temperature active", "type primary N active", "type RGBWAF active"]


class QueryColourStatus(_ColourCommand):
    _cmdval = 0xF8
    _response = QueryColourStatusResponse


class QueryColourTypeFeaturesResponse(command.BitmapResponse):
    """Retrieve gear supported colour type features:

    Bit 0: xy-coordinate
    Bit 1: colour temperature Tc
    Bit 2: primary N
    Bit 2: RGBWAF
    """
    bits = ["xy-coordinate", "colour temperature Tc", "primary N", "RGBWAF"]


class QueryColourTypeFeatures(_ColourCommand):
    _cmdval = 0xF9
    _response = QueryColourTypeFeaturesResponse


class QueryColourValue(_ColourCommand):
    _cmdval = 0xFA
    _response = command.NumericResponse
