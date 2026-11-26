"""Commands for firmware transfer, carried in 32-bit forward frames.

Firmware transfer is specified in IEC 62386-105, which this module
implements against the Ed.2 FDIS (2024).  It uses the 32-bit forward
frame of IEC 62386-101:2022 section 7.4.3, rather than the 16-bit
frames of part 102 or the 24-bit frames of part 103.

There are two frame layouts, both given in part 105 Table 1:

 * standard commands, laid out as

       address  0xfb  opcode  0x00

   where the address byte is one of the dali.address.FirmwareAddress
   family.  These are the commands of Table 6;

 * data transfer commands, which use the address byte to identify
   themselves - 0xcb for BeginBlock and 0xbd for TransferBlockData -
   and carry 24 bits of payload in the remaining three bytes.  These
   are the commands of Table 7, and they are not addressed to a
   particular bus unit.

Addressing
----------

Part 105 Table 1 encodes the address byte, in bits 31 down to 24, as:

    addressing method       bits 31..24   dali.address classes
    ----------------------  ------------  --------------------
    short addressing        0AAAAAAx      Firmware{Gear,Device}Short
    broadcast unaddressed   1111110x      Firmware{Gear,Device}-
                                            BroadcastUnaddressed
    broadcast               1111111x      Firmware{Gear,Device}Broadcast

All other address byte values are reserved, apart from the two data
transfer commands above.  There is no group addressing.

Bit 24, shown as "x", selects the address space: 0 is control gear
and 1 is control devices.  Section 9.2 requires a bus unit to discard
a short, broadcast or broadcast-unaddressed command whose bit 24 does
not match its own type, so firmware transfer is addressed to control
gear or to control devices in just the same way as the 16-bit and
24-bit frames are - hence the separate FirmwareGear* and
FirmwareDevice* address classes.

Two consequences are worth stating, because they are easy to get
wrong:

 * A firmware transfer short address is not a separate address space.
   Nothing in the part 105 command set assigns, programs or queries
   one: there is no counterpart to the part 102 SetShortAddress and
   QueryShortAddress, or to their part 103 equivalents.  A bus unit
   has a firmware transfer short address only because it already has
   a short address, from part 102 commissioning if it is control gear
   or part 103 commissioning if it is a control device.
   FirmwareGearShort(3) is the unit GearShort(3) addresses, and
   FirmwareDeviceShort(3) is the unit DeviceShort(3) addresses.

 * Those two units are not the same unit, because the two short
   address spaces are separate - but they may well be the same *bus
   unit*.  Section 4.2 says that a bus unit may contain several
   logical units, that starting a firmware update on a bus unit
   affects all of them, and that the part 105 variables of Table 5
   are shared between them.  So a product that presents both control
   gear and a control device is updated once, through either address
   space, not twice.

Naming
------

Each class is named after the command it sends, with the standard's
abbreviations spelled out: QUERY FW TRANSFER VERSION becomes
QueryFirmwareTransferVersion.  The command each one sends is named in
its docstring, along with the section of part 105 that defines it.

No command in Table 6 or Table 7 is marked "send twice", so every
command in this module has sendtwice = False.
"""

from __future__ import annotations

from typing import Optional

from dali import address, command, frame


# Bits 23:16 of every addressed firmware transfer command
_MARKER_BYTE = 0xFB


