"""Commands for firmware transfer, carried in 32-bit forward frames.

Parts 102 and 103 of IEC 62386 reserve 32-bit forward frames; they are
used by IEC 62386-105 to transfer firmware to a bus unit.  Unlike the
16-bit frames of part 102 and the 24-bit frames of part 103, a 32-bit
frame is addressed to a bus unit without distinguishing between
control gear and control devices, so the addresses in this module come
from the dali.address.FirmwareAddress family.

There are two frame layouts:

 * addressed commands, laid out as

       address  0xfb  opcode  0x00

   where the address byte is one of dali.address.FirmwareBroadcast,
   FirmwareBroadcastUnaddressed or FirmwareShort;

 * special commands, which have a fixed address byte identifying the
   command and carry 24 bits of payload in the remaining three bytes.
   BeginBlock and TransferBlockData use this layout.

The opcodes, the 0xfb marker byte and the address encodings here are
taken from Tridonic's DALI USB sources (d2cmddef.py and
DaliMouse.Dali32Cmd), which is also where the names come from.  Two
properties of these commands are *not* recorded there and have been
inferred:

 * whether a command is sent twice.  Every command in this module has
   sendtwice = False, because Tridonic's sources always transmit
   through the single-shot Dali32Cmd() and never through
   Dali32DblCmd().  Check against IEC 62386-105 before relying on
   this.

 * how a query's answer should be interpreted.  The Response class
   attached to each query follows from its name; Response.raw_value
   always gives the unprocessed backward frame if the interpretation
   turns out to be wrong.  Check against IEC 62386-105 as well.
"""

from __future__ import annotations

from typing import Optional

from dali import address, command, frame


# Bits 23:16 of every addressed firmware transfer command
_MARKER_BYTE = 0xFB


def check_destination(
        destination: address.FirmwareAddress | int) -> address.FirmwareAddress:
    """Check that a valid firmware transfer destination was supplied

    Accepts a dali.address.FirmwareAddress, an object with an
    address_obj attribute, or an integer which is wrapped in a
    dali.address.FirmwareShort.  Returns the FirmwareAddress.
    """
    if hasattr(destination, 'address_obj'):
        destination = destination.address_obj
    if isinstance(destination, int):
        destination = address.FirmwareShort(destination)
    if isinstance(destination, address.FirmwareAddress):
        return destination
    raise ValueError('destination must be an integer or a '
                     'dali.address.FirmwareAddress object')


class _FirmwareCommand(command.Command):
    """A command for firmware transfer, in a 32-bit forward frame."""

    _framesize = 32
    _firmwarecommands: list[type[_FirmwareCommand]] = []

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        # Only the category classes dispatch; their own subclasses are
        # reached through the category's from_frame()
        if _FirmwareCommand in cls.__bases__:
            cls._firmwarecommands.append(cls)

    @classmethod
    def from_frame(cls, f: frame.ForwardFrame,
                   devicetype: Optional[int] = None,
                   dev_inst_map: Optional[command.DITM] = None
                   ) -> Optional[_FirmwareCommand]:
        for fc in cls._firmwarecommands:
            r = fc.from_frame(f)
            if r:
                return r
        return UnknownFirmwareCommand(f)

    _check_destination = staticmethod(check_destination)


class UnknownFirmwareCommand(_FirmwareCommand):
    """A 32-bit forward frame we do not recognise as a firmware command"""

    @classmethod
    def from_frame(cls, f: frame.ForwardFrame,
                   devicetype: Optional[int] = None,
                   dev_inst_map: Optional[command.DITM] = None
                   ) -> Optional[_FirmwareCommand]:
        return None


