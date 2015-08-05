"""
Delclaration of base type for dali commands and their response

"""

from . import address
import logging
import struct


class CommandTracker(type):
    """
    Metaclass keeping track of all the types of Command we understand.

    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_commands'):
            cls._commands = []
        else:
            cls._commands.append(cls)

    @classmethod
    def commands(cls):
        """
        :return: List of known commands if there's any
        """

        return cls._commands


class Response(object):
    """
    Some DALI commands cause a response from the addressed devices.
    The response is either an 8-bit frame encoding 8-bit data or 0xff
    for "Yes", or a lack of response encoding "No".

    """

    def __init__(self, val):
        """
        If there was no response, call with val=None.

        """
        self._value = val

    @property
    def value(self):
        return self._value

    def __unicode__(self):
        return unicode(self.value)


class YesNoResponse(Response):
    @property
    def value(self):
        return self._value != None


class Command(object):
    """
    A standard DALI command defined in IEC-60929 annex E.

    Subclasses must provide a class method "from_bytes" which, when
    passed a (a,b) command tuple returns a new instance of the class
    corresponding to that command, or "None" if there is no match.

    """

    __metaclass__ = CommandTracker

    _isconfig = False
    _isquery = False
    _response = None
    _devicetype = 0

    def __init__(self, *params):
        self._data = tuple(params)
        Command.check_command_format(self._data)

    @classmethod
    def from_bytes(cls, command, devicetype=0):
        """
        If the device type the command is intended for is known
        (i.e. the previous command was EnableDeviceType(foo)) then
        specify it here.

        :parameter devicetype: type of the desired device

        :returns: Return a Command instance corresponding to the bytes in
        command.  Returns None if there is no match.

        """

        Command.check_command_format(command)

        if cls != Command:
            return None

        if devicetype in cls._devicetype:
            r = devicetype.from_bytes(command)
            if r:
                return r
        else:
            logging.info("The given device type ({0}) is not in the device/command tracer".format(type(devicetype)))
            pass

        # At this point we can simply wrap the bytes we received.  We
        # don't know what kind of command this is (config, query,
        # etc.) so we're unlikely ever to want to transmit it!
        return cls(command)

    @property
    def command(self):
        """
        The two bytes to be transmitted over the wire for this
        command, as a two-tuple of integers.

        """
        return self._data

    @property
    def is_config(self):
        """
        Is this a configuration command?  (Does it need repeating to
        take effect?)

        """
        return self._isconfig

    @property
    def is_query(self):
        """
        Does this command return a result?

        """
        return self._isquery

    @property
    def response(self):
        """
        If this command returns a result, use this class for the response.

        """
        return self._response

    @staticmethod
    def check_command_format(command):
        """
        Checks the input param tye, and throws an exception when it is invalid
        :param command:
        :return:
        """
        if not isinstance(command, tuple) and len(command) < 2 or len(command) > 4:
            raise ValueError("command must be a two to four length tuple")

        for digit in command:
            if not isinstance(digit, int) or digit < 0 or digit > 255:
                raise ValueError("command values must be between [0..255]")

    @property
    def _FORMAT_STRING(self):
        assert isinstance(self._data, tuple)
        pack = ""
        for elem in self._data:
            assert isinstance(elem, int)
            pack += "B"
        return pack

    @property
    def pack(self):
        """
        :return: Bytestream of the object
        """

        return struct.pack(self._FORMAT_STRING, *self._data)

    def __len__(self):
        """
        :return: the length of the dali command in bytes
        """
        return struct.calcsize(self._FORMAT_STRING)

    @staticmethod
    def _check_destination(destination):
        """destination can be a dali.device.Device object with _addressobj
        attribute, a dali.address.Address object with addrbyte attribute,
        or an integer which will be wrapped in a dali.address.Address object.

        """
        if hasattr(destination, "_addressobj"):
            destination = destination._addressobj
        if isinstance(destination, int):
            destination = address.Short(destination)
        if hasattr(destination, "addrbyte"):
            return destination
        raise ValueError("destination must be an integer, dali.device.Device "
                         "object or dali.address.Address object")

    def __unicode__(self):
        return "({0})".format(type(self)) + u":".join("{:02x}".format(ord(c)) for c in self._data)


class ArcPower(Command):
    """
    A command to set the arc power level directly.

    destination is a dali.address.Address or dali.device.Device object
    power is either an integer in the range 0..255, or one of two
    special strings:

    "OFF" sets the ballast off (same as power level 0)
    "MASK" stops any fade in progress (same as power level 255)

    The lamp will fade to the specified power according to its
    programmed fade time.  The MAX LEVEL and MIN LEVEL settings will
    be respected.
    """

    def __init__(self, destination, power):
        if power == "OFF":
            power = 0

        if power == "MASK":
            power = 255

        if not isinstance(power, int):
            raise ValueError("power must be an integer or string")

        if power < 0 or power > 255:
            raise ValueError("power must be in the range 0..255")

        self.destination = self._check_destination(destination)
        self.power = power

        Command.__init__(self, self.destination.addrbyte, power)

    @classmethod
    def from_bytes(cls, command):
        a, b = command
        if a & 0x01:
            return

        addr = address.from_byte(a)

        if addr is None:
            return

        return cls(addr, b)

    def __unicode__(self):
        if self.power == 0:
            power = "OFF"
        elif self.power == 255:
            power = "MASK"
        else:
            power = self.power
        return u"ArcPower(%s,%s)" % (self.destination, power)


class GeneralCommand(Command):
    """
    A command addressed to broadcast, short address or group, i.e. one
    with a destination as defined in E.4.3.2 and which is not a direct
    arc power command.

    """
    _cmdval = None
    _hasparam = False

    def __init__(self, destination, *args):
        if self._cmdval is None:
            raise NotImplementedError

        if self._hasparam:
            if len(args) != 1:
                raise TypeError(
                    "%s.__init__() takes exactly 3 arguments (%d given)" % (
                        self.__class__.__name__, len(args) + 2))

            param = args[0]

            if not isinstance(param, int):
                raise ValueError("param must be an integer")

            if param < 0 or param > 15:
                raise ValueError("param must be in the range 0..15")

            self.param = param

        else:
            if len(args) != 0:
                raise TypeError(
                    "%s.__init__() takes exactly 2 arguments (%d given)" % (
                        self.__class__.__name__, len(args) + 2))
            param = 0

        self.destination = self._check_destination(destination)

        Command.__init__(self, self.destination.addrbyte | 0x01, self._cmdval | param)

    @classmethod
    def from_bytes(cls, command):
        if cls == GeneralCommand:
            return
        a, b = command

        if a & 0x01 == 0:
            return

        if cls._hasparam:
            if b & 0xf0 != cls._cmdval:
                return
        else:
            if b != cls._cmdval:
                return

        addr = address.from_byte(a)

        if addr is None:
            return

        if cls._hasparam:
            return cls(addr, b & 0x0f)

        return cls(addr)

    def __unicode__(self):
        if self._hasparam:
            return u"%s(%s,%s)" % (self.__class__.__name__, self.destination,
                                   self.param)
        return u"%s(%s)" % (self.__class__.__name__, self.destination)


class ConfigCommand(GeneralCommand):
    """
    Configuration commands must be transmitted twice within 100ms,
    with no other commands addressing the same ballast being
    transmitted in between.

    """
    _isconfig = True


class SpecialCommand(Command):
    """Special commands are broadcast and are received by all devices.

    """
    _hasparam = False

    def __init__(self, *args):
        if self._hasparam:
            if len(args) != 1:
                raise TypeError(
                    "{}.__init__() takes exactly 2 arguments ({} given)".format(
                        self.__class__.__name__, len(args) + 1))
            param = args[0]
            if not isinstance(param, int):
                raise ValueError("param must be an int")
            if param < 0 or param > 255:
                raise ValueError("param must be in range 0..255")
            self.param = param
        else:
            if len(args) != 0:
                raise TypeError(
                    "{}.__init__() takes exactly 1 arguments ({} given)".format(
                        self.__class__.__name__, len(args) + 1))
            param = 0
        self.param = param

    @property
    def command(self):
        return (self._cmdval, self.param)

    @classmethod
    def from_bytes(cls, command):
        if cls == SpecialCommand:
            return
        a, b = command
        if a == cls._cmdval:
            if cls._hasparam:
                return cls(b)
            else:
                if b == 0:
                    return cls()

    def __unicode__(self):
        if self._hasparam:
            return u"{}({})".format(self.__class__.__name__, self.param)
        return u"{}()".format(self.__class__.__name__)


class QueryCommand(GeneralCommand):
    """
    Query commands are answered with "Yes", "No" or 8-bit information.

    "Yes" is encoded as 0xff (255)
    "No" is encoded as no response

    Query commands addressed to more than one ballast may receive
    invalid answers as all ballasts addressed will answer.  It may be
    useful to do this to check whether any ballast in a group provides
    a "Yes" response, for example to "QueryLampFailure".

    """
    _isquery = True
    _response = Response
