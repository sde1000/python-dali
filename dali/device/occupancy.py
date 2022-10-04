"""
Commands, responses and events from IEC 62386 part 303: "Input devices —
Occupancy sensor"
"""
from __future__ import annotations

from typing import NamedTuple
# TODO: If support for Python 3.7 is dropped then a Literal type can be used
# from typing import Literal

from dali import command, frame
from dali.device import general

# "3" corresponds with "Part 303", as per Table 4 of IEC 62386 part 103
instance_type = 3


class OccupancyEvent(general._Event):
    """
    Encodes and decodes messages defined in IEC 62386 part 303

    Occupancy Events contain several flags, which must be set during
    initialisation using the `data` attribute and the `EventData` named tuple.

    For example:
    ```
    event = OccupancyEvent(
        short_address=1,
        instance_number=2,
        data=OccupancyEvent.EventData(movement=False, occupied=True),
    )
    ```
    """

    class EventData(NamedTuple):
        """
        IEC 62386 part 303 defines several event encodings which may be sent in
        a single event notification - for example, both "Occupied", "Movement",
        and "Movement sensor" may be encoded in a single notification. Rather
        than having one Python class per possible combination, instead a named
        tuple is used to flag which properties are set for a certain
        notification.

        * movement: True for "Movement", otherwise False for "No Movement"
        * occupied: True for "Occupied", otherwise False for "Vacant"
        * repeat: True if this is a repeated event (interval set by report timer)
        * sensor_type: Either the literal strings "presence" or "movement"
        """

        movement: bool
        occupied: bool
        repeat: bool = False
        # TODO: If Literal is supported then this type hint can be improved
        # sensor_type: Literal["presence", "movement"] = "movement"
        sensor_type: str = "movement"

    # "3" corresponds with "Part 303", as per Table 4 of IEC 62386 part 103
    _instance_type = instance_type

    # Occupancy events contain some extra information, wrapped in a dataclass
    _extra_data: EventData = None

    # Event info is set based on the named tuple passed in as data
    _event_info = 0

    @classmethod
    def _register_subclass(cls, subclass):
        raise RuntimeError(
            "Called OccupancyEvent._register_subclass()! There should be no "
            "subclasses of OccupancyEvent."
        )

    @classmethod
    def from_event_data(cls, event_data: int):
        # Check that the data is valid for an occupancy sensor - only the lowest
        # 4 bits are used, make sure the high 6 bits are zero
        if event_data | 0b1111 != 0b1111:
            return None

        return OccupancyEvent

    @property
    def event_data(self):
        return self._extra_data

    def _set_event_data(
        self, set_data: int | EventData, set_frame: frame.Frame
    ):
        if set_data is None:
            raise ValueError("OccupancyEvent requires 'data' to be set")

        # If data is passed in as an int then it needs to be decoded into
        # various flags and stored as an EventData named tuple
        if isinstance(set_data, int):
            # Bit 0: "movement detected" = 1, "movement not detected" = 0
            movement = set_data & 0b0001 == 0b0001

            # Bit 1: "occupied" = 1, "vacant" = 0
            occupied = set_data & 0b0010 == 0b0010

            # Bit 2: "repeat event" = 1, not repeat = 0
            repeat = set_data & 0b0100 == 0b0100

            # Bit 3: "movement sensor" = 1, "presence sensor" = 0
            sensor = "movement" if set_data & 0b1000 == 0b1000 else "presence"

            self._extra_data = OccupancyEvent.EventData(
                movement=movement,
                occupied=occupied,
                repeat=repeat,
                sensor_type=sensor,  # noqa
            )

        # If data is already an OccupancyEvent.EventData then just store that
        elif isinstance(set_data, OccupancyEvent.EventData):
            self._extra_data = set_data

        else:
            raise TypeError(
                "'data' for OccupancyEvent must be either 'int' or "
                f"'OccupancyEvent.EventData', not: {type(set_data)}"
            )

        # Encode the extra data bits into the frame
        # Bit 0: "movement detected" = 1, "movement not detected" = 0
        set_frame[0] = self._extra_data.movement

        # Bit 1: "occupied" = 1, "vacant" = 0
        set_frame[1] = self._extra_data.occupied

        # Bit 2: "repeat event" = 1, not repeat = 0
        set_frame[2] = self._extra_data.repeat

        # Bit 3: "movement sensor" = 1, "presence sensor" = 0
        set_frame[3] = 1 if self._extra_data.sensor_type == "movement" else 0

    @property
    def movement(self) -> bool:
        return self._extra_data.movement

    @property
    def occupied(self) -> bool:
        return self._extra_data.occupied

    @property
    def repeat(self) -> bool:
        return self._extra_data.repeat

    @property
    # TODO: If Literal is supported then this type hint can be improved
    # def sensor_type(self) -> Literal["presence", "movement"]:
    def sensor_type(self) -> str:
        return self._extra_data.sensor_type


