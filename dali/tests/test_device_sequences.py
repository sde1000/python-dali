import pytest

from dali.address import DeviceShort, InstanceNumber
from dali.command import NumericResponse
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
    QueryNumberOfInstances,
    QueryResolution,
    SetEventFilter,
)
from dali.device.helpers import DeviceInstanceTypeMapper
from dali.device.pushbutton import InstanceEventFilter as EventFilter_pb
from dali.device.sequences import (
    Commissioning,
    QueryEventFilters,
    SetEventFilters,
    SetEventSchemes,
    query_input_value,
)
from dali.frame import BackwardFrame, BackwardFrameError
from dali.tests import fakes


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


def test_device_autodiscover_dont_skip_bad(fakes_bus):
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
    # The mere fact that a device has "inputDeviceError" set does not mean it is not usable
    assert len(dev_inst_map.mapping) == 16


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


def test_device_autodiscover_retries_collided_status(fakes_bus):
    """A status probe that collides with an event is retried, not skipped.

    A spontaneous event from a device can corrupt the backward frame of the
    first status probe; without a retry the whole device (and all its
    instances) would be silently dropped from the scan.
    """
    dev_inst_map = DeviceInstanceTypeMapper()
    real_send = fakes_bus.send
    collided = {"done": False}

    def send_with_one_collision(cmd):
        if (
            not collided["done"]
            and isinstance(cmd, QueryDeviceStatus)
            and getattr(cmd.destination, "address", None) == 0
        ):
            collided["done"] = True
            return QueryDeviceStatusResponse(BackwardFrameError(0xFF))
        return real_send(cmd)

    fakes_bus.send = send_with_one_collision
    fakes_bus.run_sequence(dev_inst_map.autodiscover())

    assert collided["done"]
    assert any(addr == 0 for addr, _instance in dev_inst_map.mapping)
    assert len(dev_inst_map.mapping) == 12


def test_device_autodiscover_absent_address_probed_once(fakes_bus):
    """An empty address returns a missing (not collided) status, so it is not
    retried; only a framing-error reply triggers the extra probes."""
    probes: list[int] = []
    real_send = fakes_bus.send

    def counting_send(cmd):
        if isinstance(cmd, QueryDeviceStatus):
            probes.append(getattr(cmd.destination, "address", None))
        return real_send(cmd)

    fakes_bus.send = counting_send
    fakes_bus.run_sequence(
        DeviceInstanceTypeMapper().autodiscover(addresses=(0, 5))
    )

    # Addresses 3-5 have no device, so each is probed exactly once.
    assert probes.count(3) == 1
    assert probes.count(4) == 1
    assert probes.count(5) == 1


def test_device_autodiscover_caps_instance_count(fakes_bus):
    """A device reporting more than 32 instances does not abort the scan.

    Instance numbers are 0..31, so a count above 32 (a non-conformant device,
    or a value whose backward frame collided with an event) must not build an
    out-of-range InstanceNumber and crash the whole scan; the count is capped
    and the device's real instances are still enumerated.
    """
    dev_inst_map = DeviceInstanceTypeMapper()
    real_send = fakes_bus.send

    def send_with_bad_count(cmd):
        if isinstance(cmd, QueryNumberOfInstances) and (
            getattr(cmd.destination, "address", None) == 0
        ):
            return NumericResponse(BackwardFrame(255))
        return real_send(cmd)

    fakes_bus.send = send_with_bad_count
    fakes_bus.run_sequence(dev_inst_map.autodiscover())

    # Device 0's four real instances are still found despite the bogus count.
    assert sum(1 for addr, _instance in dev_inst_map.mapping if addr == 0) == 4
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


# There used to be a test_event_filter_sequence_int() test here. Its
# comment said:

# InstanceEventFilter ultimately inherits from int, so it should be
# possible to use a plain int in the sequence

# This breaks type checking, so the test has been removed.


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


def _short_addresses(devices: list[fakes.Device]) -> list[int]:
    """Return the sorted short addresses of the devices that have one."""
    return sorted(
        d.shortaddr.address for d in devices if d.shortaddr is not None
    )


def test_device_commissioning():
    devices = [fakes.Device() for _ in range(10)]
    bus = fakes.Bus(devices)

    used = bus.run_sequence(Commissioning())

    assert _short_addresses(devices) == list(range(10))
    assert sorted(a.address for a in used) == list(range(10))
    # Quiescent mode must be exited for every device once addressing completes.
    assert all(not d.quiescent for d in devices)


def test_device_commissioning_adds_new_without_readdress():
    devices = [fakes.Device() for _ in range(10)]
    bus = fakes.Bus(devices)
    bus.run_sequence(Commissioning())

    # Move one device out to address 30 and add 10 fresh unaddressed devices.
    # bus.gear is the same list object, so appending once adds them to the bus.
    devices[5].shortaddr = DeviceShort(30)
    for _ in range(10):
        devices.append(fakes.Device())

    bus.run_sequence(Commissioning())

    # Existing addresses are kept; new devices fill the lowest free addresses.
    assert _short_addresses(devices) == list(range(19)) + [30]


def test_device_commissioning_readdress_dry_run_keeps_addresses():
    devices = [fakes.Device(DeviceShort(i + 20)) for i in range(10)]
    bus = fakes.Bus(devices)
    before = _short_addresses(devices)

    bus.run_sequence(Commissioning(readdress=True, dry_run=True))

    assert _short_addresses(devices) == before


def test_device_commissioning_readdress():
    devices = [fakes.Device(DeviceShort(i + 20)) for i in range(10)]
    bus = fakes.Bus(devices)

    bus.run_sequence(Commissioning(readdress=True))

    assert _short_addresses(devices) == list(range(10))


def test_device_commissioning_clash():
    # At least one device picks the same random address as another on the
    # first pass, forcing a re-randomise.
    randoms = list(range(0, 0xFFFFFF, 0x82000))
    randoms[8] = randoms[4]
    devices = [fakes.Device(random_preload=[x]) for x in randoms]
    bus = fakes.Bus(devices)

    bus.run_sequence(Commissioning())

    assert _short_addresses(devices) == list(range(len(devices)))


def test_device_commissioning_high_random_address():
    # One of the devices is persistently going to pick 0xffffff as
    # its random address
    devices = [fakes.Device() for x in range(9)]
    devices.append(fakes.Device(random_preload=[0xffffff] * 10))
    bus = fakes.Bus(devices)

    bus.run_sequence(Commissioning())

    assert _short_addresses(devices) == list(range(len(devices)))


def test_device_commissioning_restricted_addresses():
    devices = [fakes.Device() for _ in range(10)]
    bus = fakes.Bus(devices)

    bus.run_sequence(Commissioning(available_addresses=range(10, 15)))

    addressed = _short_addresses(devices)
    assert all(10 <= a < 15 for a in addressed)
    assert len(addressed) == 5
    assert sum(d.shortaddr is None for d in devices) == 5
