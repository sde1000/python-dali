import pytest

from dali.address import DeviceShort, InstanceNumber
from dali.command import NumericResponse, YesNoResponse
from dali.device import pushbutton
from dali.device.general import (
    DTR0,
    EventScheme,
    QueryDeviceStatus,
    QueryDeviceStatusResponse,
    QueryEventFilterZeroToSeven,
    QueryEventScheme,
    QueryEventSchemeResponse,
    QueryInputValue,
    QueryInputValueLatch,
    QueryResolution,
    SetEventFilter,
)
from dali.device.helpers import DeviceInstanceTypeMapper, check_bad_rsp
from dali.device.pushbutton import InstanceEventFilter as EventFilter_pb
from dali.device.sequences import (
    QueryEventFilters,
    SetEventFilters,
    SetEventSchemes,
    query_input_value,
)
from dali.frame import BackwardFrame, BackwardFrameError
from dali.tests import fakes


def test_check_bad_rsp_none():
    # A 'None' is always a bad response
    assert check_bad_rsp(None)


def test_check_bad_rsp_yes():
    # A 'Yes' is always a good response
    assert not check_bad_rsp(YesNoResponse(BackwardFrame(0xFF)))


def test_check_bad_rsp_numeric():
    # A numeric is always a good response, even if 0
    assert not check_bad_rsp(NumericResponse(BackwardFrame(0xFF)))
    assert not check_bad_rsp(NumericResponse(BackwardFrame(0x00)))


def test_check_bad_rsp_missing():
    # A numeric response expects a value
    assert check_bad_rsp(NumericResponse(None))


def test_check_bad_rsp_framing_error():
    # A numeric response expects a value
    assert check_bad_rsp(NumericResponse(BackwardFrameError(0xFF)))


@pytest.fixture
def fakes_bus():
    return fakes.Bus(
        [
            fakes.Device(DeviceShort(0), memory_banks=(fakes.FakeBank0,)),
            fakes.Device(DeviceShort(1), memory_banks=(fakes.FakeBank0,)),
            fakes.Device(DeviceShort(2), memory_banks=(fakes.FakeBank0,)),
        ]
    )


def test_device_autodiscover_good(fakes_bus):
    dev_inst_map = DeviceInstanceTypeMapper()
    fakes_bus.run_sequence(dev_inst_map.autodiscover())
    # There are 4 instances on each fake device, and 3 devices, so 12 in total
    assert len(dev_inst_map.mapping) == 12


class DeviceFakeError(fakes.Device):
    # Refer to Table 15 of Part 103, status bit 0 is "inputDeviceError"
    _device_status = 0b00000001


def test_device_autodiscover_skip_bad(fakes_bus):
    dev_inst_map = DeviceInstanceTypeMapper()
    # Add an extra fake device, one with an error bit set
    fakes_bus.gear.append(
        DeviceFakeError(DeviceShort(3), memory_banks=(fakes.FakeBank0,))
    )

    # The input device error bit should show up
    rsp = fakes_bus.send(QueryDeviceStatus(DeviceShort(3)))
    assert isinstance(rsp, QueryDeviceStatusResponse)
    assert rsp.input_device_error

    fakes_bus.run_sequence(dev_inst_map.autodiscover())
    # The device in error mode shouldn't have had its instances counted
    assert len(dev_inst_map.mapping) == 12


class DeviceNoInstances(fakes.Device):
    _instances = []


def test_device_autodiscover_skip_no_instances(fakes_bus):
    dev_inst_map = DeviceInstanceTypeMapper()
    # Add an extra fake device, one with an error bit set
    fakes_bus.gear.append(
        DeviceNoInstances(DeviceShort(3), memory_banks=(fakes.FakeBank0,))
    )

    fakes_bus.run_sequence(dev_inst_map.autodiscover())
    # One device has no instances to count
    assert len(dev_inst_map.mapping) == 12


def test_device_query_event_scheme(fakes_bus):
    rsp = fakes_bus.send(QueryEventScheme(DeviceShort(1), InstanceNumber(1)))
    assert isinstance(rsp, QueryEventSchemeResponse)
    assert rsp.value == EventScheme.device_instance


def test_device_set_event_schemes(fakes_bus):
    rsp = fakes_bus.send(QueryEventScheme(DeviceShort(2), InstanceNumber(3)))
    assert isinstance(rsp, QueryEventSchemeResponse)
    assert rsp.value == EventScheme.device_instance

    rsp = fakes_bus.run_sequence(
        SetEventSchemes(DeviceShort(2), InstanceNumber(3), EventScheme.device)
    )
    assert isinstance(rsp, QueryEventSchemeResponse)
    assert rsp.value == EventScheme.device


def test_device_set_event_filters(fakes_bus):
    rsp = fakes_bus.run_sequence(
        QueryEventFilters(DeviceShort(1), InstanceNumber(2), pushbutton)
    )
    assert isinstance(rsp, EventFilter_pb)
    assert rsp.value == 0

    rsp = fakes_bus.run_sequence(
        SetEventFilters(
            DeviceShort(1),
            InstanceNumber(2),
            EventFilter_pb.short_press | EventFilter_pb.long_press_start,
        )
    )
    assert isinstance(rsp, EventFilter_pb)
    assert EventFilter_pb.short_press in rsp
    assert EventFilter_pb.long_press_start in rsp
    filter_rsp = rsp

    rsp = fakes_bus.run_sequence(
        QueryEventFilters(DeviceShort(1), InstanceNumber(2), EventFilter_pb)
    )
    assert isinstance(rsp, EventFilter_pb)
    assert rsp == filter_rsp


