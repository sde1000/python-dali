from __future__ import unicode_literals


class IncompatibleFrame(Exception):
    """Cannot set destination address in supplied frame"""


class DuplicateDevice(Exception):
    """Attempt to add more than one device with the same short address
    to a bus.
    """


class BadDevice(Exception):
    """Device with invalid attributes."""


class DeviceAlreadyBound(Exception):
    """Attempt to add a device to a bus that is already bound to a
    different bus.
    """


class NotConnected(Exception):
    """A connection to the DALI bus is required to complete this
    operation, but the bus is not connected.
    """


class NoFreeAddress(Exception):
    """An unused short address was required but none was available."""


class ProgramShortAddressFailure(Exception):
    """A device did not accept programming of its short address."""

    def __init__(self, address):
        self.address = address


class MissingResponse(Exception):
    """Response was absent where a response was expected."""


class ResponseError(Exception):
    """Response had unexpected framing error."""


class CommunicationError(Exception):
    """Exception raised in case of communication error with daliserver.
    """
