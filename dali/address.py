"""Device addressing

Addressing for control gear is described in IEC 62386-102 section 7.2.
Forward frames can be addressed to one of 64 short addresses, one of
16 group addresses, to all devices, or to all devices that do not have
a short address assigned.

Addressing for control devices is described in IEC 62386-103 section
7.2.1.2.  Command frames can be addressed to one of 64 short
addresses, one of 32 group addresses, to all devices, or to all
devices that do not have a short address assigned.

Addressing for control device instances is described in IEC 62386-103
section 7.2.1.3.  Command frames can be addressed to one of 32
instance numbers, one of 32 instance groups, one of 32 instance types,
or to all instances (broadcast).  For all those types of address,
command frames can also be addressed to features.

Addressing for event messages is described in IEC 62386-103 section
7.2.2.  Decoding of event messages is currently not implemented.
"""

from dali.exceptions import IncompatibleFrame


_bad_frame_length = IncompatibleFrame("Unsupported frame size")


###############################################################################
# Address bytes
###############################################################################

class AddressTracker(type):
    """Metaclass keeping track of all the types of Address we understand."""

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_addrtypes'):
            cls._addrtypes = []
        else:
            cls._addrtypes.append(cls)


class Address(metaclass=AddressTracker):
    """An address for one or more ballasts."""

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

    def __str__(self):
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

    def __eq__(self, other):
        return isinstance(other, Broadcast)

    def __str__(self):
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

    def __eq__(self, other):
        return isinstance(other, BroadcastUnaddressed)

    def __str__(self):
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

    def __eq__(self, other):
        return isinstance(other, Group) and other.group == self.group

    def __str__(self):
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

    def __eq__(self, other):
        return isinstance(other, Short) and other.address == self.address

    def __str__(self):
        return "<address %d>" % self.address


from_frame = Address.from_frame


###############################################################################
# Instance bytes
###############################################################################

class Instance:
    def __init__(self):
        raise NotImplementedError

    def add_to_frame(self, f):
        raise NotImplementedError


class ReservedInstance(Instance):
    """A reserved instance byte."""

    def __init__(self, value):
        self._value = value

    def add_to_frame(self, f):
        if len(f) != 24:
            raise _bad_frame_length
        f[15:8] = self._value

    def __str__(self):
        return "ReservedInstance({:02x})".format(self._value)


class _AddressedInstance(Instance):
    _flags = None
    def __init__(self, value):
        if not isinstance(value, int):
            raise ValueError("value must be an integer")
        if value < 0 or value > 31:
            raise ValueError("value must be in the range 0..31")
        self._value = value

    def add_to_frame(self, f):
        if len(f) != 24:
            raise _bad_frame_length
        f[15:8] = self._flags | self._value

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self._value)


class _UnaddressedInstance(Instance):
    _val = None

    def __init__(self):
        pass

    def add_to_frame(self, f):
        if len(f) != 24:
            raise _bad_frame_length
        f[15:8] = self._val

    def __str__(self):
        return "{}()".format(self.__class__.__name__)


class InstanceNumber(_AddressedInstance):
    _flags = 0x00


class InstanceGroup(_AddressedInstance):
    _flags = 0x80


class InstanceType(_AddressedInstance):
    _flags = 0xc0


class FeatureInstanceNumber(_AddressedInstance):
    _flags = 0x20


class FeatureInstanceGroup(_AddressedInstance):
    _flags = 0xa0


class FeatureInstanceType(_AddressedInstance):
    _flags = 0x60


class FeatureInstanceBroadcast(_UnaddressedInstance):
    _val = 0xfd


class InstanceBroadcast(_UnaddressedInstance):
    _val = 0xff


class FeatureDevice(_UnaddressedInstance):
    _val = 0xfc


class Device(_UnaddressedInstance):
    _val = 0xfe


def instance_from_frame(f):
    if len(f) != 24:
        return
    flags = f[15:13]
    p = f[12:8]
    b = f[15:8]
    if flags == 0:
        return InstanceNumber(p)
    elif flags == 4:
        return InstanceGroup(p)
    elif flags == 6:
        return InstanceType(p)
    elif flags == 1:
        return FeatureInstanceNumber(p)
    elif flags == 5:
        return FeatureInstanceGroup(p)
    elif flags == 3:
        return FeatureInstanceType(p)
    elif b == 0xfd:
        return FeatureInstanceBroadcast()
    elif b == 0xff:
        return InstanceBroadcast()
    elif b == 0xfc:
        return FeatureDevice()
    elif b == 0xfe:
        return Device()
    return ReservedInstance(b)
