"""Sequences for firmware transfer, built on the commands in dali.firmware.

These are command sequences in the sense of dali.sequences: generators
that yield commands and are sent the response to each one.  Pass them
to a driver's send() method.

A firmware transfer frame is addressed to control gear or to control
devices, chosen by bit 24 of the frame, so a destination here is one
of the dali.address.FirmwareAddress classes and says which of the two
it means: FirmwareGearShort(3) and FirmwareDeviceShort(3) are
different units.  See the addressing notes in dali.firmware.

One bus unit may contain both, though.  Part 105 section 4.2 says
that a bus unit may hold several logical units, that starting a
firmware update on it affects all of them, and that the part 105
variables are shared between them - so a product that presents both
control gear and a control device is updated once, through either
address space, not twice.

The *order* of the commands below - start, then a BeginBlock followed
by the block's data, check for a block fault, poll until the receiver
is ready again, finish, enable restart, restart - was originally
inferred from the command set and has since been reconciled with part
105 Ed.2:

 * Annex C recommends QUERY BLOCK INCOMPLETE OR FAULT after each
   complete data block, for blocks 1 and above, which is what
   _transfer_block() does;

 * section 11.4.3 describes polling QUERY FW UPDATE RECEIVER READY
   while the unit erases flash or writes firmware data, which is what
   _wait_until_ready() does;

 * Annex C notes that some units restart by themselves after FINISH
   FW UPDATE while others do not restart until RESTART FW, which is
   why restarting is a separate step here.

The block size is a property of the target product and comes from its
firmware update documentation; there is deliberately no default.

Note that this module does not build the part 105 Annex A update file
itself: FirmwareUpdate() transfers an image that is already in that
format, block 0 included, and does not compute the Annex B CRC16.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, NamedTuple, Optional

from dali import address
from dali.command import NumericResponse, Response
from dali.exceptions import DALISequenceError
from dali.firmware import (
    BeginBlock,
    CancelFirmwareUpdate,
    EnableRestart,
    FinishFirmwareUpdate,
    QueryBlock0Accepted,
    QueryBlockIncompleteOrFault,
    QueryFirmwareRestartEnabled,
    QueryFirmwareUpdateFeatures,
    QueryFirmwareUpdateReceiverReady,
    QueryFirmwareTransferVersion,
    RestartFirmware,
    StartFirmwareTransfer,
    TransferBlockData,
    check_destination,
)
from dali.sequences import DALISequence, progress, sleep

# Each TransferBlockData frame carries three bytes of payload
BYTES_PER_FRAME = 3


class FirmwareUpdateTarget(NamedTuple):
    """A bus unit that answered a firmware transfer query

    destination is the address the unit answered on, and says which of
    the two address spaces it is in; address is its short address, for
    convenience, and control_device says which space it was found in.
    Two targets may share a short address - control gear A3 and
    control device A3 - and still be different units.
    """
    destination: address.FirmwareAddress
    address: int
    control_device: bool
    features: int
    version: Optional[int]


def _query_value(response: Optional[Response[Any]]) -> Optional[int]:
    """The integer value of a numeric response, or None if there was none

    Reading .value raises when nothing answered, which is what a caller
    wants from a query whose answer it needs, and not what this wants:
    an unanswered query simply means the unit does not have the value.
    """
    if not isinstance(response, NumericResponse) or not response.valid:
        return None
    return response.value


def FindFirmwareUpdateTargets(
    addresses: Iterable[int] | None = None,
    *,
    control_gear: bool = True,
    control_devices: bool = True,
) -> DALISequence[list[FirmwareUpdateTarget]]:
    """Find the bus units that support firmware transfer

    Queries each short address in turn and returns a list of
    FirmwareUpdateTarget for those that answer.

    Both address spaces are scanned by default, because bit 24 of a
    firmware transfer frame selects between them and a bus unit
    discards a command whose bit 24 does not match its own type: one
    scan of the control gear space alone would miss every control
    device.  Pass control_gear=False or control_devices=False to scan
    only one of them, which halves the number of queries.

    A bus unit holding both control gear and a control device answers
    in both spaces and appears twice, once with control_device False
    and once with it True.  Those two entries are one product, and
    updating either of them updates all of it - see part 105 section
    4.2 - so do not transfer the image twice.
    """
    if addresses is None:
        addresses = range(64)
    spaces: list[Callable[[int], address.FirmwareAddress]] = []
    if control_gear:
        spaces.append(address.FirmwareGearShort)
    if control_devices:
        spaces.append(address.FirmwareDeviceShort)
    found = []
    for a in addresses:
        for cls in spaces:
            destination = cls(a)
            control_device = destination.is_control_device
            features = _query_value(
                (yield QueryFirmwareUpdateFeatures(destination)))
            if features is None:
                continue
            version = _query_value(
                (yield QueryFirmwareTransferVersion(destination)))
            found.append(FirmwareUpdateTarget(
                destination, a, control_device, features, version))
            kind = "control device" if control_device else "control gear"
            yield progress(
                message=f"Short address {a} ({kind}): firmware update "
                f"features {features:#04x}, version {version}")
    return found


def _wait_until_ready(
    destination: address.FirmwareAddress,
    interval: float,
    timeout: float,
) -> DALISequence[None]:
    """Poll the receiver until it is ready for more data

    The receiver is typically busy for a while after each block while
    it writes to flash.  A unit that has stopped answering altogether
    looks exactly like a unit that is still busy, so this is also what
    detects a target that has fallen off the bus.
    """
    waited = 0.0
    while True:
        r = yield QueryFirmwareUpdateReceiverReady(destination)
        assert isinstance(r, QueryFirmwareUpdateReceiverReady.response)
        if r.value:
            return
        if waited >= timeout:
            raise DALISequenceError(
                f"{destination} was not ready for the next block after "
                f"{timeout}s")
        yield sleep(interval)
        waited += interval


def _transfer_block(
    destination: address.FirmwareAddress,
    number: int,
    data: bytes,
    verify: bool,
) -> DALISequence[bool]:
    """Transfer one block; return True if it was accepted

    Returns False if the target reported a block fault, which the
    caller may retry.  A block 0 that is rejected outright is not
    retried: the target has decided the image is not for it.
    """
    yield BeginBlock(number)
    for i in range(0, len(data), BYTES_PER_FRAME):
        yield TransferBlockData(
            int.from_bytes(data[i:i + BYTES_PER_FRAME], "big"))

    if not verify:
        return True

    if number == 0:
        r = yield QueryBlock0Accepted(destination)
        assert isinstance(r, QueryBlock0Accepted.response)
        if not r.value:
            raise DALISequenceError(
                f"{destination} did not accept block 0; the image is "
                "probably not intended for this unit")

    # "No fault" is the absence of a backward frame, so this cannot tell
    # a healthy target from a silent one; _wait_until_ready() does that.
    r = yield QueryBlockIncompleteOrFault(destination)
    assert isinstance(r, QueryBlockIncompleteOrFault.response)
    return not r.value


def RestartFirmwareUpdateTarget(
    destination: address.FirmwareAddress,
    *,
    verify: bool = True,
) -> DALISequence[None]:
    """Restart a unit into its newly transferred firmware

    A restart has to be enabled before it is requested; the two
    commands are sent together here.
    """
    destination = check_destination(destination)
    yield EnableRestart(destination)
    if verify:
        r = yield QueryFirmwareRestartEnabled(destination)
        assert isinstance(r, QueryFirmwareRestartEnabled.response)
        if not r.value:
            raise DALISequenceError(
                f"{destination} did not report a restart as enabled")
    yield progress(message=f"Restarting {destination}")
    yield RestartFirmware(destination)


def FirmwareUpdate(
    destination: address.FirmwareAddress,
    image: bytes,
    *,
    block_size: int,
    padding: int = 0xFF,
    verify: bool | None = None,
    retries: int = 3,
    restart: bool = True,
    start_delay: float = 0.1,
    ready_poll_interval: float = 0.1,
    ready_poll_timeout: float = 10.0,
) -> DALISequence[int]:
    """Transfer a firmware image to one or more bus units

    Returns the number of blocks transferred.

    destination is a dali.address.FirmwareAddress, which says both
    which unit is meant and which address space it is in: a bare
    integer is not accepted, because a short address alone does not
    distinguish control gear A3 from control device A3.

    A FirmwareGearBroadcast or FirmwareDeviceBroadcast updates every
    unit in that address space at once, which is only sensible when
    they are all the same product: the queries that check progress
    cannot be used, because more than one unit would answer at the
    same time.  Note that the data transfer commands are not addressed
    at all, so the image reaches both address spaces whatever the
    destination; it is the commands around them that are addressed.

    image is the firmware image, and block_size is the number of bytes
    in a block.  Both come from the target product's firmware update
    documentation; there is deliberately no default block size.  The
    last block, and the last frame of a block, are filled out with the
    padding byte.

    verify controls whether the target is asked about each block.  The
    default is to verify when the destination is a single short
    address and not to verify otherwise, since only one unit can answer
    a query.  Without verification nothing detects a failed transfer.

    If restart is set, the unit is asked to restart into the new
    firmware once the transfer has finished.  It will stop responding
    for a while at that point.

    start_delay, ready_poll_interval and ready_poll_timeout are all in
    seconds: how long to wait after StartFirmwareTransfer, how often to
    ask whether the receiver is ready for the next block, and how long
    to keep asking before giving up.

    If anything goes wrong the update is cancelled on the way out, so
    that the target does not sit waiting for the rest of an image that
    is not coming.  Note that a driver runs the whole sequence as one
    transaction, so nothing else can use the bus until it finishes.
    """
    destination = check_destination(destination)
    if verify is None:
        verify = isinstance(
            destination,
            (address.FirmwareGearShort, address.FirmwareDeviceShort))
    if block_size < 1:
        raise ValueError("block_size must be at least one byte")
    if not 0 <= padding <= 0xFF:
        raise ValueError("padding must be a single byte")
    if not image:
        raise ValueError("image is empty")

    # Every block is sent as a whole number of three-byte frames.  If
    # block_size is not a multiple of three the extra bytes are padding
    # too; that is an assumption, since there is no way to send a
    # partial frame.
    frame_size = block_size + (-block_size % BYTES_PER_FRAME)
    blocks = [image[i:i + block_size].ljust(frame_size, bytes((padding,)))
              for i in range(0, len(image), block_size)]

    yield progress(
        message=f"Transferring {len(image)} bytes to {destination} as "
        f"{len(blocks)} blocks of {block_size} bytes"
        + ("" if verify else ", without verification"))

    try:
        if verify:
            features = _query_value(
                (yield QueryFirmwareUpdateFeatures(destination)))
            if features is None:
                raise DALISequenceError(
                    f"{destination} did not answer "
                    "QueryFirmwareUpdateFeatures; it may not support "
                    "firmware transfer")
            yield progress(
                message=f"{destination} firmware update features "
                f"{features:#04x}")

        yield StartFirmwareTransfer(destination)
        yield sleep(start_delay)

        for number, data in enumerate(blocks):
            yield progress(completed=number, size=len(blocks))
            for attempt in range(retries + 1):
                accepted = yield from _transfer_block(
                    destination, number, data, verify)
                if accepted:
                    break
                if attempt < retries:
                    yield progress(
                        message=f"Block {number} was faulty; retrying "
                        f"({attempt + 1}/{retries})")
            else:
                raise DALISequenceError(
                    f"Block {number} was still faulty after {retries} "
                    "retries")
            if verify:
                yield from _wait_until_ready(
                    destination, ready_poll_interval, ready_poll_timeout)

        yield progress(completed=len(blocks), size=len(blocks))
        yield FinishFirmwareUpdate(destination)
        yield progress(message="Firmware transfer finished")

        if restart:
            yield from RestartFirmwareUpdateTarget(
                destination, verify=verify)
    except Exception:
        # GeneratorExit is not an Exception, so a caller that closes
        # this sequence does not end up here: yielding during a close
        # would be an error.
        yield progress(message="Cancelling the firmware update")
        yield CancelFirmwareUpdate(destination)
        raise

    return len(blocks)