def check_destination(
        destination: address.FirmwareAddress) -> address.FirmwareAddress:
    """Check that a valid firmware transfer destination was supplied

    Accepts a dali.address.FirmwareAddress, or an object with an
    address_obj attribute that is one.  Returns the FirmwareAddress.

    A bare integer is deliberately not accepted.  Bit 24 of the frame
    selects the control gear or control device address space, so a
    short address on its own does not say which unit is meant; the
    caller has to choose FirmwareGearShort or FirmwareDeviceShort.
    """
    if hasattr(destination, 'address_obj'):
        destination = destination.address_obj
    if isinstance(destination, address.FirmwareAddress):
        return destination
    if isinstance(destination, int):
        raise ValueError(
            'destination must say which address space it is in: use '
            'dali.address.FirmwareGearShort or FirmwareDeviceShort '
            'rather than a bare integer')
    raise ValueError('destination must be a '
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
    """A standard firmware transfer command, from part 105 Table 6.

    The frame is "address 0xfb opcode 0x00", where the address byte
    selects one or more bus units in one of the two address spaces.
    """

    _opcode: Optional[int] = None
    _opcodes: dict[int, type[_AddressedFirmwareCommand]] = {}

    def __init__(self, device: address.FirmwareAddress) -> None:
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
    """A data transfer command, from part 105 Table 7.

    The address byte identifies the command - 0xcb or 0xbd - and the
    remaining 24 bits are payload.  These commands are not addressed
    to a particular bus unit, and so reach both address spaces: every
    bus unit with the firmware update process enabled receives them.
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
# Standard commands (part 105 Table 6)
###############################################################################


class StartFirmwareTransfer(_AddressedFirmwareCommand):
    """START FW TRANSFER - enable the firmware update process

    Part 105 section 11.3.2.  Discarded if the update process is
    already enabled, and discarded by a bus unit whose integrated bus
    power supply is enabled when bit 1 of its firmware update features
    is set.  Several bus units may be started at once, to update more
    than one at a time (9.7.1).
    """

    _opcode = 0x00


class RestartFirmware(_AddressedFirmwareCommand):
    """RESTART FW - restart into the transferred firmware

    Part 105 section 11.3.3.  Some bus units restart by themselves
    after FINISH FW UPDATE; others do not restart until this command.
    """

    _opcode = 0x01


class EnableRestart(_AddressedFirmwareCommand):
    """ENABLE RESTART - permit a subsequent RESTART FW

    Part 105 section 11.3.4.
    """

    _opcode = 0x02


class FinishFirmwareUpdate(_AddressedFirmwareCommand):
    """FINISH FW UPDATE - end the firmware update process

    Part 105 section 11.3.5.
    """

    _opcode = 0x03


class CancelFirmwareUpdate(_AddressedFirmwareCommand):
    """CANCEL FW UPDATE - abandon the firmware update process

    Part 105 sections 9.7.2.3 and 11.3.6.
    """

    _opcode = 0x04


class QueryFirmwareUpdateFeatures(_AddressedFirmwareCommand):
    """QUERY FW UPDATE FEATURES - the unit's firmware update features

    Part 105 sections 9.6 and 11.4.1.  A bit map; bit 1 reports an
    integrated bus power supply that is disabled during the update, in
    which case the updating tool has to supply bus power itself.
    """

    _opcode = 0x05
    response = command.NumericResponse


class QueryFirmwareRestartEnabled(_AddressedFirmwareCommand):
    """QUERY FW RESTART ENABLED - has a restart been enabled?

    Part 105 section 11.4.2.
    """

    _opcode = 0x06
    response = command.YesNoResponse


class QueryFirmwareUpdateReceiverReady(_AddressedFirmwareCommand):
    """QUERY FW UPDATE RECEIVER READY - ready for the next block?

    Part 105 section 11.4.3.  A bus unit may need time to erase flash
    or write firmware data after each complete block; this is how a
    tool tells when it may continue.
    """

    _opcode = 0x07
    response = command.YesNoResponse


class QueryBlockIncompleteOrFault(_AddressedFirmwareCommand):
    """QUERY BLOCK INCOMPLETE OR FAULT - was the last block good?

    Part 105 section 11.4.4.  Answers "NO" - that is, does not answer
    at all - when the block is complete and sound.  Otherwise it
    answers YES if every logical unit's short address is MASK, and
    otherwise the short address of the first addressed logical unit,
    as "0AAAAAA1".

    YesNoResponse reads any answer as True, which is the right
    reading: all of those answers mean the block was incomplete or
    faulty.  Response.raw_value gives the backward frame if the
    answering short address is wanted.

    Note that an answer does not necessarily indicate a fault: it
    also indicates that a block transfer is incomplete, so send it at
    the end of each complete block transfer, for blocks 1 and above.
    """

    _opcode = 0x08
    response = command.YesNoResponse


class QueryFirmwareTransferVersion(_AddressedFirmwareCommand):
    """QUERY FW TRANSFER VERSION - the block data format version

    Part 105 sections 9.7.4 and 11.4.5.  The answer is 1 for this
    edition of the standard; it will increase if the block data format
    changes.
    """

    _opcode = 0x09
    response = command.NumericResponse


class QueryBlock0Accepted(_AddressedFirmwareCommand):
    """QUERY BLOCK 0 ACCEPTED - was the information block accepted?

    Part 105 sections 9.7.2.1 and 11.4.6.  YES means block 0 was
    accepted and the unit is ready for further block data.  A busy
    unit - erasing flash, for instance - may not answer at all even
    though block 0 was accepted.
    """

    _opcode = 0x0A
    response = command.YesNoResponse


###############################################################################
# Data transfer commands (part 105 Table 7)
###############################################################################


class BeginBlock(_SpecialFirmwareCommand):
    """BEGIN BLOCK (data h, data m, data l) - start a numbered block

    Part 105 sections 9.7.2 and 11.5.2.  The 24-bit payload is the
    block number, which must be 0, the current block, or the current
    block plus one.
    """

    _addrbyte = 0xCB


class TransferBlockData(_SpecialFirmwareCommand):
    """TRANSFER BLOCK DATA (data h, data m, data l) - three payload bytes

    Part 105 sections 9.7.2 and 11.5.3.
    """

    _addrbyte = 0xBD
