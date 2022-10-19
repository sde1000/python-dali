"""
Commands, responses and events from IEC 62386 part 304: "Input devices —
Light sensor"
"""
from __future__ import annotations

from dali import command, frame
from dali.device import general

# "4" corresponds with "Part 304", as per Table 4 of IEC 62386 part 103
instance_type = 4


class LightEvent(general._Event):
    """
    Encodes and decodes messages defined in IEC 62386 part 304

    Light Events contain just a simple integer of the relative illuminance, with
    10 bit resolution. Note that the illuminance value is a relative value, and
    does not represent absolute lux values.
    """

    # "4" corresponds with "Part 304", as per Table 4 of IEC 62386 part 103
    _instance_type = instance_type

    # Event info is set based the illuminance value
    _event_info = 0

    @classmethod
    def _register_subclass(cls, subclass):
        raise RuntimeError(
            "Called LightEvent._register_subclass()! There should be no "
            "subclasses of LightEvent."
        )

    @classmethod
    def from_event_data(cls, event_data: int):
        # There is only one class for LightEvent, which contains the illuminance
        return LightEvent

    @property
    def event_data(self):
        return self._event_info

    def _set_event_data(self, set_data: int, set_frame: frame.Frame):
        if not isinstance(set_data, int):
            raise ValueError("LightEvent requires 'data' to be set as an 'int'")

        # Store the data as the "event info"
        self._event_info = set_data

        # Encode the data bits into the frame
        set_frame[9:0] = set_data

    @property
    def illuminance(self) -> int:
        return self._event_info


###############################################################################
# Event Filters from Part 304 Table 2 start here
###############################################################################


class InstanceEventFilter(general.InstanceEventFilter):
    """
    Event Filters for a light instance, as defined in Part 304 Table 2
    """

    illuminance_level = 0b00000001


###############################################################################
# Commands from Part 303 Table 10 start here
###############################################################################


class _LightCommand(general._StandardInstanceCommand):
    """
    An extension of the standard commands, addressed to a light sensor control
    device instance
    """

    _opcode = None


class SetReportTimer(_LightCommand):
    """
    The Report Timer (T_repeat) sets the interval between "repeat" messages.
    These are sent regardless of the state of the input, even if it has not
    changed.

    Report Timer increments in intervals of 1 second, i.e. the raw value is the
    actual value, in seconds.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x30


class SetHysteresis(_LightCommand):
    """
    The Hysteresis band is calculated based on a hysteresis percent value and a
    minimum absolute value. After a change has been reported, the next change
    will not be reported unless the illuminance value has changed by at least
    the hysteresis percent or the minimum value.

    This command sets the hysteresis percent.

    See also: SetHysteresisMin.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x31


class SetDeadtimeTimer(_LightCommand):
    """
    If the Deadtime Timer is set, the instance shall not send out an event until
    the Deadtime Timer has expired. The Deadtime Timer is restarted every time
    an event is sent.

    NOTE: The purpose of the Deadtime Timer is to increase the effective bus
    bandwidth availability.

    Deadtime Timer increments in intervals of 50 ms, i.e. the raw value needs
    to be multiplied by 50 ms to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x32


class SetHysteresisMin(_LightCommand):
    """
    The Hysteresis band is calculated based on a hysteresis percent value and a
    minimum absolute value. After a change has been reported, the next change
    will not be reported unless the illuminance value has changed by at least
    the hysteresis percent or the minimum value.

    This command sets the minimum hysteresis value.

    See also: SetHysteresis.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x33


class QueryHysteresisMin(_LightCommand):
    """
    Gets the current value for HysteresisMin

    See also: SetHysteresisMin
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3C


class QueryDeadtimeTimer(_LightCommand):
    """
    Gets the current value for Deadtime Timer

    See also: SetDeadtimeTimer

    Deadtime Timer increments in intervals of 50 ms, i.e. the raw value needs
    to be multiplied by 50 ms to get the actual value.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3D


class QueryReportTimer(_LightCommand):
    """
    Gets the current value for Report Timer

    See also: SetReportTimer

    Report Timer increments in intervals of 1 second, i.e. the raw value is the
    actual value, in seconds.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3E


class QueryHysteresis(_LightCommand):
    """
    Gets the current value for Hysteresis

    See also: SetHysteresis
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x3F
