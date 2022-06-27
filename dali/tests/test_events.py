from dataclasses import dataclass
from typing import Optional, Type

import pytest

import dali.frame
from dali import address
from dali.command import Command
from dali.device import general, pushbutton
from dali.device.general import (
    DTR0,
    SetEventFilter,
    _Event,
    device_instance_map,
)
from dali.device.sequences import SetPushbuttonEventFilters
from dali.device.pushbutton import (
    EventFilterPushbutton,
    QueryEventFilterPushbutton,
    QueryEventFilterPushbuttonResponse,
)


def test_event_base_not_implemented():
    with pytest.raises(NotImplementedError):
        general._Event()


@pytest.fixture
def event_test_data_good():
    @dataclass
    class EventTestData:
        event_type: Type[_Event] = pushbutton.ButtonReleased
        short_address: Optional[int] = None
        instance_number: Optional[int] = None
        instance_group: Optional[int] = None
        device_group: Optional[int] = None
        frame: str = "000000000000000000000000"

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
    )
    return test_data


def test_event_to_frame_pushbutton_good(event_test_data_good):
    """
    Tests a number of values against known-good expected frames, for various
    pushbutton events
    """
    for test_case in event_test_data_good:
        event = test_case.event_type(
            short_address=test_case.short_address,
            instance_number=test_case.instance_number,
            instance_group=test_case.instance_group,
            device_group=test_case.device_group,
        )
        event_frame = f"{event.frame.as_integer:024b}"
        assert event_frame == test_case.frame


def test_frame_to_event_pushbutton_good(event_test_data_good):
    """
    Tests a number of known-good frames, to ensure the correct object is decoded
    """
    for test_case in event_test_data_good:
        test_frame = dali.frame.Frame(24, data=int(test_case.frame, base=2))
        event = Command.from_frame(test_frame)
        assert isinstance(event, test_case.event_type)
        if test_case.short_address:
            assert event.short_address.address == test_case.short_address
        assert event.instance_number == test_case.instance_number
        assert event.instance_group == test_case.instance_group
        assert event.device_group == test_case.device_group


def test_event_repr_short_address():
    event = pushbutton.ButtonReleased(short_address=1)
    event_str = f"{event}"
    assert "ButtonReleased(short_address=1)" == event_str


def test_event_repr_instance_number():
    event = pushbutton.ButtonReleased(instance_number=2)
    event_str = f"{event}"
    assert "ButtonReleased(instance_number=2)" == event_str


def test_event_repr_instance_group():
    event = pushbutton.ButtonReleased(instance_group=3)
    event_str = f"{event}"
    assert "ButtonReleased(instance_group=3)" == event_str


def test_event_repr_device_group():
    event = pushbutton.ButtonReleased(device_group=31)
    event_str = f"{event}"
    assert "ButtonReleased(device_group=31)" == event_str


def test_frame_to_ambiguous_event():
    dev_inst_frame = dali.frame.Frame(24, data=0b000000101000010000000010)
    decode_cmd = dali.command.Command.from_frame(dev_inst_frame)
    assert isinstance(decode_cmd, general.AmbiguousInstanceType)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1
    assert decode_cmd.event_data == 0b0000000010


def test_frame_to_event_dev_inst_pushbutton():
    device_instance_map.add_type(
        short_address=1,
        instance_number=1,
        instance_type=pushbutton,
    )

    dev_inst_frame = dali.frame.Frame(24, data=0b000000101000010000000010)
    decode_cmd = dali.command.Command.from_frame(dev_inst_frame)

    assert isinstance(decode_cmd, pushbutton.ShortPress)
    assert decode_cmd.short_address.address == 1
    assert decode_cmd.instance_number == 1

    device_instance_map.clear()


def test_event_enum_pushbutton():
    """
    Confirms that the custom 'position' attribute of the EventFilterPushbutton
    enumerator works as expected
    """
    assert EventFilterPushbutton.button_released.position == 0
    assert EventFilterPushbutton.button_pressed.position == 1
    assert EventFilterPushbutton.short_press.position == 2
    assert EventFilterPushbutton.double_press.position == 3
    assert EventFilterPushbutton.long_press_start.position == 4
    assert EventFilterPushbutton.long_press_repeat.position == 5
    assert EventFilterPushbutton.long_press_stop.position == 6
    assert EventFilterPushbutton.button_stuck_free.position == 7


def test_event_filter_pushbutton_sequence_partial():
    """
    Confirms that the SetEventFilterPushbutton sequence yields the expected DALI
    message objects and sets the correct bit flags for DTR0
    """
    sequence = SetPushbuttonEventFilters(
        device=address.Short(0),
        instance=address.InstanceNumber(0),
        filters={
            EventFilterPushbutton.button_released,
            EventFilterPushbutton.button_stuck_free,
            EventFilterPushbutton.double_press,
        },
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
    assert cmd.destination == address.Short(0)
    assert cmd.instance == address.InstanceNumber(0)

    # The third message should be QueryEventFilterPushbutton
    try:
        cmd = sequence.send(rsp)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, QueryEventFilterPushbutton)

    # The sequence should then just return whatever the response is
    rsp = QueryEventFilterPushbuttonResponse(dali.frame.BackwardFrame(0b10001001))
    ret = None
    try:
        sequence.send(rsp)
    except StopIteration as r:
        ret = r.value
    assert isinstance(ret, QueryEventFilterPushbuttonResponse)
    assert ret == rsp
    assert EventFilterPushbutton.button_released in ret.status
    assert EventFilterPushbutton.button_stuck_free in ret.status
    assert EventFilterPushbutton.double_press in ret.status
    assert EventFilterPushbutton.short_press not in ret.status


def test_event_filter_pushbutton_sequence_all():
    sequence = SetPushbuttonEventFilters(
        device=address.Short(0),
        instance=address.InstanceNumber(0),
        filters=(
            EventFilterPushbutton.double_press,
            EventFilterPushbutton.long_press_start,
            EventFilterPushbutton.button_pressed,
            EventFilterPushbutton.short_press,
            EventFilterPushbutton.long_press_repeat,
            EventFilterPushbutton.button_released,
            EventFilterPushbutton.long_press_stop,
            EventFilterPushbutton.button_stuck_free,
            EventFilterPushbutton.double_press,  # Intentional duplicate
        ),
    )
    # The first message the sequence should send is DTR0
    try:
        cmd = sequence.send(None)
    except StopIteration:
        raise RuntimeError()
    assert isinstance(cmd, DTR0)
    assert cmd.frame.as_byte_sequence[2] == 0b11111111
    # The previous test for the sequence adequately checks the remaining logic


def test_event_filter_pushbutton_sequence_bad_type():
    sequence = SetPushbuttonEventFilters(
        device=address.Short(0),
        instance=address.InstanceNumber(0),
        filters=("double_press",),
    )
    # Using a string is not valid, it must be an enum object
    with pytest.raises(ValueError):
        sequence.send(None)
