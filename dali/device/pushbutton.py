"""
Commands, responses and events from IEC 62386 part 301: "Input devices — Push buttons"
"""
from __future__ import annotations

from typing import Dict, Type

from dali import command
from dali.device.general import (
    DeviceEnum,
    QueryEventFilterZeroToSeven,
    _Event,
    _StandardInstanceCommand,
)

# "1" corresponds with "Part 301", as per Table 4 of IEC 62386 part 103
instance_type = 1


class _PushbuttonEvent(_Event):
    """
    Encodes and decodes messages defined in IEC 62386 part 301. For Push Buttons, the
    event information uniquely defines an event, i.e. there is no additional data
    encoded in the event information apart from the event name itself.
    """

    # "1" corresponds with "Part 301", as per Table 4 of IEC 62386 part 103
    _instance_type = instance_type
    _event_classes: Dict[int, Type["_PushbuttonEvent"]] = {}

    @classmethod
    def _register_subclass(cls, subclass):
        if not issubclass(subclass, _PushbuttonEvent):
            raise RuntimeError(
                "Somehow called _PushbuttonEvent._register_subclass() "
                "without a subclass of _PushbuttonEvent"
            )
        cls._event_classes[subclass._event_info] = subclass

    @classmethod
    def from_event_data(cls, event_data: int):
        return cls._event_classes.get(event_data)


###############################################################################
# Commands from Part 301 Table 2 start here
###############################################################################


class ButtonReleased(_PushbuttonEvent):
    """
    The button is released
    """

    _event_info = 0b0000000000


class ButtonPressed(_PushbuttonEvent):
    """
    The button is pressed
    """

    _event_info = 0b0000000001


class ShortPress(_PushbuttonEvent):
    """
    The button is pressed and released, without being pressed quickly again (in case
    double press is enabled), or the button is pressed and quickly released (in case
    double press is disabled).

    The Short Timer differentiates a short press from a long press. If a button is
    released within T_short, either a short or a double press event will follow;
    otherwise the press will generate a long press event.

    See also: SetShortTimer
    """

    _event_info = 0b0000000010


class DoublePress(_PushbuttonEvent):
    """
    The button is pressed and released, quickly followed by another button press.

    The Double Timer (T_double) differentiates a single short press from a double
    press. If a button is pressed, released, then pressed again within T_double then
    a double press event is generated. T_double is disabled by setting a value of 0,
    when disabled a short press event is generated immediately upon button release.

    See also: SetDoubleTimer
    """

    _event_info = 0b0000000101


class LongPressStart(_PushbuttonEvent):
    """
    The button is pressed without releasing it.

    The Short Timer (T_short) differentiates a short press from a long press. If a
    button is released within T_short, either a short or a double press event will
    follow; otherwise the press will generate a long press event.

    See also: SetShortTimer
    """

    _event_info = 0b0000001001


class LongPressRepeat(_PushbuttonEvent):
    """
    Following a long press start condition, the button is still pressed. The event
    occurs at regular intervals as long as the condition holds.

    The Repeat Timer (T_repeat) sets the repetition interval of long press repeat
    events.

    See also: SetRepeatTimer
    """

    _event_info = 0b0000001011


class LongPressStop(_PushbuttonEvent):
    """
    Following a long press start condition, the button is released. If the long
    press stop event is enabled, there is no separate button released event.
    """

    _event_info = 0b0000001100


class ButtonFree(_PushbuttonEvent):
    """
    The button has been stuck and is now released
    """

    _event_info = 0b0000001110


class ButtonStuck(_PushbuttonEvent):
    """
    The button has been pressed for a very long time and is assumed stuck.

    If a button is pressed or bouncing longer than the Stuck Timer (T_stuck) it is
    considered broken.

    See also: SetStuckTimer
    """

    _event_info = 0b0000001111


###############################################################################
# Commands from Part 301 Table 10 start here
###############################################################################


class _PushbuttonCommand(_StandardInstanceCommand):
    """
    An extension of the standard commands, addressed to a push button control
    device instance
    """

    _opcode = None


class SetShortTimer(_PushbuttonCommand):
    """
    The Short Timer (T_short) differentiates a short press from a long press. If a
    button is released within T_short, either a short or a double press event will
    follow; otherwise the press will generate a long press event.

    T_short increments in intervals of 20 ms, i.e. the raw value needs to be
    multiplied by 20 ms to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x00


class SetDoubleTimer(_PushbuttonCommand):
    """
    The Double Timer (T_double) differentiates a single short press from a double
    press. If a button is pressed, released, then pressed again within T_double then
    a double press event is generated. T_double is disabled by setting a value of 0,
    when disabled a short press event is generated immediately upon button release.

    T_double increments in intervals of 20 ms, i.e. the raw value needs to be
    multiplied by 20 ms to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x01


class SetRepeatTimer(_PushbuttonCommand):
    """
    The Repeat Timer (T_repeat) sets the repetition interval of long press repeat
    events.

    T_repeat increments in intervals of 20 ms, i.e. the raw value needs to be
    multiplied by 20 ms to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x02


class SetStuckTimer(_PushbuttonCommand):
    """
    If a button is pressed or bouncing longer than the Stuck Timer (T_stuck) it is
    considered broken.

    T_stuck increments in intervals of 1 second, i.e. the raw value is the actual
    value, in seconds.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x03


class QueryShortTimer(_PushbuttonCommand):
    """
    Gets the current value for T_short.

    See also: SetShortTimer
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0A


class QueryShortTimerMin(_PushbuttonCommand):
    """
    Gets the minimum value for T_short supported by the hardware
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0B


class QueryDoubleTimer(_PushbuttonCommand):
    """
    Gets the current value for T_double.

    See also: SetDoubleTimer
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0C


class QueryDoubleTimerMin(_PushbuttonCommand):
    """
    Gets the minimum value for T_double supported by the hardware.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0D


class QueryRepeatTimer(_PushbuttonCommand):
    """
    Gets the current value for T_repeat.

    See also: SetRepeatTimer
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0E


class QueryStuckTimer(_PushbuttonCommand):
    """
    Gets the current value for T_stuck.

    See also: SetStuckTimer
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x0F


###############################################################################
# Event Filters from Part 301 Table 3 start here
###############################################################################


class EventFilterPushbutton(DeviceEnum):
    """
    Event Filters for a push button instance, as defined in Part 301 Table 3. The
    order of the values below correspond to the bit position in the bitmask, from
    0 to 7 (push button instances only have one byte of event filters defined).
    """

    button_released = "Button released event enabled"
    button_pressed = "Button pressed event enabled"
    short_press = "Short press event enabled"
    double_press = "Double press event enabled"
    long_press_start = "Long press start event enabled"
    long_press_repeat = "Long press repeat event enabled"
    long_press_stop = "Long press stop event enabled"
    button_stuck_free = "Button stuck/free event enabled"


class QueryEventFilterPushbuttonResponse(command.BitmapResponse):
    """
    A response object corresponding to a QueryEventFilterPushbutton message. Internally
    uses the EventFilterPushbutton enum, i.e. the `status` attribute will be a
    list of values from this enum.
    """

    bits = list(EventFilterPushbutton)


class QueryEventFilterPushbutton(QueryEventFilterZeroToSeven):
    """
    A specific override of the QueryEventFilterZeroToSeven command, tailored to the
    response expected from a push button instance. There is nothing in a DALI
    response itself that indicates which instance type was being queried, the type must
    be known beforehand.
    """

    no_register = True
    response = QueryEventFilterPushbuttonResponse
