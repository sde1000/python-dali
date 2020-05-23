"""Declaration of base types for dali commands and their responses."""

from dali import address
from dali import frame
from dali.exceptions import MissingResponse
from dali.exceptions import ResponseError
import warnings


class _CommandTracker(type):
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
        if not hasattr(cls, '_supported_devicetypes'):
            cls._supported_devicetypes = set()
        else:
            if cls.devicetype != 0:
                cls._supported_devicetypes.add(cls.devicetype)
        for c in bases:
            if issubclass(c, Command):
                c._register_subclass(cls)


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

    def __init__(self, val):
        if val is not None and not isinstance(val, frame.BackwardFrame):
            raise TypeError("Response must be passed None or a BackwardFrame")
        self._value = val

    @property
    def raw_value(self):
        return self._value

    @property
    def value(self):
        if self._value is None and self._expected:
            raise MissingResponse()
        if self._value and self._value.error and not self._error_acceptable:
            raise ResponseError()
        return self._value

    def __str__(self):
        try:
            return "{}".format(self.value)
        except MissingResponse or ResponseError as e:
            return "{}".format(e)

class NumericResponse(Response):
    _expected = True

    @property
    def value(self):
        if self._value is None:
            return "(missing)"
        if self._value and self._value.error:
            return "(framing error)"
        return self._value.as_integer

class NumericResponseMask(NumericResponse):
    @property
    def value(self):
        v = super(NumericResponseMask, self).value
        if v == 255:
            return "MASK"
        return v

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


class BitmapResponse(Response, metaclass=BitmapResponseBitDict):
    """A response that consists of several named bits.

    Bits are listed in subclasses with the least-sigificant bit first.
    """
    _expected = True
    bits = []

    @property
    def status(self):
        if self._value is None:
            raise MissingResponse()
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
        # XXX: be more explicit which exception to catch
        except Exception as e:
            return "{}".format(e)


class Command(metaclass=_CommandTracker):
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
    response = None
    sendtwice = False

    # 16-bit frames may be interpreted differently if they are
    # preceded by the EnableDeviceType command.  If a command needs
    # EnableDeviceType(foo) to be sent first, override devicetype to
    # foo.  This parameter is ignored for all other frame lengths.
    devicetype = 0

    # devicetype used to be called "_devicetype".  This property is
    # here for compatibility with older code that relied on this.  It
    # will be removed in a future release.
    @property
    def _devicetype(self):
        warnings.warn("'_devicetype' has been renamed to 'devicetype'",
                      DeprecationWarning, stacklevel=2)
        return self.devicetype

    def __init__(self, f):
        assert isinstance(f, frame.ForwardFrame)
        self._data = f

    _framesizes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        subs = cls._framesizes.setdefault(subclass._framesize, list())
        subs.append(subclass)

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
            raise Exception(f"from_frame not overridden in class {cls}")

        # At the top level, we simply distinguish by frame size
        subs = cls._framesizes.get(len(f), [])

        for c in subs:
            r = c.from_frame(f, devicetype=devicetype)
            if r:
                return r

        # The frame doesn't match any of the commands we know.
        return cls(f)

    @property
    def frame(self):
        """The forward frame to be transmitted for this command."""
        return self._data

    @property
    def is_config(self):
        """Is this a configuration command?  (Does it need repeating to
        take effect?)

        Use of this property is deprecated: access the "sendtwice"
        attribute directly.
        """
        warnings.warn("Access 'sendtwice' directly instead of using 'is_config'",
                      DeprecationWarning, stacklevel=2)
        return self.sendtwice

    @property
    def is_query(self):
        """Does this command return a result?"""
        return self.response is not None

    @property
    def _response(self):
        """If this command returns a result, use this class for the response.

        This property is provided for compatibility with old code.
        Access the "response" attribute directly.
        """
        warnings.warn("Access 'response' directly instead of using '_response'",
                      DeprecationWarning, stacklevel=2)
        return self.response

    @staticmethod
    def _check_destination(destination):
        """Check that a valid destination has been specified.

        destination can be a dali.bus.Device object with
        address_obj attribute, a dali.address.Address object with
        add_to_frame method, or an integer which will be wrapped in a
        dali.address.Address object.
        """
        if hasattr(destination, 'address_obj'):
            destination = destination.address_obj
        if isinstance(destination, int):
            destination = address.Short(destination)
        if hasattr(destination, 'add_to_frame'):
            return destination
        raise ValueError('destination must be an integer, dali.bus.Device '
                         'object or dali.address.Address object')

    def __str__(self):
        joined = ":".join(
            "{:02x}".format(c) for c in self._data.as_byte_sequence)
        return "({0}){1}".format(type(self), joined)

from_frame = Command.from_frame
