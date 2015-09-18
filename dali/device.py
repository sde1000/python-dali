from dali.address import Short


# XXX: descriptor classes for DALI device attributes goes here...


class Device(object):
    """Any DALI slave device that has been configured with a short
    address.
    """

    def __init__(self, address, name=None, bus=None):
        if not isinstance(address, int) or address < 0 or address > 63:
            raise ValueError("address must be an integer in the range 0..63")
        self.address = address
        self._addressobj = Short(address)
        self.bus = None
        if bus:
            self.bind(bus)

    def bind(self, bus):
        """Bind this device object to a particular DALI bus."""
        bus.add_device(self)
