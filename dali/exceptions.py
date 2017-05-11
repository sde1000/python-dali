from __future__ import unicode_literals


###############################################################################
# general
###############################################################################

class DALIError(Exception):
    """Base exception for DALI related errors."""


###############################################################################
# address
###############################################################################

class AddressError(DALIError):
    """Base Exception for address related errors."""


class IncompatibleFrame(AddressError):
    """Cannot set destination address in supplied frame"""


###############################################################################
# command
###############################################################################

class CommandError(DALIError):
    """Base Exception for command related errors."""


class MissingResponse(CommandError):
    """Response was absent where a response was expected."""


class ResponseError(CommandError):
    """Response had unexpected framing error."""


###############################################################################
# bus
###############################################################################

class BusError(DALIError):
    """Base Exception for bus related errors."""


class BadDevice(BusError):
    """Device with invalid attributes."""


class DeviceAlreadyBound(BusError):
    """Attempt to add a device to a bus that is already bound to a
    different bus.
    """


class DuplicateDevice(BusError):
    """Attempt to add more than one device with the same short address
    to a bus.
    """


class NoFreeAddress(BusError):
    """An unused short address was required but none was available."""


class NotConnected(BusError):
    """A connection to the DALI bus is required to complete this
    operation, but the bus is not connected.
    """


class ProgramShortAddressFailure(BusError):
    """A device did not accept programming of its short address."""

    def __init__(self, address):
        self.address = address


###############################################################################
# driver
###############################################################################

class DriverError(DALIError):
    """Base Exception for driver related errors."""


class CommunicationError(DriverError):
    """Exception raised in case of communication error with backend.
    """
