"""Device addressing

Addressing for control gear is described in IEC 62386-102 section 7.2.
Forward frames can be addressed to one of 64 short addresses, one of
16 group addresses, to all devices, or to all devices that do not have
a short address assigned.

Addressing for control devices is described in IEC 62386-103 section
7.2.1.  Command frames can be addressed to one of 64 short addresses,
one of 32 group addresses, to all devices, or to all devices that do
not have a short address assigned.

Addressing for event messages is described in IEC 62386-103 section
7.2.2.  Decoding of event messages is currently not implemented.
"""

from __future__ import unicode_literals

class IncompatibleFrame(Exception):
    """Cannot set destination address in supplied frame"""
    pass

_bad_frame_length = IncompatibleFrame("Unsupported frame size")

class AddressTracker(type):
    """Metaclass keeping track of all the types of Address we understand."""

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_addrtypes'):
            cls._addrtypes = []
        else:
            cls._addrtypes.append(cls)


class Address(object):
    """An address for one or more ballasts."""
    __metaclass__ = AddressTracker

    @classmethod
    def from_frame(cls, f):
        """Return an Address object

        If the frame has a destination address, return a suitable
        Address object; otherwise return None.
        """
        if cls != Address:
            return
        for at in cls._addrtypes:
            r = at.from_frame(f)
            if r:
                return r

    def add_to_frame(self, f):
        raise IncompatibleFrame("Cannot add unknown address to any frame")

    @classmethod
    def from_byte(cls, a):
        """Given an address byte (the first of the two bytes in a DALI
        command), return a corresponding Address object or None if the
        byte is for a special command.
        """
        if cls != Address:
            return
        for at in cls._addrtypes:
            r = at.from_byte(a)
            if r:
                return r

    @property
    def addrbyte(self):
        """The DALI address byte encoding this address."""
        return None

    def __unicode__(self):
        return "<no address>"


class Broadcast(Address):
    """All control gear or devices connected to the network."""

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:9] == 0x7f:
                return cls()
        elif len(f) == 24:
            if f[16] and f[23:17] == 0x7f:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15:9] = 0x7f
        elif len(f) == 24:
            f[23:17] = 0x7f
        else:
            raise _bad_frame_length

    @property
    def addrbyte(self):
        """The DALI address byte for broadcasts."""
        return 0xfe

    @classmethod
    def from_byte(cls, a):
        if a == 0xfe or a == 0xff:
            return cls()

    def __eq__(self, other):
        return isinstance(other, Broadcast)

    def __unicode__(self):
        return "<broadcast>"


class BroadcastUnaddressed(Address):
    """All unaddressed control gear or devices

    All control gear or devices in the system that have no short
    address assigned.
    """

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:9] == 0x7e:
                return cls()
        elif len(f) == 24:
            if f[16] and f[23:17] == 0x7e:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15:9] = 0x7e
        elif len(f) == 24:
            f[23:17] = 0x7e
        else:
            raise _bad_frame_length

    @property
    def addrbyte(self):
        """The DALI address byte for broadcasts to unaddressed devices."""
        return 0xfc

    @classmethod
    def from_byte(cls, a):
        if a == 0xfc or a == 0xfd:
            return cls()

    def __eq__(self, other):
        return isinstance(other, BroadcastUnaddressed)

    def __unicode__(self):
        return "<broadcast unaddressed>"


class Group(Address):
    """All control gear or devices that are members of the specified group."""

    def __init__(self, group):
        if not isinstance(group, int):
            raise ValueError("group must be an integer")
        if group < 0 or group > 31:
            raise ValueError("group must be in the range 0..31")
        self.group = group

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:13] == 0x4:
                return cls(f[12:9])
        elif len(f) == 24:
            if f[16] and f[23:22] == 0x2:
                return cls(f[21:17])

    def add_to_frame(self, f):
        if len(f) == 16:
            if self.group > 15:
                raise IncompatibleFrame(
                    "Groups 16..31 are not supported in 16-bit forward frames")
            f[15:13] = 0x4
            f[12:9] = self.group
        elif len(f) == 24:
            f[23:22] = 0x2
            f[21:17] = self.group
        else:
            raise _bad_frame_length

    @property
    def addrbyte(self):
        """The DALI address byte for this group."""
        return 0x80 | (self.group << 1)

    @classmethod
    def from_byte(cls, a):
        if (a & 0xe0) == 0x80:
            return cls((a & 0x1e) >> 1)

    def __eq__(self, other):
        return isinstance(other, Group) and other.group == self.group

    def __unicode__(self):
        return "<group %d>" % self.group


class Short(Address):
    """The control gear or device that has this address.

    In a correctly configured DALI network, no more than one control
    gear will have a particular short address, and no more than one
    control device will have a particular short address.  The short
    address spaces for control gear and control devices are separate;
    it is legal for a control gear and control device to share a short
    address.
    """

    def __init__(self, address):
        if not isinstance(address, int):
            raise ValueError("address must be an integer")
        if address < 0 or address > 63:
            raise ValueError("address must be in the range 0..63")
        self.address = address

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if not f[15]:
                return cls(f[14:9])
        elif len(f) == 24:
            if f[16] and not f[23]:
                return cls(f[22:17])

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15] = False
            f[14:9] = self.address
        elif len(f) == 24:
            f[23] = False
            f[22:17] = self.address
        else:
            raise _bad_frame_length

    @property
    def addrbyte(self):
        """The DALI address byte for this particular ballast."""
        return (self.address << 1)

    @classmethod
    def from_byte(cls, a):
        if (a & 0x80) == 0x00:
            return cls((a & 0x7e) >> 1)

    def __eq__(self, other):
        return isinstance(other, Short) and other.address == self.address

    def __unicode__(self):
        return "<address %d>" % self.address

from_byte = Address.from_byte
from_frame = Address.from_frame
