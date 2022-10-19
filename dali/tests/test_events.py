from dataclasses import dataclass
from typing import Any, Optional, Type

import pytest

from dali.command import Command
from dali.device import general, pushbutton
from dali.device.general import (
    AmbiguousInstanceType,
    EventScheme,
    InstanceEventFilter,
    QueryEventSchemeResponse,
    UnknownEvent,
    _Event,
)
from dali.device.helpers import DeviceInstanceTypeMapper
from dali.device.occupancy import OccupancyEvent
from dali.device.light import LightEvent
from dali.device.pushbutton import InstanceEventFilter as EventFilter_pb
from dali.frame import BackwardFrame, ForwardFrame, Frame


def test_event_base_not_implemented():
    with pytest.raises(NotImplementedError):
        general._Event()


@pytest.fixture
def event_test_data_good():
    @dataclass
    class EventTestData:
        event_type: Type[_Event] = general._Event
        short_address: Optional[int] = None
        instance_number: Optional[int] = None
        instance_group: Optional[int] = None
        device_group: Optional[int] = None
        frame: str = "000000000000000000000000"
        data: Any = None

    test_data = (
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            instance_group=2,
            frame="110001000000010000000000",
        ),
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            instance_group=31,
            frame="111111100000010000000000",
        ),
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            instance_group=0,
            frame="110000000000010000000000",
        ),
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            instance_number=2,
            frame="100000101000100000000000",
        ),
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            instance_number=31,
            frame="100000101111110000000000",
        ),
        EventTestData(
            event_type=pushbutton.ShortPress,
            instance_group=31,
            frame="111111100000010000000010",
        ),
        EventTestData(
            event_type=pushbutton.DoublePress,
            instance_group=31,
            frame="111111100000010000000101",
        ),
        EventTestData(
            event_type=pushbutton.LongPressStart,
            device_group=15,
            frame="100111100000010000001001",
        ),
        EventTestData(
            event_type=pushbutton.LongPressRepeat,
            device_group=15,
            frame="100111100000010000001011",
        ),
        EventTestData(
            event_type=pushbutton.LongPressStop,
            device_group=16,
            frame="101000000000010000001100",
        ),
        EventTestData(
            event_type=pushbutton.ButtonPressed,
            instance_number=17,
            frame="100000101100010000000001",
        ),
        EventTestData(
            event_type=pushbutton.ButtonReleased,
            short_address=0,
            frame="000000000000010000000000",
        ),
        EventTestData(
            event_type=pushbutton.ShortPress,
            short_address=63,
            frame="011111100000010000000010",
        ),
        EventTestData(
            event_type=OccupancyEvent,
            short_address=0,
            frame="000000000000110000001011",
            data=OccupancyEvent.EventData(movement=True, occupied=True),
        ),
        EventTestData(
            event_type=OccupancyEvent,
            short_address=0,
            frame="000000000000110000001010",
            data=OccupancyEvent.EventData(movement=False, occupied=True),
        ),
        EventTestData(
            event_type=OccupancyEvent,
            short_address=0,
            frame="000000000000110000000010",
            data=OccupancyEvent.EventData(
                movement=False, occupied=True, sensor_type="presence"
            ),
        ),
        EventTestData(
            event_type=OccupancyEvent,
            short_address=63,
            frame="011111100000110000001111",
            data=OccupancyEvent.EventData(
                movement=True, occupied=True, repeat=True
            ),
        ),
        EventTestData(
            event_type=LightEvent,
            short_address=1,
            frame="000000100001001010101010",
            data=682,
        ),
    )
    return test_data


def test_event_to_frame_good(event_test_data_good):
    """
    Tests a number of values against known-good expected frames, for various
    events
    """
    for test_case in event_test_data_good:
        event = test_case.event_type(
            short_address=test_case.short_address,
            instance_number=test_case.instance_number,
            instance_group=test_case.instance_group,
            device_group=test_case.device_group,
            data=test_case.data,
        )
        event_frame = f"{event.frame.as_integer:024b}"
        assert event_frame == test_case.frame


def test_frame_to_event_good(event_test_data_good):
    """
    Tests a number of known-good frames, to ensure the correct object is
    decoded
    """
    for test_case in event_test_data_good:
        test_frame = Frame(24, data=int(test_case.frame, base=2))
        event = Command.from_frame(test_frame)
        assert isinstance(event, test_case.event_type)
        if test_case.short_address:
            assert event.short_address.address == test_case.short_address
        assert event.instance_number == test_case.instance_number
        assert event.instance_group == test_case.instance_group
        assert event.device_group == test_case.device_group
        assert event.event_data == test_case.data


def test_event_pushbutton_repr_short_address():
    event = pushbutton.ButtonReleased(short_address=1)
    event_str = f"{event}"
    assert "ButtonReleased(short_address=1)" == event_str


def test_event_pushbutton_repr_instance_number():
    event = pushbutton.ButtonReleased(instance_number=2)
    event_str = f"{event}"
    assert "ButtonReleased(instance_number=2)" == event_str


def test_event_pushbutton_repr_instance_group():
    event = pushbutton.ButtonReleased(instance_group=3)
    event_str = f"{event}"
    assert "ButtonReleased(instance_group=3)" == event_str


