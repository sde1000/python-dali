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
        return u"Command(0x%02x,0x%02x)" % (self.a, self.b)

