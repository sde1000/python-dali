class AddressTracker(type):
    """Metaclass keeping track of all the types of Address we understand.
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_addrtypes'):
            cls._addrtypes = []
        else:
            cls._addrtypes.append(cls)


class Address(object):
    """An address for one or more ballasts.
    """
    __metaclass__ = AddressTracker

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
        """The DALI address byte encoding this address.
        """
        return None

    def __unicode__(self):
        return u"<no address>"


class Broadcast(Address):
    """All control gear connected to the network.
    """

    @property
    def addrbyte(self):
        """The DALI address byte for broadcasts.
        """
        return 0xfe

    @classmethod
    def from_byte(cls, a):
        if a == 0xfe or a == 0xff:
            return cls()

    def __eq__(self, other):
        return isinstance(other, Broadcast)

    def __unicode__(self):
        return u"<broadcast>"


class BroadcastUnaddressed(Address):
    """All control devices in the system that have no short address.
    """

    @property
    def addrbyte(self):
        """The DALI address byte for broadcasts to unaddressed devices.
        """
        return 0xfc

    @classmethod
    def from_byte(cls, a):
        if a == 0xfc or a == 0xfd:
            return cls()

    def __eq__(self, other):
        return isinstance(other, BroadcastUnaddressed)

    def __unicode__(self):
        return u"<broadcast unaddressed>"


class Group(Address):
    """All ballasts that are members of the specified group.
    """

    def __init__(self, group):
        if not isinstance(group, int):
            raise ValueError("group must be an integer")
        if group < 0 or group > 15:
            raise ValueError("group must be in the range 0..15")
        self.group = group

    @property
    def addrbyte(self):
        """The DALI address byte for this group.
        """
        return 0x80 | (self.group << 1)

    @classmethod
    def from_byte(cls, a):
        if (a & 0xe0) == 0x80:
            return cls((a & 0x1e) >> 1)

    def __eq__(self, other):
        return isinstance(other, Group) and other.group == self.group

    def __unicode__(self):
        return u"<group %d>" % self.group


class Short(Address):
    """The particular ballast that has this address.

    In a correctly configured DALI network, no more than one ballast will
    have a particular short address.
    """

    def __init__(self, address):
        if not isinstance(address, int):
            raise ValueError("address must be an integer")
        if address < 0 or address > 63:
            raise ValueError("address must be in the range 0..63")
        self.address = address

    @property
    def addrbyte(self):
        """The DALI address byte for this particular ballast.
        """
        return (self.address << 1)

    @classmethod
    def from_byte(cls, a):
        if (a & 0x80) == 0x00:
            return cls((a & 0x7e) >> 1)

    def __eq__(self, other):
        return isinstance(other, Short) and other.address == self.address

    def __unicode__(self):
        return u"<address %d>" % self.address


from_byte = Address.from_byte

__all__ = ["Address", "Broadcast", "Group", "Short", "from_byte"]
