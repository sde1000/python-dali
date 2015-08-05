import sets, time
from . import address, command, device


class DuplicateDevice(Exception):
    """Attempt to add more than one device with the same short address
    to a bus.

    """
    pass


class BadDevice(Exception):
    """Device with invalid attributes.

    """
    pass


class DeviceAlreadyBound(Exception):
    """Attempt to add a device to a bus that is already bound to a
    different bus.

    """
    pass


class NotConnected(Exception):
    """A connection to the DALI bus is required to complete this
    operation, but the bus is not connected.

    """
    pass


class NoFreeAddress(Exception):
    """An unused short address was required but none was available.

    """
    pass


class ProgramShortAddressFailure(Exception):
    """A device did not accept programming of its short address.

    """

    def __init__(self, address):
        self.address = address


class Bus(object):
    """A DALI bus.

    """
    _all_addresses = sets.ImmutableSet(xrange(64))

    def __init__(self, name=None, interface=None):
        self._devices = {}
        self._bus_scanned = False  # Have we scanned the bus for devices?
        self.name = name
        self._interface = interface

    def get_interface(self):
        if not self._interface: raise NotConnected
        return self._interface

    def add_device(self, device):
        if device.bus and device.bus != self:
            raise DeviceAlreadyBound()
        if device.address in self._devices:
            raise DuplicateDevice()
        if not isinstance(device.address, int) or device.address < 0 \
                or device.address > 63:
            raise BadDevice("device address is invalid")
        self._devices[device.address] = device
        device.bus = self

    def unused_addresses(self):
        """Return all short addresses that are not in use.

        """
        used_addresses = sets.ImmutableSet(self._devices.keys())
        return list(self._all_addresses - used_addresses)

    def scan(self):
        """Scan the bus for devices and ensure there are device objects for
        each discovered device.

        """
        i = self.get_interface()
        for sa in xrange(0, 64):
            if sa in self._devices:
                continue
            response = i.send(
                command.QueryBallast(address.Short(sa)))
            if response.value:
                device.Device(address=sa, bus=self)
        self._bus_scanned = True

    def set_search_addr(self, addr):
        i = self.get_interface()
        i.send(command.SetSearchAddrH((addr >> 16) & 0xff))
        i.send(command.SetSearchAddrM((addr >> 8) & 0xff))
        i.send(command.SetSearchAddrL(addr & 0xff))

    def find_next(self, low, high):
        """Find the ballast with the lowest random address.  The caller
        guarantees that there are no ballasts with an address lower
        than 'low'.

        If found, returns the random address.  SearchAddr will be set
        to this address in all ballasts.  The ballast is not
        withdrawn.

        If not found, returns None.

        """
        i = self.get_interface()
        self.set_search_addr(high)
        if low == high:
            response = i.send(command.Compare())
            if response.value == True:
                return low
            return None
        response = i.send(command.Compare())
        if response.value == True:
            midpoint = (low + high) / 2
            return self.find_next(low, midpoint) \
                   or self.find_next(midpoint + 1, high)

    def assign_short_addresses(self):
        """Search for devices on the bus with no short address allocated, and
        allocate each one a short address from the set of unused
        addresses.

        """
        if not self._bus_scanned: self.scan()
        addrs = self.unused_addresses()
        i = self.get_interface()
        i.send(command.Terminate())
        i.send(command.Initialise(broadcast=False, address=None))
        i.send(command.Randomise())
        time.sleep(0.1)  # Randomise may take up to 100ms
        low = 0
        high = 0xffffff
        while low is not None:
            low = self.find_next(low, high)
            if low is not None:
                if addrs:
                    new_addr = addrs.pop(0)
                    i.send(command.ProgramShortAddress(new_addr))
                    r = i.send(command.VerifyShortAddress(new_addr))
                    if r.value != True:
                        raise ProgramShortAddressFailure(new_addr)
                    i.send(command.Withdraw())
                    device.Device(address=new_addr, bus=self)
                else:
                    i.send(command.Terminate())
                    raise NoFreeAddress
                low = low + 1
        i.send(command.Terminate())
