"""Sequences for firmware transfer, built on the commands in dali.firmware.

These are command sequences in the sense of dali.sequences: generators
that yield commands and are sent the response to each one.  Pass them
to a driver's send() method.

A 32-bit firmware transfer frame is addressed to a bus unit without
saying whether that unit is control gear or a control device, so one
sequence covers both.  Beware that this means a short address on its
own is ambiguous if a control gear and a control device on the same
bus have the same short address: control gear A3 and control device
A3 are different units, but dali.address.FirmwareShort(3) is the only
way either of them can be addressed here.  Tridonic's sources always
encode the short address as "address << 1" with the low bit of the
address byte clear, and never use it to select between gear and
devices; whether IEC 62386-105 gives that bit (or another one) a
meaning is not something this library knows.  If it matters for your
bus, update one unit at a time and confirm you reached the one you
meant with QueryFirmwareUpdateVersion before and after.

The *order* of the commands below - start, then a BeginBlock followed
by the block's data, check for a block fault, poll until the receiver
is ready again, finish, enable restart, restart - follows from the
command set, not from a copy of the standard.  Tridonic's DALI USB
sources define the commands but do not contain an update procedure.
Check the sequence against IEC 62386-105 and against the firmware
update documentation for your product before using it to write
firmware to real hardware.  In particular the block size is a property
of the target, and there is no default here for that reason.
"""

from __future__ import annotations

from typing import Any, Iterable, NamedTuple, Optional

from dali import address
from dali.command import NumericResponse, Response
from dali.exceptions import DALISequenceError
from dali.firmware import (
    BeginBlock,
    CancelFirmwareUpdate,
    EnableFirmwareRestart,
    FinishFirmwareUpdate,
    QueryBlock0Accepted,
    QueryBlockFault,
    QueryFirmwareRestartEnabled,
    QueryFirmwareUpdateFeatures,
    QueryFirmwareUpdateReceiverReady,
    QueryFirmwareUpdateVersion,
    RestartFirmware,
    StartFirmwareTransfer,
    TransferBlockData,
    check_destination,
)
from dali.sequences import DALISequence, progress, sleep

# Each TransferBlockData frame carries three bytes of payload
BYTES_PER_FRAME = 3


class FirmwareUpdateTarget(NamedTuple):
    """A bus unit that answered a firmware transfer query"""
    address: int
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
) -> DALISequence[list[FirmwareUpdateTarget]]:
    """Find the bus units that support firmware transfer

    Queries each short address in turn and returns a list of
    FirmwareUpdateTarget for those that answer.  Both control gear and
    control devices are found, because a firmware transfer frame does
    not distinguish between them.
    """
    if addresses is None:
        addresses = range(64)
    found = []
    for a in addresses:
        destination = address.FirmwareShort(a)
        features = _query_value(
            (yield QueryFirmwareUpdateFeatures(destination)))
        if features is None:
            continue
        version = _query_value(
            (yield QueryFirmwareUpdateVersion(destination)))
        found.append(FirmwareUpdateTarget(a, features, version))
        yield progress(
            message=f"Short address {a}: firmware update features "
            f"{features:#04x}, version {version}")
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
    r = yield QueryBlockFault(destination)
    assert isinstance(r, QueryBlockFault.response)
    return not r.value


def RestartFirmwareUpdateTarget(
    destination: address.FirmwareAddress | int,
    *,
    verify: bool = True,
) -> DALISequence[None]:
    """Restart a unit into its newly transferred firmware

    A restart has to be enabled before it is requested; the two
    commands are sent together here.
    """
    destination = check_destination(destination)
    yield EnableFirmwareRestart(destination)
    if verify:
        r = yield QueryFirmwareRestartEnabled(destination)
        assert isinstance(r, QueryFirmwareRestartEnabled.response)
        if not r.value:
            raise DALISequenceError(
                f"{destination} did not report a restart as enabled")
    yield progress(message=f"Restarting {destination}")
    yield RestartFirmware(destination)


def FirmwareUpdate(
    destination: address.FirmwareAddress | int,
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

    destination is a dali.address.FirmwareAddress, or an integer which
    is taken as a short address.  A FirmwareBroadcast updates every
    unit on the bus at once, which is only sensible when they are all
    the same product: the queries that check progress cannot be used,
    because more than one unit would answer at the same time.

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
        verify = isinstance(destination, address.FirmwareShort)
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
