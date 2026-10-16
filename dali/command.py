"""Declaration of base types for dali commands and their responses."""

from __future__ import annotations

from typing import Optional, Protocol, Literal, Generic, Any, Sequence, TypeVar
from abc import ABC, abstractmethod
from enum import IntEnum
from dali import address
from dali import frame
from dali.exceptions import MissingResponse
from dali.exceptions import ResponseError


# Device Instance Type Mapper
class DITM(Protocol):
    def get_type(
            self,
            *,
            short_address: address.DeviceShort,
            instance_number: address.InstanceNumber | int,
    ) -> Optional[int]:
        ...


T = TypeVar("T")


# XXX it may simplify things in the future if we add a "NoResponse"
# subclass (Response[None]) to indicate no response is expected,
# rather than have response = None in the Command class.


class Response(Generic[T], ABC):
    """Some DALI commands cause a response from the addressed devices.

    The response is either an 8-bit backward frame encoding 8-bit data
    or 0xff for "Yes", or a lack of response encoding "No".  If
    multiple devices respond at once the backward frame may be
    received with a framing error; this shall be interpreted as "more
    than one device answered "Yes".

    Initialise this class by passing a BackwardFrame object, or None
    if there was no response.

    This is a generic abstract base class; subclasses override the
    `value` property and return a suitable type. Accessing this
    property raises `MissingResponse` or `ResponseError` if the
    response frame is not valid. Before accessing the `value`
    property, you can check the `valid` property (or `missing` and
    `error` separately) to avoid receiving an exception.
    """
    _expected = False
    _error_acceptable = False

    def __init__(self, val: Optional[frame.BackwardFrame]) -> None:
        if val is not None and not isinstance(val, frame.BackwardFrame):
            raise TypeError("Response must be passed None or a BackwardFrame")
        self._value = val

    @property
    def raw_value(self) -> Optional[frame.BackwardFrame]:
        return self._value

    @property
    def missing(self) -> bool:
        return self._value is None and self._expected

    # NB don't extend this in subclasses if only a subset of responses
    # are acceptable; extend the "valid" property instead
    @property
    def error(self) -> bool:
        if self._value:
            return self._value.error and not self._error_acceptable
        return False

    def raise_for_status(self) -> None:
        if self.missing:
            raise MissingResponse()
        if self.error:
            raise ResponseError()

    # If only a subset of response frames are acceptable, extend this
    # property to check for them.
    @property
    def valid(self) -> bool:
        return not (self.missing or self.error)

    @property
    @abstractmethod
    def value(self) -> T:
        ...

    def __str__(self) -> str:
        if self.valid:
            return f"{self.value}"
        return "MissingResponse" if self.missing else "ResponseError"


class NumericResponse(Response[int]):
    _expected = True

    @property
    def value(self) -> int:
        self.raise_for_status()
        assert self._value
        return self._value.as_integer


class NumericResponseMask(Response[int | Literal["MASK"]]):
    _expected = True

    @property
    def value(self) -> int | Literal["MASK"]:
        self.raise_for_status()
        assert self._value
        if self._value.as_integer == 0xff:
            return "MASK"
        return self._value.as_integer


class OptionalNumericResponse(Response[Optional[int]]):
    @property
    def value(self) -> Optional[int]:
        self.raise_for_status()
        if not self._value:
            return None
        return self._value.as_integer


class OptionalNumericResponseMask(Response[Optional[int | Literal["MASK"]]]):
    @property
    def value(self) -> Optional[int | Literal["MASK"]]:
        self.raise_for_status()
        if self._value is None:
            return None
        if self._value.as_integer == 0xff:
            return "MASK"
        return self._value.as_integer


class YesNoResponse(Response[bool]):
    _error_acceptable = True

    @property
    def value(self) -> bool:
        return self._value is not None


class BitmapResponse(Response[dict[str, bool]]):
    """A response that consists of several named bits.

    Bits are listed in subclasses with the least-sigificant bit first.
    """
    _expected = True
    _bit_properties: dict[str, int]
    bits: Sequence[Optional[str]] = ()

    def __init_subclass__(cls) -> None:
        bd = {}
        bit = 0
        for b in cls.bits:
            if b:
                mangled = b.replace(' ', '_').replace('-', '')
                bd[mangled] = bit
            bit = bit + 1
        cls._bit_properties = bd

    # XXX this is new and needs a test adding
    @property
    def value(self) -> dict[str, bool]:
        self.raise_for_status()
        assert self._value is not None
        return {name: bool(self._value[self._bit_properties[name]])
                for name in self._bit_properties.keys()}

    @property
    def status(self) -> list[str]:
        self.raise_for_status()
        assert self._value is not None
        v = self._value[7:0]
        l = []
        for b in self.bits:
            if v & 0x01 and b:
                l.append(b)
            v = (v >> 1)
        return l

    def __getattr__(self, name: str) -> Optional[bool]:
        if name in self._bit_properties:
            self.raise_for_status()
            assert self._value is not None
            return bool(self._value[self._bit_properties[name]])
        raise AttributeError

    def __str__(self) -> str:
        try:
            return ",".join(self.status)
        except (MissingResponse, ResponseError) as e:
            return "{}".format(e)