class _AddressedFirmwareCommand(_FirmwareCommand):
    """A firmware transfer command addressed to one or more bus units.

    The frame is "address 0xfb opcode 0x00".
    """

    _opcode: Optional[int] = None
    _opcodes: dict[int, type[_AddressedFirmwareCommand]] = {}

    def __init__(self, device: address.FirmwareAddress | int) -> None:
        if self._opcode is None:
            raise NotImplementedError

        self.destination = self._check_destination(device)

        f = frame.ForwardFrame(32, (_MARKER_BYTE << 16) | (self._opcode << 8))
        self.destination.add_to_frame(f)

        super().__init__(f)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls._opcode is not None:
            cls._opcodes[cls._opcode] = cls

    @classmethod
    def from_frame(cls, f: frame.ForwardFrame,
                   devicetype: Optional[int] = None,
                   dev_inst_map: Optional[command.DITM] = None
                   ) -> Optional[_FirmwareCommand]:
        if f[23:16] != _MARKER_BYTE or f[7:0] != 0x00:
            return None

        addr = address.from_frame(f)
        if not isinstance(addr, address.FirmwareAddress):
            return None

        cc = cls._opcodes.get(f[15:8])
        if not cc:
            return UnknownFirmwareCommand(f)

        return cc(addr)

    def __str__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, self.destination)


class _SpecialFirmwareCommand(_FirmwareCommand):
    """A firmware transfer command with a fixed address byte.

    The address byte identifies the command; the remaining 24 bits are
    payload.  These commands are not addressed to a particular bus
    unit.
    """

    _addrbyte: Optional[int] = None
    _addrbytes: dict[int, type[_SpecialFirmwareCommand]] = {}

    def __init__(self, data: int) -> None:
        if self._addrbyte is None:
            raise NotImplementedError
        if not isinstance(data, int):
            raise ValueError("data must be an integer")
        if data < 0 or data > 0xFFFFFF:
            raise ValueError("data must be in the range 0..0xffffff")

        self.data = data

        super().__init__(
            frame.ForwardFrame(32, (self._addrbyte << 24) | data))

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls._addrbyte is not None:
            cls._addrbytes[cls._addrbyte] = cls

    @classmethod
    def from_frame(cls, f: frame.ForwardFrame,
                   devicetype: Optional[int] = None,
                   dev_inst_map: Optional[command.DITM] = None
                   ) -> Optional[_FirmwareCommand]:
        cc = cls._addrbytes.get(f[31:24])
        if not cc:
            return None
        return cc(f[23:0])

    def __str__(self) -> str:
        return "%s(0x%06x)" % (self.__class__.__name__, self.data)


###############################################################################
# Addressed commands
###############################################################################


class StartFirmwareTransfer(_AddressedFirmwareCommand):
    _opcode = 0x00


class RestartFirmware(_AddressedFirmwareCommand):
    _opcode = 0x01


class EnableFirmwareRestart(_AddressedFirmwareCommand):
    _opcode = 0x02


class FinishFirmwareUpdate(_AddressedFirmwareCommand):
    _opcode = 0x03


class CancelFirmwareUpdate(_AddressedFirmwareCommand):
    _opcode = 0x04


class QueryFirmwareUpdateFeatures(_AddressedFirmwareCommand):
    _opcode = 0x05
    response = command.NumericResponse


class QueryFirmwareRestartEnabled(_AddressedFirmwareCommand):
    _opcode = 0x06
    response = command.YesNoResponse


class QueryFirmwareUpdateReceiverReady(_AddressedFirmwareCommand):
    _opcode = 0x07
    response = command.YesNoResponse


class QueryBlockFault(_AddressedFirmwareCommand):
    _opcode = 0x08
    response = command.YesNoResponse


class QueryFirmwareUpdateVersion(_AddressedFirmwareCommand):
    _opcode = 0x09
    response = command.NumericResponse


class QueryBlock0Accepted(_AddressedFirmwareCommand):
    _opcode = 0x0A
    response = command.YesNoResponse


###############################################################################
# Special commands
###############################################################################


class BeginBlock(_SpecialFirmwareCommand):
    """Announce the number of the block that is about to be transferred."""

    _addrbyte = 0xCB


class TransferBlockData(_SpecialFirmwareCommand):
    """Three bytes of firmware block payload."""

    _addrbyte = 0xBD
