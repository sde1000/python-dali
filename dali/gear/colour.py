"""Commands and responses from IEC 62386 part 208."""

from __future__ import unicode_literals
from dali import command
from dali.gear.general import _StandardCommand
from enum import Enum

class QueryValueVariables(Enum):
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

class SetTemporaryRGBWAFControl(_ColourCommand):
    _cmdval = 0xED

class Activate(_ColourCommand):
    _cmdval = 0xE2

class QueryGearFeatures(_ColourCommand):
    _cmdval = 0xF7
    _response = command.NumericResponse

class QueryColourValue(_ColourCommand):
    _cmdval = 0xFA
    _response = command.NumericResponse