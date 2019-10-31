from __future__ import division
from __future__ import unicode_literals
from dali import address
from dali.address import Short
from dali.exceptions import BadDevice
from dali.exceptions import DeviceAlreadyBound
from dali.exceptions import DuplicateDevice
from dali.exceptions import NoFreeAddress
from dali.exceptions import NotConnected
from dali.exceptions import ProgramShortAddressFailure
import dali.gear.general as gear
import time


class Device(object):
    """Any DALI slave device that has been configured with a short address."""

    def __init__(self, address, randomAddress=None, deviceType=None, groups=None, bus=None):
        if not isinstance(address, int) or address < 0 or address > 63:
            raise ValueError("address must be an integer in the range 0..63")
        self.address = address
        self.address_obj = Short(address)
        self.bus = None
        if bus:
            self.bind(bus)
        self.randomAddress = randomAddress
        self.deviceType = deviceType
        self.groups = groups

    def bind(self, bus):
        """Bind this device object to a particular DALI bus."""
        bus.add_device(self)


class Bus(object):
    """A DALI bus."""

    _all_addresses = set(range(64))

    def __init__(self, name=None, interface=None):
        self._devices = {}
        self._bus_scanned = False  # Have we scanned the bus for devices?
        self.name = name
        self._interface = interface

    def get_interface(self):
        if not self._interface:
            raise NotConnected()
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
        """Return all short addresses that are not in use."""
        used_addresses = set(self._devices.keys())
        return list(self._all_addresses - used_addresses)

    def scan(self):
        """Scan the bus for devices and ensure there are device objects for
        each discovered device.
        """
        i = self.get_interface()
        for sa in range(64):
            if sa in self._devices:
                continue
            response = i.send(gear.QueryControlGearPresent(address.Short(sa)))
            if response.value:
                Device(address=sa, bus=self)
        self._bus_scanned = True

    def set_search_addr(self, addr):
        i = self.get_interface()
        i.send(gear.SetSearchAddrH((addr >> 16) & 0xff))
        i.send(gear.SetSearchAddrM((addr >> 8) & 0xff))
        i.send(gear.SetSearchAddrL(addr & 0xff))

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
            response = i.send(gear.Compare())
            if response.value is True:
                return low
            return None
        response = i.send(gear.Compare())
        if response.value is True:
            midpoint = (low + high) // 2
            return self.find_next(low, midpoint) \
                or self.find_next(midpoint + 1, high)

    def search_bus(self, broadcast=False):
        """ Initialize bus with broadcast on or off and find the devices from the bus

        """
        addrs = self.unused_addresses()
        i = self.get_interface()
        i.send(gear.Terminate())
        i.send(gear.Initialise(broadcast=broadcast, address=None))
        i.send(gear.Randomise())
        # Randomise may take up to 100ms
        time.sleep(0.1)
        low = 0
        high = 0xffffff
        while low is not None:
            low = self.find_next(low, high)
            if low is not None:
                if addrs:
                    new_addr = addrs.pop(0)
                    i.send(gear.ProgramShortAddress(new_addr))
                    r = i.send(gear.VerifyShortAddress(new_addr))
                    if r.value is not True:
                        ProgramShortAddressFailure(new_addr)
                        print(f"Error in programming short address {new_addr}")
                    i.send(gear.Withdraw())
                    Device(address=new_addr, randomAddress=low, bus=self)
                else:
                    i.send(gear.Terminate())
                    raise NoFreeAddress()
                low = low + 1
        i.send(gear.Terminate())

    def assign_short_addresses(self):
        """Search for devices on the bus with no short address allocated, and
        allocate each one a short address from the set of unused
        addresses.
        """
        if not self._bus_scanned:
            self.scan()
        self.search_bus(broadcast=False)
        self.query_device_types()
        self.query_groups()

    def initialize_bus(self):
        """Initialize bus
        """
        self._devices = {}
        self.search_bus(broadcast=True)
        self.query_device_types()
        self.query_groups()

    def query_device_types(self):
        """Find the device types of the devices in the bus
        """
        i = self.get_interface()
        for sa in range(64):
            if sa in self._devices:
                self._devices[sa].deviceType = i.send(gear.QueryDeviceType(sa))

    def query_groups(self):
        """Find the groups of the devices in the bus
        """
        i = self.get_interface()
        for sa in range(64):
            if sa in self._devices:
                group1 = i.send(gear.QueryGroupsZeroToSeven(sa))
                group2 = i.send(gear.QueryGroupsEightToFifteen(sa))
                try:
                    group1 = group1.value.as_integer
                    group2 = group2.value.as_integer
                except:
                    self._devices[sa].group = None
                else:
                    self._devices[sa].groups = self.parse_groups(group1, group2)

    def parse_groups(self, group1, group2):
        groups = ""
        if (group1 & 1<<0) != 0:
            groups += "0, "
        if (group1 & 1<<1) != 0:
            groups += "1, "
        if (group1 & 1<<2) != 0:
            groups += "2, "
        if (group1 & 1<<3) != 0:
            groups += "3, "
        if (group1 & 1<<4) != 0:
            groups += "4, "
        if(group1 & 1 << 5) != 0:
            groups += "5, "
        if (group1 & 1 << 6) != 0:
            groups += "6, "
        if (group1 & 1 << 7) != 0:
            groups += "7, "
        if (group2 & 1 << 0) != 0:
            groups += "8, "
        if (group2 & 1 << 1) != 0:
            groups += "9, "
        if (group2 & 1 << 2) != 0:
            groups += "10, "
        if (group2 & 1 << 3) != 0:
            groups += "11, "
        if (group2 & 1 << 4) != 0:
            groups += "12, "
        if (group2 & 1 << 5) != 0:
            groups += "13, "
        if (group2 & 1 << 6) != 0:
            groups += "14, "
        if (group2 & 1 << 7) != 0:
            groups += "15, "
        groups = groups[:-2]

        return groups