def test_event_pushbutton_repr_device_group():
    event = pushbutton.ButtonReleased(device_group=31)
    event_str = f"{event}"
    assert "ButtonReleased(device_group=31)" == event_str


def test_frame_to_ambiguous_event():
    dev_inst_frame = Frame(24, data=0b000000101000010000000010)
    decode_cmd = Command.from_frame(dev_inst_frame)
    assert isinstance(decode_cmd, general.AmbiguousInstanceType)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1
    assert decode_cmd.event_data == 0b0000000010


def test_frame_to_event_dev_inst_pushbutton():
    device_instance_map = DeviceInstanceTypeMapper()
    device_instance_map.add_type(
        short_address=1,
        instance_number=1,
        instance_type=pushbutton,
    )

    dev_inst_frame = Frame(24, data=0b000000101000010000000010)
    decode_cmd = Command.from_frame(
        dev_inst_frame, dev_inst_map=device_instance_map
    )

    assert isinstance(decode_cmd, pushbutton.ShortPress)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1


def test_event_decode_retry():
    device_instance_map = DeviceInstanceTypeMapper()
    device_instance_map.add_type(
        short_address=1,
        instance_number=1,
        instance_type=pushbutton,
    )

    dev_inst_frame = Frame(24, data=0b000000101000010000000010)
    decode_cmd = Command.from_frame(dev_inst_frame, dev_inst_map=None)

    assert isinstance(decode_cmd, AmbiguousInstanceType)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1
    retry = decode_cmd.retry_decode(device_instance_map)
    assert isinstance(retry, pushbutton.ShortPress)
    assert retry.short_address.address == 1
    assert retry.instance_number == 1


def test_event_scheme_response_good():
    rsp = QueryEventSchemeResponse(BackwardFrame(0))
    assert rsp.value == EventScheme.instance

    rsp = QueryEventSchemeResponse(BackwardFrame(1))
    assert rsp.value == EventScheme.device

    rsp = QueryEventSchemeResponse(BackwardFrame(2))
    assert rsp.value == EventScheme.device_instance

    rsp = QueryEventSchemeResponse(BackwardFrame(3))
    assert rsp.value == EventScheme.device_group

    rsp = QueryEventSchemeResponse(BackwardFrame(4))
    assert rsp.value == EventScheme.instance_group


def test_event_scheme_response_bad():
    rsp = QueryEventSchemeResponse(BackwardFrame(5))
    with pytest.raises(ValueError):
        assert rsp.value


def test_event_filter_subclasses():
    """
    Runs tests on all InstanceEventFilter subclasses to make sure they are
    implemented properly, i.e. all members are powers of two, and all powers
    of two are named up to the largest value
    """
    for subcls in InstanceEventFilter.__subclasses__():
        # This would raise a TypeError if it is more than 24 bits
        subcls.dali_width()

        expected_values = {pow(2, n) for n in range(len(subcls))}
        for member in subcls.__members__.values():
            # Each member must only have a power of two value
            if member.value not in expected_values:
                raise KeyError(
                    f"{subcls.__name__} from {subcls.__module__} enum value "
                    f"'{member.value}' is not valid (must be sequential powers "
                    "of two)"
                )
            expected_values.remove(member.value)
        if len(expected_values) != 0:
            raise ValueError(
                f"{subcls.__name__} from {subcls.__module__} does not have "
                f"values for the following flags: {expected_values}"
            )


def test_event_filter_pushbutton_width():
    """
    Confirms that the custom 'bit_width' property of the EventFilter_pb
    enumerator works as expected, on both the class and on instances
    """
    assert EventFilter_pb.dali_width() == 8
    filter_instance = EventFilter_pb(3)
    assert filter_instance.dali_width() == 8


def test_frame_to_event_dev_inst_occupancy_occupied():
    device_instance_map = DeviceInstanceTypeMapper()
    device_instance_map.add_type(
        short_address=1,
        instance_number=1,
        instance_type=3,
    )

    dev_inst_frame = Frame(24, data=0b000000101000010000001011)
    decode_cmd = Command.from_frame(
        dev_inst_frame, dev_inst_map=device_instance_map
    )

    assert isinstance(decode_cmd, OccupancyEvent)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1
    assert decode_cmd.movement
    assert decode_cmd.occupied
    assert not decode_cmd.repeat
    assert decode_cmd.sensor_type == "movement"


def test_invalid_occupancy():
    """
    Confirms that invalid occupancy messages do not decode
    """
    base_frame = 0b000000000000110000000000
    for tst_int in range(1, 64):
        tst = base_frame | (tst_int << 4)
        fr = ForwardFrame(24, tst.to_bytes(3, "big"))
        ev = Command.from_frame(fr)
        assert isinstance(ev, UnknownEvent)


def test_frame_to_event_dev_inst_light():
    device_instance_map = DeviceInstanceTypeMapper()
    device_instance_map.add_type(
        short_address=5,
        instance_number=2,
        instance_type=4,
    )

    dev_inst_frame = Frame(24, data=0b000010101000100000001011)
    decode_cmd = Command.from_frame(
        dev_inst_frame, dev_inst_map=device_instance_map
    )

    assert isinstance(decode_cmd, LightEvent)
    assert decode_cmd.short_address.address == 5
    assert decode_cmd.instance_number == 2
    assert decode_cmd.illuminance == 11
