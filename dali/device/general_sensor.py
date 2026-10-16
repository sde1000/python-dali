"""Commands and events from IEC 62386 part 306: General sensors."""

from __future__ import annotations

from typing import Optional
from enum import IntEnum

from dali import command, frame
from dali.device import general

# IEC 62386-306 instance type.
instance_type = 6


class MeasurementVariable(IntEnum):
    """DTR0 values for QUERY MEASUREMENT VARIABLE, from Part 306 Table 17.

    Note: each QUERY MEASUREMENT VARIABLE execution auto-increments DTR0 by 1,
    so DTR0 must be set again before every single-byte read.
    """

    ALARM_IS_ACTIVATED = 0x00
    ALARM_TYPE = 0x01
    INPUT_SIGNAL_SIGNED = 0x02
    ALARM_0_BYTE_0 = 0x03
    ALARM_0_BYTE_1 = 0x04
    ALARM_0_BYTE_2 = 0x05
    ALARM_1_BYTE_0 = 0x06
    ALARM_1_BYTE_1 = 0x07
    ALARM_1_BYTE_2 = 0x08
    ALARM_2_BYTE_0 = 0x09
    ALARM_2_BYTE_1 = 0x0A
    ALARM_2_BYTE_2 = 0x0B
    ALARM_3_BYTE_0 = 0x0C
    ALARM_3_BYTE_1 = 0x0D
    ALARM_3_BYTE_2 = 0x0E
    ALARM_0_HYSTERESIS_BYTE_0 = 0x0F
    ALARM_0_HYSTERESIS_BYTE_1 = 0x10
    ALARM_0_HYSTERESIS_BYTE_2 = 0x11
    ALARM_1_HYSTERESIS_BYTE_0 = 0x12
    ALARM_1_HYSTERESIS_BYTE_1 = 0x13
    ALARM_1_HYSTERESIS_BYTE_2 = 0x14
    ALARM_2_HYSTERESIS_BYTE_0 = 0x15
    ALARM_2_HYSTERESIS_BYTE_1 = 0x16
    ALARM_2_HYSTERESIS_BYTE_2 = 0x17
    ALARM_3_HYSTERESIS_BYTE_0 = 0x18
    ALARM_3_HYSTERESIS_BYTE_1 = 0x19
    ALARM_3_HYSTERESIS_BYTE_2 = 0x1A
    UNIT_OF_MEASUREMENT = 0x1B
    UNIT_OF_MEASUREMENT_EXTENDED_0 = 0x1C
    UNIT_OF_MEASUREMENT_EXTENDED_1 = 0x1D
    QUANTITY_NAME = 0x1E
    QUANTITY_NAME_EXTENDED_0 = 0x1F
    QUANTITY_NAME_EXTENDED_1 = 0x20
    MAGNITUDE = 0x21
    MAGNITUDE_PHYSICAL_MAX = 0x22
    MAGNITUDE_PHYSICAL_MIN = 0x23
    MAX_MEASURED_VALUE_BYTE_0 = 0x24
    MAX_MEASURED_VALUE_BYTE_1 = 0x25
    MAX_MEASURED_VALUE_BYTE_2 = 0x26
    MAX_MEASURED_VALUE_BYTE_3 = 0x27
    MIN_MEASURED_VALUE_BYTE_0 = 0x28
    MIN_MEASURED_VALUE_BYTE_1 = 0x29
    MIN_MEASURED_VALUE_BYTE_2 = 0x2A
    MIN_MEASURED_VALUE_BYTE_3 = 0x2B


class UnitOfMeasurement(IntEnum):
    """Standard unit-of-measurement values from Part 306 Annex A, Table A.1."""

    MANUFACTURER_DEFINED = 0
    DIMENSIONLESS = 1
    SECOND = 2
    HERTZ = 3
    METRE = 4
    KILOGRAM = 5
    VOLT = 6
    AMPERE = 7
    KELVIN = 8
    CELSIUS = 9
    FAHRENHEIT = 10
    MOLE = 11
    DEGREE_ANGLE = 12
    RADIAN = 13
    STERADIAN = 14
    NEWTON = 15
    PASCAL = 16
    PSI = 17
    JOULE = 18
    WATT = 19
    COULOMB = 20
    FARAD = 21
    OHM = 22
    SIEMENS = 23
    WEBER = 24
    TESLA = 25
    HENRY = 26
    AMPERE_PER_METRE = 27
    VOLT_PER_METRE = 28
    AMPERE_HOUR = 29
    WATT_HOUR = 30
    LUMEN = 31
    LUX = 32
    CANDELA = 33
    CANDELA_PER_SQUARE_METRE = 34
    BECQUEREL = 35
    GRAY = 36
    SIEVERT = 37
    KATAL = 38
    SQUARE_METRE = 39
    CUBIC_METRE = 40
    METRE_PER_SECOND = 41
    METRE_PER_SECOND_SQUARED = 42
    CUBIC_METRE_PER_SECOND = 43
    KILOGRAM_PER_CUBIC_METRE = 44
    KILOGRAM_PER_SQUARE_METRE = 45
    CUBIC_METRE_PER_KILOGRAM = 46
    FOOT = 47
    NEWTON_METRE = 48
    DECIBEL = 49
    PERCENT = 50
    PART_PER_THOUSAND = 51
    PART_PER_TEN_THOUSAND = 52
    PARTS_PER_MILLION = 53
    DECIBEL_A = 54


