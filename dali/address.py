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
        if not hasattr(cls, "_addrtypes"):
            cls._addrtypes = []
        else:
            cls._addrtypes.append(cls)


class Address(metaclass=AddressTracker):
    """An address for one or more ballasts."""

    required_frame_size = None

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


class GearAddress(Address):
    """Base class for control gear addresses"""

    required_frame_size = 16


class DeviceAddress(Address):
    """Base class for control device addresses"""

    required_frame_size = 24


class GearBroadcast(GearAddress):
    """All control gear connected to the network"""

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:9] == 0x7F:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15:9] = 0x7F
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, GearBroadcast)

    def __str__(self):
        return "<broadcast (control gear)>"


# Broadcast alias provided for legacy purposes, new code should avoid
# ambiguity by using either GearBroadcast or DeviceBroadcast
Broadcast = GearBroadcast


class DeviceBroadcast(DeviceAddress):
    """All control devices connected to the network"""

    @classmethod
    def from_frame(cls, f):
        if len(f) == 24:
            if f[16] and f[23:17] == 0x7F:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 24:
            f[23:17] = 0x7F
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, DeviceBroadcast)

    def __str__(self):
        return "<broadcast (control device)>"


class GearBroadcastUnaddressed(GearAddress):
    """All unaddressed control gear

    All control gear in the system that have no short address assigned.
    """

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:9] == 0x7E:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15:9] = 0x7E
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, GearBroadcastUnaddressed)

    def __str__(self):
        return "<broadcast unaddressed (control gear)>"


# BroadcastUnaddressed alias provided for legacy purposes, new code should
# avoid ambiguity by using either GearBroadcastUnaddressed or
# DeviceBroadcastUnaddressed
BroadcastUnaddressed = GearBroadcastUnaddressed


class DeviceBroadcastUnaddressed(DeviceAddress):
    """All unaddressed control devices

    All control devices in the system that have no short address assigned.
    """

    @classmethod
    def from_frame(cls, f):
        if len(f) == 24:
            if f[16] and f[23:17] == 0x7E:
                return cls()

    def add_to_frame(self, f):
        if len(f) == 24:
            f[23:17] = 0x7E
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, DeviceBroadcastUnaddressed)

    def __str__(self):
        return "<broadcast unaddressed (control device)>"


class GearGroup(GearAddress):
    """All control gear that are members of the specified group"""

    def __init__(self, group: int):
        if not isinstance(group, int):
            raise ValueError("group must be an integer")
        if group < 0 or group > 15:
            raise ValueError("group must be in the range 0..15")
        self.group = group

    @classmethod
    def from_frame(cls, f):
        if len(f) == 16:
            if f[15:13] == 0x4:
                return cls(f[12:9])

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15:13] = 0x4
            f[12:9] = self.group
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, GearGroup) and other.group == self.group

    def __str__(self):
        return f"<group (control gear) {self.group}>"


# Group alias provided for legacy purposes, new code should avoid ambiguity
# by using either GearGroup or DeviceGroup
Group = GearGroup


class DeviceGroup(DeviceAddress):
    """All control devices that are members of the specified group"""

    def __init__(self, group: int):
        if not isinstance(group, int):
            raise ValueError("group must be an integer")
        if group < 0 or group > 31:
            raise ValueError("group must be in the range 0..31")
        self.group = group

    @classmethod
    def from_frame(cls, f):
        if len(f) == 24:
            if f[16] and f[23:22] == 0x2:
                return cls(f[21:17])

    def add_to_frame(self, f):
        if len(f) == 24:
            f[23:22] = 0x2
            f[21:17] = self.group
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, DeviceGroup) and other.group == self.group

    def __str__(self):
        return f"<group (control device) {self.group}>"


class GearShort(GearAddress):
    """
    The control gear that has this address.

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

    def add_to_frame(self, f):
        if len(f) == 16:
            f[15] = False
            f[14:9] = self.address
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, GearShort) and other.address == self.address

    def __str__(self):
        return f"<address (control gear) {self.address}>"


# Short alias provided for legacy purposes, new code should avoid ambiguity
# by using either GearShort or DeviceShort
Short = GearShort


class DeviceShort(DeviceAddress):
    """
    The control device that has this address.

    In a correctly configured DALI network, no more than one control
    gear will have a particular short address, and no more than one
    control device will have a particular short address.  The short
    address spaces for control gear and control devices are separate;
    it is legal for a control gear and control device to share a short
    address.
    """

    def __init__(self, address: int):
        if not isinstance(address, int):
            raise ValueError("address must be an integer")
        if address < 0 or address > 63:
            raise ValueError("address must be in the range 0..63")
        self.address = address

    @classmethod
    def from_frame(cls, f):
        if len(f) == 24:
            if f[16] and not f[23]:
                return cls(f[22:17])

    def add_to_frame(self, f):
        if len(f) == 24:
            f[23] = False
            f[22:17] = self.address
        else:
            raise _bad_frame_length

    def __eq__(self, other):
        return isinstance(other, DeviceShort) and other.address == self.address

    def __str__(self):
        return f"<address (control device) {self.address}>"


from_frame = Address.from_frame


###############################################################################
# Instance bytes
###############################################################################


class Instance:
    def __init__(self):
        raise NotImplementedError

    @property
    def value(self):
        if hasattr(self, "_value"):
            return self._value

    def add_to_frame(self, f):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if hasattr(self, "_value") and hasattr(other, "_value"):
                if self._value == other._value:
                    return True

        return False


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
    _flags = 0xC0


class FeatureInstanceNumber(_AddressedInstance):
    _flags = 0x20


class FeatureInstanceGroup(_AddressedInstance):
    _flags = 0xA0


class FeatureInstanceType(_AddressedInstance):
    _flags = 0x60


class FeatureInstanceBroadcast(_UnaddressedInstance):
    _val = 0xFD


class InstanceBroadcast(_UnaddressedInstance):
    _val = 0xFF


class FeatureDevice(_UnaddressedInstance):
    _val = 0xFC


class Device(_UnaddressedInstance):
    _val = 0xFE


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
    elif b == 0xFD:
        return FeatureInstanceBroadcast()
    elif b == 0xFF:
        return InstanceBroadcast()
    elif b == 0xFC:
        return FeatureDevice()
    elif b == 0xFE:
        return Device()
    return ReservedInstance(b)