class EnumResponse(Response[IntEnum]):
    """A response that consists of a number from a pre-defined enumerator

    If the value of the response is not present in the enumerator, then
    TypeError will be raised.
    """
    _expected = True
    enumerator: type[IntEnum]

    @property
    def valid(self) -> bool:
        if not super().valid:
            return False
        assert self._value is not None
        # In Python >=3.12 we can write this as:
        # return self._value.as_integer in self.enumerator
        return self._value.as_integer in self.enumerator.__members__.values()

    @property
    def value(self) -> IntEnum:
        self.raise_for_status()
        assert self._value is not None
        return self.enumerator(self._value.as_integer)


class EnumResponseMask(Response[IntEnum | Literal["MASK"]]):
    _expected = True
    enumerator: type[IntEnum]

    @property
    def valid(self) -> bool:
        if not super().valid:
            return False
        assert self._value is not None
        # In Python >=3.12 we can write this as:
        # return self._value.as_integer in self.enumerator
        return self._value.as_integer in self.enumerator.__members__.values()

    @property
    def value(self) -> IntEnum | Literal["MASK"]:
        self.raise_for_status()
        assert self._value is not None
        if self._value.as_integer == 0xff:
            return "MASK"
        return self.enumerator(self._value.as_integer)


# XXX we may want to make Command a generic, too, on the type of its
# Response.  That way, the DALISequence type annotation can match up
# commands with response types.

class Command:
    """A command frame.

    Subclasses must provide a class method "from_frame" which, when
    passed a Frame returns a new instance of the class corresponding
    to that command, or "None" if there is no match.
    """

    # Override this as appropriate
    _framesize = 0

    # The following flags correspond to the columns in tables 15 and
    # 16 of IEC 62386-102 and tables 21 and 22 of IEC 62386-103.
    # Override them in subclasses if there is a tick in the
    # appropriate column.
    #
    # "response" is None if no response is expected, or a Response
    # class to process the response.
    appctrl = False
    inputdev = False
    uses_dtr0 = False
    uses_dtr1 = False
    uses_dtr2 = False
    response: Optional[type[Response[Any]]] = None
    sendtwice = False

    # 16-bit frames may be interpreted differently if they are
    # preceded by the EnableDeviceType command.  If a command needs
    # EnableDeviceType(foo) to be sent first, override devicetype to
    # foo.  This parameter is ignored for all other frame lengths.
    devicetype = 0

    _commands: set[type[Command]] = set()
    _supported_devicetypes: set[int] = set()
    _framesizes: dict[int, list[type[Command]]] = {}

    def __init_subclass__(cls) -> None:
        if cls.__name__[0] != '_':
            cls._commands.add(cls)
        if cls.devicetype != 0:
            cls._supported_devicetypes.add(cls.devicetype)
        subs = cls._framesizes.setdefault(cls._framesize, list())
        subs.append(cls)

    def __init__(self, f: frame.ForwardFrame) -> None:
        if not isinstance(f, frame.ForwardFrame):
            raise TypeError(
                f"{self.__class__.__name__} expected a ForwardFrame, "
                f"not a {type(f)}"
            )
        self._data = f

    @classmethod
    def from_frame(
            cls, f: frame.ForwardFrame, devicetype: int = 0,
            dev_inst_map: Optional[DITM] = None
    ) -> Optional[Command]:
        """Return a Command instance corresponding to the supplied frame.

        If the device type the command is intended for is known
        (i.e. the previous command was EnableDeviceType(foo)) then
        specify it here.

        :parameter frame: a forward frame
        :parameter devicetype: type of device frame is intended for
        :param dev_inst_map: An instance of DeviceInstanceTypeMapper to
        assist with DALI events

        :returns: Return a Command instance corresponding to the
        frame.  Returns None if there is no match.
        """
        if cls != Command:
            raise Exception(f"from_frame not overridden in class {cls}")

        # At the top level, we simply distinguish by frame size
        subs = cls._framesizes.get(len(f), [])

        for c in subs:
            r = c.from_frame(f, devicetype=devicetype,
                             dev_inst_map=dev_inst_map)
            if r:
                return r

        # The frame doesn't match any of the commands we know.
        return cls(f)

    @property
    def frame(self) -> frame.ForwardFrame:
        """The forward frame to be transmitted for this command."""
        return self._data

    @property
    def is_query(self) -> bool:
        """Does this command return a result?"""
        return self.response is not None

    def __str__(self) -> str:
        joined = ":".join(
            "{:02x}".format(c) for c in self._data.as_byte_sequence)
        return "({0}){1}".format(type(self), joined)


from_frame = Command.from_frame
