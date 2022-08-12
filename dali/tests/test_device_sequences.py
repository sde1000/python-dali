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
    SetEventFilter,
)
from dali.device.helpers import DeviceInstanceTypeMapper, check_bad_rsp
from dali.device.pushbutton import InstanceEventFilter as EventFilter_pb
from dali.device.sequences import (
    QueryEventFilters,
    SetEventFilters,
    SetEventSchemes,
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