class QuantityName(IntEnum):
    """Standard quantity-name values from Part 306 Annex A, Table A.2."""

    MANUFACTURER_DEFINED = 0
    TIME = 1
    FREQUENCY = 2
    LENGTH = 3
    FORCE = 4
    WEIGHT = 5
    MASS = 6
    VELOCITY = 7
    ACCELERATION = 8
    ANGLE = 9
    AREA = 10
    VOLUME = 11
    TORQUE = 12
    VOLTAGE = 13
    CURRENT = 14
    POWER = 15
    POWER_APPARENT = 16
    POWER_REACTIVE = 17
    ENERGY = 18
    POWER_FACTOR = 19
    SOUND_PRESSURE_LEVEL = 20
    CCT = 21
    CRI = 22
    RED_LIGHT = 23
    GREEN_LIGHT = 24
    BLUE_LIGHT = 25
    TEMPERATURE = 26
    WET_BULB_TEMPERATURE = 27
    ABSOLUTE_HUMIDITY = 28
    RELATIVE_HUMIDITY = 29
    DEW_POINT = 30
    PRESSURE = 31
    FLOW_RATE = 32
    SO2 = 33
    CO2 = 34
    CO = 35
    VOC = 36
    NOX = 37
    N2O = 38
    AMMONIA = 39
    OZONE = 40
    CHLORINE = 41
    METHANE = 42
    ACIDITY = 43
    PARTICULATE_MATTER_PM10 = 44
    PARTICULATE_MATTER_PM2_5 = 45
    AIR_QUALITY_INDEX = 46
    RSSI_IBEACON = 47
    RSSI_EDDYSTONE = 48
    RSSI_ALTBEACON = 49
    GLOBAL_POSITION_LONGITUDE = 50
    GLOBAL_POSITION_LATITUDE = 51
    ALTITUDE = 52
    RELATIVE_POSITION_X = 53
    RELATIVE_POSITION_Y = 54
    RELATIVE_POSITION_Z = 55
    WIND_SPEED = 56
    FLUID_LEVEL = 57
    BATTERY_CHARGE = 58
    # Clarifications and Recommendations for IEC 62386:
    GENERAL_PURPOSE_COUNTER = 59
    PEOPLE_COUNTER = 60


class GeneralSensorEvent(general._Event):
    """A Part 306 measured-value event."""

    _instance_type = instance_type
    _event_info = 0x20000

    @classmethod
    def from_event_data(
            cls, event_data: int
    ) -> Optional[type[GeneralSensorEvent]]:
        """Return this event class for a measurement event."""
        return cls if event_data & 0x200 else None

    @property
    def measured_value(self) -> int:
        """Return the 9-bit measured-value event payload."""
        return self.event_data & 0x1FF

    @property
    def event_data(self) -> int:
        """Return the encoded event information."""
        return self._event_info

    def _set_event_data(self, set_data: int, set_frame: frame.Frame) -> None:
        """Encode the measured value into a Part 306 event frame."""
        if not isinstance(set_data, int) or not 0 <= set_data <= 0x3FF:
            raise ValueError("GeneralSensorEvent requires 9-bit event data")
        self._event_info = 0x200 | (set_data & 0x1FF)
        set_frame[9:0] = self._event_info


class InstanceEventFilter(general.InstanceEventFilter):
    """Part 306 event filters."""

    measured_value = 0x01


class QueryMeasurementVariable(general._StandardInstanceCommand):
    """Query a Part 306 measurement variable selected by DTR0.

    Executing this command auto-increments DTR0 by 1, so DTR0 must be set
    again before every single-byte read. See MeasurementVariable.
    """

    inputdev = True
    uses_dtr0 = True
    response = command.NumericResponse
    _opcode = 0x5F
