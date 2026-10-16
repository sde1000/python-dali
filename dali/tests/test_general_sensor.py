"""Tests for IEC 62386 part 306 general sensor support."""

from dali.address import DeviceShort, InstanceNumber
from dali.device import general, general_sensor
from dali.device.general_sensor import (
    GeneralSensorEvent,
    MeasurementVariable,
    QuantityName,
    UnitOfMeasurement,
)


def test_measurement_event_round_trip() -> None:
    """Test encoding and decoding a measurement event."""
    event = GeneralSensorEvent(
        short_address=DeviceShort(3),
        data=0x155,
    )

    assert event.measured_value == 0x155
    decoded = general._Event.from_frame(event.frame)
    assert isinstance(decoded, GeneralSensorEvent)
    assert decoded.measured_value == 0x155


def test_non_measurement_event_is_not_general_sensor() -> None:
    """Test Part 306 alarm/reserved payloads are not measurement events."""
    assert GeneralSensorEvent.from_event_data(0x001) is None


def test_measurement_variable_command() -> None:
    """Test the Part 306 measurement-variable query command."""
    command = general_sensor.QueryMeasurementVariable(DeviceShort(1), InstanceNumber(2))

    assert command._opcode == 0x5F
    assert command.uses_dtr0
    assert command.response is not None


def test_part_306_constants() -> None:
    """Test normative quantity and unit constants."""
    assert general_sensor.instance_type == 6
    assert MeasurementVariable.QUANTITY_NAME == 0x1E
    assert QuantityName.TEMPERATURE == 26
    assert QuantityName.RELATIVE_HUMIDITY == 29
    assert QuantityName.PRESSURE == 31
    assert QuantityName.CO2 == 34
    assert QuantityName.VOC == 36
    assert QuantityName.AIR_QUALITY_INDEX == 46
    assert UnitOfMeasurement.CELSIUS == 9
    assert UnitOfMeasurement.PASCAL == 16
    assert UnitOfMeasurement.PERCENT == 50
    assert UnitOfMeasurement.PARTS_PER_MILLION == 53