def test_event_filter_pushbutton_sequence_partial():
    """
    Confirms that the SetEventFilters sequence yields the expected
    DALI message objects and sets the correct bit flags for DTR0 for
    pushbutton instances
    """
    filter_to_set = (
        EventFilter_pb.button_released
        | EventFilter_pb.button_stuck_free
        | EventFilter_pb.double_press
    )
    sequence = SetEventFilters(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        filter_value=filter_to_set,
    )
    # The first message the sequence should send is DTR0
    rsp = None
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, DTR0)
    assert cmd.frame.as_byte_sequence[2] == 0b10001001

    # The second message should be SetEventFilter
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, SetEventFilter)
    assert cmd.destination == DeviceShort(0)
    assert cmd.instance == InstanceNumber(0)

    # The third message should be QueryEventFilterZeroToSeven
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryEventFilterZeroToSeven)

    # The sequence should then just return whatever the response is
    rsp = NumericResponse(BackwardFrame(0b10001001))
    ret = None
    try:
        sequence.send(rsp)
    except StopIteration as r:
        ret = r.value
    assert isinstance(ret, EventFilter_pb)
    assert ret == filter_to_set
    assert EventFilter_pb.button_released in ret
    assert EventFilter_pb.button_stuck_free in ret
    assert EventFilter_pb.double_press in ret
    assert EventFilter_pb.short_press not in ret


def test_event_filter_pushbutton_sequence_all():
    filter_to_set = (
        EventFilter_pb.double_press
        | EventFilter_pb.long_press_start
        | EventFilter_pb.button_pressed
        | EventFilter_pb.short_press
        | EventFilter_pb.long_press_repeat
        | EventFilter_pb.button_released
        | EventFilter_pb.long_press_stop
        | EventFilter_pb.button_stuck_free
        | EventFilter_pb.double_press  # Intentional duplicate
    )
    sequence = SetEventFilters(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        filter_value=filter_to_set,
    )
    # The first message the sequence should send is DTR0
    try:
        cmd = sequence.send(None)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, DTR0)
    assert cmd.frame.as_byte_sequence[2] == 0b11111111
    # The previous test for the sequence adequately checks the remaining logic


def test_event_filter_sequence_int():
    # InstanceEventFilter ultimately inherits from int, so it should be
    # possible to use a plain int in the sequence
    sequence = SetEventFilters(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        filter_value=3,
    )
    # The first message the sequence should send is DTR0
    try:
        cmd = sequence.send(None)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, DTR0)
    assert cmd.frame.as_byte_sequence[2] == 3
    # The previous test for the sequence adequately checks the remaining logic


def test_event_filter_sequence_bad_type():
    sequence = SetEventFilters(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        filter_value="double_press",
    )
    # Using a string is not valid, it must be an enum object
    with pytest.raises(TypeError):
        sequence.send(None)

    sequence = QueryEventFilters(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        filter_type=EventFilter_pb.short_press,
    )
    # filter_type needs to be a type, not an instance
    with pytest.raises(TypeError):
        sequence.send(None)


def test_query_input_values_unknown_1bit():
    """
    Reading a device's input register which has a one-bit resolution, with
    no prior information. Device sends 0xff, which is converted to 1.
    """
    sequence = query_input_value(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        resolution=None,
    )
    rsp = None
    # No resolution was given, so the first message sends out a query for that
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryResolution)
    assert cmd.frame.as_byte_sequence[2] == 0x81  # QUERY_RESOLUTION
    rsp = NumericResponse(BackwardFrame(1))

    # Ask for the first byte
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryInputValue)
    assert cmd.frame.as_byte_sequence[2] == 0x8c  # QUERY_INPUT_VALUE
    assert cmd.destination == DeviceShort(0)
    assert cmd.instance == InstanceNumber(0)

    rsp = NumericResponse(BackwardFrame(0xff))
    ret = None
    try:
        cmd = sequence.send(rsp)
        raise RuntimeError()
    except StopIteration as r:
        ret = r.value

    assert ret == 1


def test_query_input_values_10bit():
    """
    Reading a device's input register. The resolution is known upfront to be
    10bit. The first byte is:

      0x6c = 0110 1100

    The second byte is:

      0x9b = 1001 1011

    And since only the first two bits are needed (10-8), the rest is just
    repeated first byte, so the result is 0b0110110010 = 434.
    """
    sequence = query_input_value(
        device=DeviceShort(0),
        instance=InstanceNumber(0),
        resolution=10,
    )
    rsp = None
    # resolution is known upfront, so there will be no querying
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryInputValue)
    assert cmd.frame.as_byte_sequence[2] == 0x8c  # QUERY_INPUT_VALUE
    assert cmd.destination == DeviceShort(0)
    assert cmd.instance == InstanceNumber(0)
    rsp = NumericResponse(BackwardFrame(0x6c))
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryInputValueLatch)
    assert cmd.frame.as_byte_sequence[2] == 0x8d  # QUERY_INPUT_VALUE_LATCH
    assert cmd.destination == DeviceShort(0)
    assert cmd.instance == InstanceNumber(0)
    rsp = NumericResponse(BackwardFrame(0x9b))

    ret = None
    try:
        cmd = sequence.send(rsp)
        raise RuntimeError()
    except StopIteration as r:
        ret = r.value
    assert ret == 434