###############################################################################
# Event Filters from Part 303 Table 3 start here
###############################################################################


class InstanceEventFilter(general.InstanceEventFilter):
    """
    Event Filters for an occupancy instance, as defined in Part 303 Table 3
    """

    occupied = 0b00000001
    vacant = 0b00000010
    repeat = 0b00000100
    movement = 0b00001000
    no_movement = 0b00010000


###############################################################################
# Commands from Part 303 Table 10 start here
###############################################################################


class _OccupancyCommand(general._StandardInstanceCommand):
    """
    An extension of the standard commands, addressed to an occupancy control
    device instance
    """

    _opcode = None


class CatchMovement(_OccupancyCommand):
    """
    Enabling the event filter for "movement" can result in bursts of
    transmissions that could flood the bus. To mitigate this, the Catch Movement
    command can be used - which tells the device to temporarily enable movement
    events for only the first detected movement - then the movement event is
    disabled again.

    If the movement event is already enabled then the Catch Movement command is
    ignored.

    The event filter is not modified by this command.
    """

    inputdev = True
    _opcode = 0x20


class SetHoldTimer(_OccupancyCommand):
    """
    The hold timer is only implemented for movement based sensors. The hold
    timer is used to determine if an area should still be considered "occupied"
    some time after movement was last detected, i.e. detection of movement will
    set the area as "occupied" and start the hold timer running; each subsequent
    detection of movement will restart the timer and the "occupied" state will
    remain; when the hold timer expires the area will be considered "vacant".

    Hold Timer increments in intervals of 10 seconds, i.e. the raw value needs
    to be multiplied by 10 seconds to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x21


class SetReportTimer(_OccupancyCommand):
    """
    The Report Timer (T_repeat) sets the interval between "repeat" messages.
    These are sent regardless of the state of the input has not changed.

    Report Timer increments in intervals of 1 second, i.e. the raw value is the
    actual value, in seconds.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x22


class SetDeadtimeTimer(_OccupancyCommand):
    """
    If the Deadtime Timer is set, the instance shall not send out an event until
    the Deadtime Timer has expired. The Deadtime Timer is restarted every time
    an event is sent.

    NOTE: The purpose of the Deadtime Timer is to increase the effective bus
    bandwidth availability. It is not intended to be used as a hold timer.

    Deadtime Timer increments in intervals of 50 ms, i.e. the raw value needs
    to be multiplied by 50 ms to get the actual value.
    """

    inputdev = True
    uses_dtr0 = True
    sendtwice = True
    _opcode = 0x23


class CancelHoldTimer(_OccupancyCommand):
    """
    If the hold timer is implemented and the timer is running, this command
    clears the timer and generates a "vacant" trigger.
    """

    inputdev = True
    _opcode = 0x24


class QueryDeadtimeTimer(_OccupancyCommand):
    """
    Gets the current value for Deadtime Timer

    See also: SetDeadtimeTimer

    Deadtime Timer increments in intervals of 50 ms, i.e. the raw value needs
    to be multiplied by 50 ms to get the actual value.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x2C


class QueryHoldTimer(_OccupancyCommand):
    """
    Gets the current value for Hold Timer

    See also: SetHoldTimer

    Hold Timer increments in intervals of 10 seconds, i.e. the raw value needs
    to be multiplied by 10 seconds to get the actual value.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x2D


class QueryReportTimer(_OccupancyCommand):
    """
    Gets the current value for Report Timer

    See also: SetReportTimer

    Report Timer increments in intervals of 1 second, i.e. the raw value is the
    actual value, in seconds.
    """

    inputdev = True
    response = command.NumericResponse
    _opcode = 0x2E


class QueryCatching(_OccupancyCommand):
    """
    Queries if "movement catching" is running

    See also: CatchMovement
    """

    inputdev = True
    response = command.YesNoResponse
    _opcode = 0x2F
