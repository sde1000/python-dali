"""Declaration of base types for dali commands and their responses."""

from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from dali import address
from dali import frame
from dali.compat import add_metaclass, python_2_unicode_compatible


class CommandTracker(type):
    """Metaclass keeping track of all the types of Command we understand.

    Commands that have names starting with '_' are treated as abstract
    base classes that will never be instantiated because they do not
    correspond to a DALI frame.
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_commands'):
            cls._commands = []
        else:
            if cls.__name__[0] != '_':
                cls._commands.append(cls)

    @classmethod
    def commands(cls):
        """
        :return: List of known commands if there's any
        """
        return cls._commands


class MissingResponse(Exception):
    """Response was absent where a response was expected."""


class ResponseError(Exception):
    """Response had unexpected framing error."""


@python_2_unicode_compatible
class Response(object):
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

    def __init__(self, val):
        if val is not None and not isinstance(val, frame.BackwardFrame):
            raise TypeError("Response must be passed None or a BackwardFrame")
        self._value = val

    @property
    def value(self):
        if self._value is None and self._expected:
            raise MissingResponse
        if self._value and self._value.error and not self._error_acceptable:
            raise ResponseError
        return self._value

    def __str__(self):
        try:
            return "{}".format(self.value)
        except MissingResponse or ResponseError as e:
            return "{}".format(e)


class YesNoResponse(Response):
    _error_acceptable = True

    @property
    def value(self):
        return self._value is not None


class BitmapResponseBitDict(type):
    """Metaclass adding dict of status bits."""

    def __init__(cls, name, bases, attrs):
        if hasattr(cls, "bits"):
            bd = {}
            bit = 0
            for b in cls.bits:
                if b:
                    mangled = b.replace(' ', '_').replace('-', '')
                    bd[mangled] = bit
                bit = bit + 1
            cls._bit_properties = bd


@python_2_unicode_compatible
@add_metaclass(BitmapResponseBitDict)
class BitmapResponse(Response):
    """A response that consists of several named bits.

    Bits are listed in subclasses with the least-sigificant bit first.
    """
    _expected = True
    bits = []

    @property
    def status(self):
        if self._value is None:
            raise MissingResponse
        if self._value.error:
            return ["response received with framing error"]
        v = self._value[7:0]
        l = []
        for b in self.bits:
            if v & 0x01 and b:
                l.append(b)
            v = (v >> 1)
        return l

    @property
    def error(self):
        if self._value is None:
            return False
        return self._value.error

    def __getattr__(self, name):
        if name in self._bit_properties:
            if self._value is None:
                return
            if self._value.error:
                return
            return self._value[self._bit_properties[name]]
        raise AttributeError

    def __str__(self):
        try:
            return ",".join(self.status)
        except Exception as e:
            return "{}".format(e)


@python_2_unicode_compatible
@add_metaclass(CommandTracker)
class Command(object):
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
    _appctrl = False
    _inputdev = False
    _uses_dtr0 = False
    _uses_dtr1 = False
    _uses_dtr2 = False
    _response = None
    _sendtwice = False

    # 16-bit frames may be interpreted differently if they are
    # preceded by the EnableDeviceType command.  If a command needs
    # EnableDeviceType(foo) to be sent first, override _devicetype to
    # foo.  This parameter is ignored for all other frame lengths.
    _devicetype = 0

    def __init__(self, f):
        assert isinstance(f, frame.ForwardFrame)
        self._data = f

    @classmethod
    def from_frame(cls, f, devicetype=0):
        """Return a Command instance corresponding to the supplied frame.

        If the device type the command is intended for is known
        (i.e. the previous command was EnableDeviceType(foo)) then
        specify it here.

        :parameter frame: a forward frame
        :parameter devicetype: type of device frame is intended for

        :returns: Return a Command instance corresponding to the
        frame.  Returns None if there is no match.
        """
        if cls != Command:
            return

        for dc in cls._commands:
            if dc._devicetype != devicetype:
                continue
            r = dc.from_frame(f)
            if r:
                return r

        # At this point we can simply wrap the frame.  We don't know
        # what kind of command this is (config, query, etc.) so we're
        # unlikely ever to want to transmit it!
        return cls(f)

    @property
    def frame(self):
        """The forward frame to be transmitted for this command."""
        return self._data

    # XXX rename to send_twice ?
    @property
    def is_config(self):
        """Is this a configuration command?  (Does it need repeating to
        take effect?)
        """
        return self._sendtwice

    @property
    def is_query(self):
        """Does this command return a result?"""
        return self._response is not None

    @property
    def response(self):
        """If this command returns a result, use this class for the response.
        """
        return self._response

    @staticmethod
    def _check_destination(destination):
        """Check that a valid destination has been specified.

        destination can be a dali.device.Device object with
        _addressobj attribute, a dali.address.Address object with
        add_to_frame method, or an integer which will be wrapped in a
        dali.address.Address object.
        """
        if hasattr(destination, "_addressobj"):
            destination = destination._addressobj
        if isinstance(destination, int):
            destination = address.Short(destination)
        if hasattr(destination, "add_to_frame"):
            return destination
        raise ValueError("destination must be an integer, dali.device.Device "
                         "object or dali.address.Address object")

    def __str__(self):
        joined = ":".join(
            "{:02x}".format(c) for c in self._data.as_byte_sequence)
        return "({0}){1}".format(type(self), joined)

from_frame = Command.from_frame
