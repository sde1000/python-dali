"""Declaration of base types for dali commands and their responses."""

from __future__ import annotations

from typing import Optional, Protocol, Literal
from enum import IntEnum
from dali import frame, address
from dali.exceptions import MissingResponse
from dali.exceptions import ResponseError


# Device Instance Type Mapper
class DITM(Protocol):
    def get_type(
            self,
            *,
            short_address: address.DeviceShort | int,
            instance_number: address.InstanceNumber | int,
    ) -> Optional[int]:
        ...


class Response:
    """Some DALI commands cause a response from the addressed devices.

    The response is either an 8-bit backward frame encoding 8-bit data
    or 0xff for "Yes", or a lack of response encoding "No".  If
    multiple devices respond at once the backward frame may be
    received with a framing error; this shall be interpreted as "more
    than one device answered "Yes".

    Initialise this class by passing a BackwardFrame object, or None
    if there was no response.
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

    @property
    def valid(self) -> bool:
        return not (self.missing or self.error)

    # The "value" property has too many possible types to be useful.
    # It will be deprecated in favour of type-specific properties on
    # subclasses.
    @property
    def value(self) -> Optional[frame.BackwardFrame | int | str | bool | IntEnum]:
        if self._value is None and self._expected:
            raise MissingResponse()
        if self._value and self._value.error and not self._error_acceptable:
            raise ResponseError()
        return self._value

    def __str__(self) -> str:
        try:
            return "{}".format(self.value)
        except (MissingResponse, ResponseError) as e:
            return "{}".format(e)


class NumericResponse(Response):
    _expected = True

    @property
    def value(self) -> int | str:
        if self._value is None:
            return "(missing)"
        if self._value and self._value.error:
            return "(framing error)"
        return self._value.as_integer

    @property
    def as_integer(self) -> int:
        self.raise_for_status()
        assert self._value
        return self._value.as_integer


class NumericResponseMask(NumericResponse):
    @property
    def value(self) -> int | str:
        v = super().value
        if v == 255:
            return "MASK"
        return v

    @property
    def as_maskinteger(self) -> int | Literal["MASK"]:
        v = self.as_integer
        if v == 255:
            return "MASK"
        return v


class YesNoResponse(Response):
    _error_acceptable = True

    @property
    def value(self) -> bool:
        return self._value is not None

    @property
    def as_boolean(self) -> bool:
        return self._value is not None


class BitmapResponseBitDict(type):
    """Metaclass adding dict of status bits."""

    def __init__(cls: type, name: str, bases: tuple[type],
                 attrs: dict[str, object]) -> None:
        if hasattr(cls, "bits"):
            bd = {}
            bit = 0
            for b in cls.bits:
                if b:
                    mangled = b.replace(' ', '_').replace('-', '')
                    bd[mangled] = bit
                bit = bit + 1
            cls._bit_properties = bd


class BitmapResponse(Response, metaclass=BitmapResponseBitDict):
    """A response that consists of several named bits.

    Bits are listed in subclasses with the least-sigificant bit first.
    """
    _expected = True
    _bit_properties: dict[str, int]
    bits: list[Optional[str]] = []

    @property
    def status(self) -> list[str]:
        if self._value is None:
            raise MissingResponse()
        if self._value.error:
            raise ResponseError()
            # return ["response received with framing error"]
        v = self._value[7:0]
        l = []
        for b in self.bits:
            if v & 0x01 and b:
                l.append(b)
            v = (v >> 1)
        return l

    def __getattr__(self, name: str) -> Optional[bool]:
        if name in self._bit_properties:
            if self._value is None:
                return None
            if self._value.error:
                return None
            return bool(self._value[self._bit_properties[name]])
        raise AttributeError

    def __str__(self) -> str:
        try:
            return ",".join(self.status)
        except (MissingResponse, ResponseError) as e:
            return "{}".format(e)


class EnumResponse(Response):
    """
    A response that consists of a number from a pre-defined enumerator
    """

    enumerator: Optional[type[IntEnum]] = None

    @property
    def value(self) -> Optional[frame.BackwardFrame | int | str | IntEnum]:
        if self._value is None and self._expected:
            raise MissingResponse()
        if self._value and self._value.error and not self._error_acceptable:
            raise ResponseError()
        if self._value and self.enumerator:
            return self.enumerator(self._value.as_integer)
        return self._value


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
    response: Optional[type[Response]] = None
    sendtwice = False

    # 16-bit frames may be interpreted differently if they are
    # preceded by the EnableDeviceType command.  If a command needs
    # EnableDeviceType(foo) to be sent first, override devicetype to
    # foo.  This parameter is ignored for all other frame lengths.
    devicetype = 0

    _commands: list[type[Command]] = []
    _supported_devicetypes: set[int] = set()
    _framesizes: dict[int, list[type[Command]]] = {}

    def __init_subclass__(cls) -> None:
        if cls.__name__[0] != '_':
            cls._commands.append(cls)
        if cls.devicetype != 0:
            cls._supported_devicetypes.add(cls.devicetype)
        subs = cls._framesizes.setdefault(cls._framesize, list())
        subs.append(cls)

        # XXX we have a _register_subclass() method which duplicates what
        # we are doing here in __init_subclass__() — we had it before
        # __init_subclass__() existed!
        #
        # For now, keep it working. All uses of this should be replaced
        # by __init_subclass__() methods that extend this method.
        for base in cls.__bases__:
            if issubclass(base, Command):
                base._register_subclass(cls)

    def __init__(self, f: frame.ForwardFrame) -> None:
        if not isinstance(f, frame.ForwardFrame):
            raise TypeError(
                f"{self.__class__.__name__} expected a ForwardFrame, not a {type(f)}"
            )
        self._data = f

    # This is deprecated and will be removed. For now it is overridden in
    # subclasses.
    @classmethod
    def _register_subclass(cls, subclass: type[Command]) -> None:
        pass

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
