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
# sequences
###############################################################################

class DALISequenceError(DALIError):
    """An error occurred during execution of a command sequence."""
    pass

class ProgramShortAddressFailure(DALIError):
    """A device did not accept programming of its short address."""

    def __init__(self, address):
        self.address = address


###############################################################################
# driver
###############################################################################

class DriverError(DALIError):
    """Base Exception for driver related errors."""

class CommunicationError(DriverError):
    """Unable to communicate with the device
    """

class UnsupportedFrameTypeError(DriverError):
    """Device driver does not support this type of frame
    """
