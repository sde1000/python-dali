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
# memory access
###############################################################################


class MemoryError(DALIError):
    """Base Exception for memory related errors."""
    pass


class LatchingNotSupported(MemoryError):
    """This memory bank does not support latching."""
    pass


class MemoryLocationNotImplemented(MemoryError):
    """The addressed device does not implement the requested memory location."""
    pass


class MemoryWriteError(MemoryError):
    """Base Exception for memory writing errors."""
    pass


class MemoryValueNotWriteable(MemoryWriteError):
    """The memory value is not writeable.

    Writing of this memory value is not supported by python-dali.
    """
    pass


class MemoryLocationNotWriteable(MemoryWriteError):
    """No response to attempted memory write

    No response was received from the bus unit when attempting to
    write to a memory location.
    """
    pass


class MemoryWriteFailure(MemoryWriteError):
    """Check of DTR0 at end of write yielded unexpected value

    The memory value has not been written correctly. Another attempt
    to write the value may succeed.
    """
    pass


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
