
"""
serial.py - Driver for serial-based DALI interfaces, including the
Lunatone RS232 LUBA and Lunatone SCI RS232 devices.


This file is part of python-dali.

python-dali is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import asyncio
import logging
import warnings
from enum import Enum
from functools import reduce
from operator import xor
from typing import Any, Callable, Generator, NamedTuple, Optional, Sequence, cast
from urllib.parse import ParseResult, urlparse, urlunparse

import serialx

import dali.gear
from dali import command, frame, gear, sequences
from dali.driver.trace_logging import get_logger
from dali.device.helpers import DeviceInstanceTypeMapper
from dali.exceptions import TransmissionError

_LOG = get_logger("dali.driver")

# Sentinel placed on the raw DALI response queue when the interface reports a
# framing error, so a waiting query returns an error response instead of
# silently timing out. Two control gear answering at once (a short-address
# collision) are the usual cause, and callers need to tell that apart from an
# address that simply did not answer.
_DALI_FRAMING_ERROR = object()


def _drain_queue(queue: asyncio.Queue[Any]) -> list[Any]:
    """Remove and return every currently-queued item without blocking."""
    items: list[Any] = []
    while True:
        try:
            items.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            return items


def _single_command_sequence(
    cmd: command.Command,
) -> Generator[command.Command, Optional[command.Response], Optional[command.Response]]:
    """Wrap a single command as a trivial sequence that returns its response."""
    return (yield cmd)


class DistributorQueue(asyncio.Queue[Any]):
    def __init__(self, parent: Optional[DistributorQueue] = None, *, maxsize: int = 0) -> None:
        """
        A DistributorQueue provides a way of distributing some object to
        multiple waiting consumers. The base of a DistributorQueue structure
        is initialised without a parent, then as many child DistributorQueue
        instances as needed are created, passing in a reference to the one
        parent object. The child instance will register itself with the
        parent. Each time the `distribute()` method on the parent is called,
        it will add the given data to the internal queue of each child - in
        this way, the same data can be awaited in multiple places.

        Note that only one "level" of DistributorQueue objects is supported.

        Example:
        ```
        >>> dq_parent = DistributorQueue()
        >>> dq_child1 = DistributorQueue(dq_parent)
        >>> dq_child2 = DistributorQueue(dq_parent)

        >>> dq_parent.distribute("hello world")
        >>> dq_child1.get_nowait()
        'hello world'
        >>> dq_child2.get_nowait()
        'hello world'
        ```

        :param parent: An instance of a DistributorQueue to register with.
        Leave as None if this instance will be the parent.
        :param maxsize: Maximum queue size, passed though to asyncio.Queue
        object
        """
        super().__init__(maxsize=maxsize)
        self._handlers: dict[int, DistributorQueue] = {}
        self._parent = parent
        if self._parent is not None:
            self._parent.add_handler(self)

    @property
    def is_parent(self) -> bool:
        return self._parent is None

    def add_handler(self, handler: DistributorQueue) -> None:
        if self.is_parent:
            self._handlers[hash(handler)] = handler
        else:
            # Don't allow more than one layer of nesting, to avoid confusion
            raise RuntimeError(
                "Cannot add handler to DistributorQueue with a parent"
            )

    def del_handler(self, handler: DistributorQueue) -> None:
        self._handlers.pop(hash(handler), None)

    def distribute(self, item: Any) -> None:
        if self._parent is not None:
            self.put_nowait(item)
        for handler in self._handlers.values():
            handler.distribute(item)

    def __del__(self) -> None:
        if self._parent is not None:
            self._parent.del_handler(self)


class DriverSerialBase:
    uri_scheme = ""

    def __init__(
        self,
        uri: str | ParseResult,
        dev_inst_map: Optional[DeviceInstanceTypeMapper] = None,
    ):
        """
        Sets up everything necessary for the driver to be able to start,
        but doesn't actually create the connection yet - that must be done by
        awaiting the 'connect()' coroutine.

        :param uri: A urllib ParseResult, or a string, of the URI to be used
        in initialising the driver. Depending on the specific driver type
        this will probably include the path to the serial device,
        e.g. 'luba232:/dev/ttyUSB0'
        :param dev_inst_map: A DeviceInstanceTypeMapper object to use for
        storing information about DALI control device instances and their
        corresponding types. If not given, a new instance will be created.
        Can be accessed later through the 'dev_inst_map' attribute.
        """
        if self.__class__.__name__ == "DriverSerialBase":
            raise RuntimeError(
                "DriverSerialBase cannot be instantiated directly"
            )

        if isinstance(uri, str):
            uri = urlparse(uri)

        if uri.scheme != self.uri_scheme:
            raise TypeError(
                f"Cannot create a {self.__class__.__name__} "
                f"instance with a scheme of {uri.scheme}"
            )

        self.uri: ParseResult = uri
        self.dev_inst_map = (
            DeviceInstanceTypeMapper() if dev_inst_map is None else dev_inst_map
        )
        self._connected = asyncio.Event()
        # Assigned by the subclass once the asyncio transport protocol exists
        self._protocol: Any = None
        self.transaction_lock = asyncio.Lock()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{urlunparse(self.uri)}")'

    def __hash__(self) -> int:
        return hash(self.uri)

    async def connect(self, *, scan_dev_inst: bool = False) -> None:
        """
        Perform the connection to the physical device. This may take some
        time, depending on how the hardware works.

        :param scan_dev_inst: Whether or not to scan the DALI bus for control
        devices, and update the mapping of addresses and instance numbers to
        instance type
        """
        raise NotImplementedError(
            "'connect()' needs to be implemented in a subclass"
        )

    @property
    def is_connected(self) -> bool:
        """
        Flags whether the underlying transport is connected and ready for use

        The serial device can disappear at any time, e.g. a USB interface
        being unplugged. The driver's own event only records that the
        handshake completed once, so for drivers backed by an asyncio
        transport the protocol, which is told about the loss through
        'connection_lost()', has the last word.

        :return: Boolean, true if connection is ready
        """
        if not self._connected.is_set():
            return False
        if self._protocol is None:
            return True
        return bool(self._protocol.connected.is_set())

    async def wait_connected(self) -> None:
        """
        Blocks until the underlying transport is connected and ready for use

        :return: None
        """
        await self._connected.wait()

    async def _send_frame(
        self, cmd: command.Command, *, priority: int = 1
    ) -> Optional[command.Response]:
        """
        Transmit a single DALI frame over the bus. If the command expects a
        response it is returned.

        This is the low-level, per-frame transmit used by `send()`. Callers
        should use `send()` instead, which runs commands and sequences as
        transactions and takes care of EnableDeviceType and priority.

        :param cmd: A Command object to transmit
        :param priority: IEC 62386-101 Table 22 transmit priority (1..5) for
        this frame. Drivers that cannot set a transmit priority ignore it.
        :return: Either None if no response is expected, or a Response object
        """
        raise NotImplementedError(
            "'_send_frame()' needs to be implemented in a subclass"
        )

    def new_dali_rx_queue(self) -> DistributorQueue:
        """
        Returns a DistributorQueue child object, which can then be used as a
        normal asyncio.Queue to be notified of processed DALI commands
        received from the underlying device.

        Each call creates a new DistributorQueue, of which each one will have
        a separate queue of received DALI messages.

        Note that this does not return any responses, e.g. an answer to a
        query - those are returned to the caller when using the `send()`
        method.

        Example:
        ```
        dali_rx_queue = driver.new_dali_rx_queue()
        dali_rx_cmd = await dali_rx.wait()
        ```

        :return: A new DistributorQueue child object, already linked to the
        necessary parent
        """
        raise NotImplementedError(
            "'new_dali_rx_queue()' needs to be implemented in a subclass"
        )

    async def send(
        self,
        msg: command.Command | Generator[Any, Any, Any],
        *,
        priority: int = 5,
        progress: Optional[Callable[[str | sequences.progress], None]] = None,
    ) -> Any:
        """
        Send a command or run a sequence as a single transaction.

        A bare Command is wrapped in a trivial sequence, so a single command
        and a multi-command sequence share the same execution path. The whole
        transaction is sent while holding the transaction lock, so it cannot be
        interrupted by another sender.

        The first forward frame of the transaction is sent at `priority`; all
        subsequent frames are sent at priority 1, forming an IEC 62386-101 §9.3
        transaction. When a command has a non-zero device type, an
        EnableDeviceType frame is transmitted immediately before it (taking the
        caller's priority, so the command itself follows at priority 1).

        :param msg: A Command to send, or a sequence generator to run. Sequences
        are available in various places in the python-dali library.
        :param priority: IEC 62386-101 Table 22 priority for the first frame, in
        the range 2..5 (see IEC 62386-103 §9.14 for how to choose it). A value
        outside this range raises ValueError.
        :param progress: A function to call with progress updates, used by some
        sequences to provide status information. The function must accept a
        single argument. A suitable example is `progress=print`.
        :return: The command response for a single command, otherwise the
        sequence's return value.
        """
        if priority not in (2, 3, 4, 5):
            raise ValueError(
                f"priority must be in the range 2..5, not {priority!r}"
            )

        seq = (
            _single_command_sequence(msg)
            if isinstance(msg, command.Command)
            else msg
        )

        async with self.transaction_lock:
            response = None
            next_priority = priority
            try:
                while True:
                    try:
                        # Note that 'send()' here refers to the Python
                        # 'generator' paradigm, not to the DALI driver!
                        cmd = seq.send(response)
                    except StopIteration as r:
                        return r.value
                    response = None
                    if isinstance(cmd, sequences.sleep):
                        await asyncio.sleep(cmd.delay)
                    elif isinstance(cmd, sequences.progress):
                        if progress:
                            progress(cmd)
                    else:
                        if cmd.devicetype != 0:
                            await self._send_frame(
                                gear.general.EnableDeviceType(cmd.devicetype),
                                priority=next_priority,
                            )
                            next_priority = 1
                        response = await self._send_frame(
                            cmd, priority=next_priority
                        )
                        next_priority = 1
            finally:
                seq.close()

    async def run_sequence(
        self,
        seq: Generator[
            command.Command,  # Sequences yield commands to send
            command.Response,  # Sequences get sent the response from the previous command
            Any,  # The return type depends specifically on the sequence
        ],
        progress: Optional[Callable[[str | sequences.progress], None]] = None,
    ) -> Any:
        """
        Deprecated alias for `send()`, which now accepts both commands and
        sequences. Kept for backwards compatibility.
        """
        warnings.warn(
            "run_sequence() is deprecated; use send() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.send(seq, progress=progress)


def drivers_map() -> dict[str, type[DriverSerialBase]]:
    """
    Return a dict that maps each known driver URI scheme to the relevant
    driver class. This can be used to initialise drivers based on a given
    URI, example:

    ```
    driver = drivers_map()["luba232"]
    ```
    """
    # TODO: this could be tracked in a metaclass, to avoid recreating each time
    return {
        driver.uri_scheme: driver
        for driver in DriverSerialBase.__subclasses__()
    }


class DriverLubaRs232(DriverSerialBase):
    uri_scheme = "luba232"
    timeout_rx = 0.025
    timeout_tx_confirm = 1.0  # TX might take some time if the bus is busy
    timeout_connect = 1.0
    timeout_bus_power = 5.0  # Time for the integrated PS to bring the bus up
    # The interface can be slow to acknowledge the initial handshake while the
    # bus is busy (e.g. an input device streaming events), so retry it a few
    # times rather than failing the whole connect on a single timeout.
    handshake_attempts = 5

    # Lunatone article numbers this driver has been tested against.
    TESTED_ARTICLE_NUMBERS = frozenset({24166096, 24138246})

    class LubaCmd(Enum):
        """
        All supported LUBA command codes. Refer §2 of Lunatone's
        documentation on LUBA:
        https://www.lunatone.com/wp-content/uploads/2021/04/LUBA_Protocol_EN.pdf
        """

        READ_WRITE_SETTINGS_CMD = 0x2A
        READ_WRITE_SETTINGS_RSP = 0x2B
        READ_STATUS_CMD = 0x2C
        READ_STATUS_RSP = 0x2D
        QUERY_DEVICE_INFO_CMD = 0x20
        QUERY_DEVICE_INFO_RSP = 0x21
        QUERY_DEVICE_DESCRIPTOR_CMD = 0x28
        QUERY_DEVICE_DESCRIPTOR_RSP = 0x29
        EVENT_MESSAGE = 0x31
        ADD_DALI_FRAME_TO_TX_CMD = 0x32
        ADD_DALI_FRAME_TO_TX_RSP = 0x33
        ADD_16DALI_FRAME_TO_TX_CMD = 0x34
        ADD_16DALI_FRAME_TO_TX_RSP = 0x35
        ADD_24DALI_FRAME_TO_TX_CMD = 0x36
        ADD_24DALI_FRAME_TO_TX_RSP = 0x37

    class LubaTxError(Enum):
        """Reason codes reported when the interface rejects a DALI frame.

        Refer §2.1.1 "ADD DALI FRAME TO TX BUFFER" of Lunatone's LUBA
        documentation.
        """

        BUS_VOLTAGE_ERROR = 1
        DALI_INITIALIZE_MODE = 2
        DALI_QUIESCENT_MODE = 3
        SEND_BUFFER_FULL = 4
        LINE_NOT_AVAILABLE = 5
        SYNTAX_ERROR = 6
        MACRO_RUNNING = 7

    class LubaDeviceInfo(NamedTuple):
        """
        Named tuple for storing a set of information about the LUBA device
        """

        gtin: int
        id: int
        pcb_ver: int
        assembly_ver: int
        article_num: int

    class LubaDeviceSettings(NamedTuple):
        """
        Named tuple for storing a set of information about the LUBA device
        """

        mode: int
        event_filter: int

    class LubaDeviceDescriptor(NamedTuple):
        """
        Named tuple describing the functionality of the LUBA interface, as
        returned by the "QUERY DEVICE DESCRIPTOR" command
        """

        # HardwareFeature bit 7: device has an integrated, switchable bus
        # power supply
        has_bus_power_supply: bool

    class LubaLineStatus(NamedTuple):
        """
        Named tuple for the status of a DALI line, as returned by the
        "READ STATUS" command
        """

        # Status bit 7: a bus voltage error is present (i.e. the bus is not
        # powered)
        bus_voltage_error: bool

    class LubaProtocol(asyncio.Protocol):
        """
        This class is internally used by DriverLubaRs232 to implement a state
        machine for decoding the incoming serial bytes into LUBA messages,
        which in turn wrap DALI frames. The class also handles encoding DALI
        frames into LUBA messages, setting the appropriate flags etc.
        """

        MAX_LEN = 24
        EVENT_TYPE_MASK = 0b11000000
        EVENT_INFO_MASK = 0b00111111

        class ReadState(Enum):
            """
            Enum of states used in the receiver state machine
            """

            WAIT_START = 1
            WAIT_COMMAND = 2
            WAIT_LENGTH = 3
            LOOP_READ = 4
            WAIT_CHECKSUM = 5

        class LubaMsgTxConf(NamedTuple):
            """
            Named tuple used to enqueue messages along with their transmit ID
            """

            tx_id: int
            message: Optional[command.Command] = None
            error_code: Optional[int] = None

        def __init__(self) -> None:
            super().__init__()
            self.transport: Optional[serialx.SerialTransport] = None

            self._queue_rx_dali = DistributorQueue()
            self._queue_rx_raw_dali: asyncio.Queue[Any] = asyncio.Queue()
            self._queue_rx_luba_cmd: asyncio.Queue[Any] = asyncio.Queue()
            self._queue_tx_conf: asyncio.Queue[Any] = asyncio.Queue()
            self._prev_rx_enable_dt = 0
            self._prev_tx_enable_dt = 0
            self._tx_lock = asyncio.Lock()
            self._rx_state = self.ReadState.WAIT_START
            self.rx_idle = asyncio.Event()
            self._buffer: list[int] = []
            self._rx_expected_len: Optional[int] = None
            self._rx_received_len: int = 0
            self._connected = asyncio.Event()
            self._dev_info: Optional[DriverLubaRs232.LubaDeviceInfo] = None
            self._dev_inst_map: Optional[DeviceInstanceTypeMapper] = None
            # Whether to switch on the interface's integrated bus power supply
            self.bus_power = False

            self.reset()

        @property
        def _tx(self) -> serialx.SerialTransport:
            """The connected serial transport, or raise if not connected."""
            if self.transport is None:
                raise IOError("serial transport not connected")
            return self.transport

        @property
        def rx_state(self) -> ReadState:
            assert self._rx_state is not None
            return self._rx_state

        @rx_state.setter
        def rx_state(self, state: ReadState) -> None:
            if not isinstance(state, self.ReadState):
                raise TypeError(
                    f"rx_state must be a ReadState enum, not {type(state)}"
                )

            self._rx_state = state
            if state == self.ReadState.WAIT_START:
                self.rx_idle.set()
            else:
                self.rx_idle.clear()

        @property
        def dev_inst_map(self) -> Optional[DeviceInstanceTypeMapper]:
            return self._dev_inst_map

        @dev_inst_map.setter
        def dev_inst_map(self, value: DeviceInstanceTypeMapper) -> None:
            self._dev_inst_map = value

        @property
        def queue_rx_dali(self) -> DistributorQueue:
            return self._queue_rx_dali

        def reset(self) -> None:
            """
            Returns the state machine to "WAIT_START"
            """
            self.rx_state = self.ReadState.WAIT_START
            self._buffer = [0] * self.MAX_LEN
            self._rx_expected_len = None
            self._rx_received_len = 0

        async def wait_dali_raw_response(self) -> int:
            """
            Async method which waits for a raw (i.e. un-decoded) DALI frame
            to be received from the LUBA device.

            :return: A received DALI frame, as an int
            """
            return cast(int, await self._queue_rx_raw_dali.get())

        def reset_dali_response(self) -> None:
            """Drop any DALI responses left buffered from a previous exchange.

            A backward frame that arrives after its query's receive timeout has
            no matching request, so it is cleared before the next transaction.
            On a busy bus this is routine housekeeping, hence debug level.
            """
            discarded = _drain_queue(self._queue_rx_raw_dali)
            if discarded:
                _LOG.debug(
                    "LUBA RX DALI queue: discarded %d stale response(s): %s",
                    len(discarded),
                    discarded,
                )

        def reset_luba_response(self) -> None:
            """Drop any LUBA command replies left buffered from a prior attempt.

            A reply that arrives after its command's confirm timeout would
            otherwise be mistaken for the next command's reply, so it is cleared
            before a handshake is retried.
            """
            _drain_queue(self._queue_rx_luba_cmd)

        @staticmethod
        def _insert_checksum(in_ints: list[int]) -> None:
            in_ints[-1] = reduce(xor, in_ints[1:-1])

        async def send_dali_command(
            self, tx: command.Command, priority: int = 1
        ) -> int:
            """
            Sends a variable length DALI command (16 or 24 bits), waiting
            until the LUBA device confirms it has sent the message before
            returning the frame ID.

            :param tx: A single DALI command to send
            :param priority: IEC 62386-101 Table 22 transmit priority (1..5)
            """
            # Make sure the serial interface is not in the process of reading
            # data before we send
            await self.rx_idle.wait()

            dali_ints = list(tx.frame.as_byte_sequence)
            if not len(dali_ints) in (2, 3):
                raise ValueError(
                    f"Only works with 16 or 24 bit messages, not {8*len(dali_ints)}"
                )
            luba_mode = priority  # IEC 62386-101 Table 22 priority (1..5)
            luba_mode |= 0b10000000 if tx.sendtwice else 0  # "Send Twice" flag
            tx_ints = [
                0x59,  # ASCII 'Y'
                DriverLubaRs232.LubaCmd.ADD_DALI_FRAME_TO_TX_CMD.value,  # LUBA Command
                7,  # Length
                0,  # DALI bus selector (RS232 device only has one bus)
                8 * len(dali_ints),  # No. of bits in DALI frame
                luba_mode,
                dali_ints[0],  # Data, big-endian
                dali_ints[1],  # Data, big-endian
                0 if len(dali_ints) == 2 else dali_ints[2],  # Data, big-endian
                0,  # Pad out to four bytes, to fit LUBA frame
                0,  # Checksum
            ]
            # Fill in the checksum
            self._insert_checksum(tx_ints)

            # Use a mutex to ensure only one message is sent at a time,
            # waiting for the LUBA device to confirm before sending another
            async with self._tx_lock:
                _LOG.debug(f"DALI sending message: {tx}")
                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                # Wait for the LUBA device to respond, considering whether the
                # message is sent twice or not
                confirm_count = 2 if tx.sendtwice else 1
                while confirm_count > 0:
                    confirm = await asyncio.wait_for(
                        self._queue_tx_conf.get(),
                        timeout=DriverLubaRs232.timeout_tx_confirm,
                    )
                    if confirm.error_code is not None:
                        raise TransmissionError(confirm.error_code)
                    if hasattr(confirm.message, "frame"):
                        if confirm.message.frame == tx.frame:
                            _LOG.trace(
                                f"LUBA device reports message '{tx}' sent, "
                                f"with ID {confirm.tx_id}"
                            )
                        else:
                            _LOG.error(
                                "Expected LUBA device to confirm transmission "
                                f"of message '{tx}', but got a confirmation "
                                f"for '{confirm.message}'"
                            )
                    else:
                        _LOG.debug(
                            f"Unable to decode message id {confirm.tx_id}, but "
                            "LUBA device reports it was sent successfully"
                        )
                    confirm_count -= 1
            # Release the lock

            return cast(int, confirm.tx_id)

        async def send_device_info_query(self) -> None:
            """
            Query some basic information from the LUBA device
            """
            # Use a mutex to ensure only one message is sent at a time
            async with self._tx_lock:
                _LOG.debug("Querying LUBA device info")
                tx_ints = [
                    0x59,  # ASCII 'Y'
                    DriverLubaRs232.LubaCmd.QUERY_DEVICE_INFO_CMD.value,  # LUBA Command
                    1,  # Length
                    0,  # Request set "0" information
                    0,  # Checksum
                ]
                # Fill in the checksum
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                # Wait for the LUBA device to respond
                dev_info = await asyncio.wait_for(
                    self._queue_rx_luba_cmd.get(),
                    timeout=DriverLubaRs232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(dev_info, DriverLubaRs232.LubaDeviceInfo):
                _LOG.error(f"Expected a LubaDeviceInfo, but got: {dev_info}")
                return

        async def send_device_descriptor_query(
            self,
        ) -> Optional[DriverLubaRs232.LubaDeviceDescriptor]:
            """
            Query the LUBA device descriptor, describing which features (such
            as a switchable bus power supply) the interface supports
            """
            # Use a mutex to ensure only one message is sent at a time
            async with self._tx_lock:
                _LOG.debug("Querying LUBA device descriptor")
                tx_ints = [
                    0x59,  # ASCII 'Y'
                    DriverLubaRs232.LubaCmd.QUERY_DEVICE_DESCRIPTOR_CMD.value,
                    0,  # Length, this command carries no data
                    0,  # Checksum
                ]
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                descriptor = await asyncio.wait_for(
                    self._queue_rx_luba_cmd.get(),
                    timeout=DriverLubaRs232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(
                descriptor, DriverLubaRs232.LubaDeviceDescriptor
            ):
                _LOG.error(
                    f"Expected a LubaDeviceDescriptor, but got: {descriptor}"
                )
                return None
            return descriptor

        async def send_read_status(
            self,
        ) -> Optional[DriverLubaRs232.LubaLineStatus]:
            """
            Read the status of the (single) DALI line, which reports whether
            the bus is powered
            """
            # Use a mutex to ensure only one message is sent at a time
            async with self._tx_lock:
                _LOG.debug("Reading LUBA line status")
                tx_ints = [
                    0x59,  # ASCII 'Y'
                    DriverLubaRs232.LubaCmd.READ_STATUS_CMD.value,
                    1,  # Length
                    0,  # Line 0 (devices with a single DALI line)
                    0,  # Checksum
                ]
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                line_status = await asyncio.wait_for(
                    self._queue_rx_luba_cmd.get(),
                    timeout=DriverLubaRs232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(line_status, DriverLubaRs232.LubaLineStatus):
                _LOG.error(
                    f"Expected a LubaLineStatus, but got: {line_status}"
                )
                return None
            return line_status

        async def send_device_settings(self) -> None:
            """
            The implementation of the LUBA protocol assumes a certain
            configuration of the device, this method ensures this
            configuration is set up correctly
            """
            # Use a mutex to ensure only one message is sent at a time
            async with self._tx_lock:
                _LOG.debug("Sending LUBA device settings")
                mode_settings = 0b00000000
                # 7: 1 = activates the DALI ping
                # 6: 1 = Deactivates sending of DALI frames during "Initialize" mode
                # 5: 1 = Deactivates sending of DALI frames during "Quiescent" mode
                # 4..0: Reserved
                event_settings = 0b00010010
                # 7: 1 = deactivates all events
                # 6: 1 = deactivates events for successfully sending a DALI frame
                # 5: 1 = deactivates events for receiving a DALI frame
                # 4: 1 = deactivate events for the send-buffer (full/empty)
                # 3: 1 = deactivates including the tick in events
                # 2: 1 = deactivates including the line number in events
                # 1: 1 = Deactivates events for macros
                # 0: reserved
                hardware_settings = 0b10000000 if self.bus_power else 0b00000000
                # 7: 1 = turn on bus power supply
                # 6..0: Reserved
                tx_ints = [
                    0x59,  # ASCII 'Y'
                    DriverLubaRs232.LubaCmd.READ_WRITE_SETTINGS_CMD.value,  # LUBA Command
                    3,  # Length
                    mode_settings,
                    event_settings,
                    hardware_settings,
                    0,  # Checksum
                ]
                # Fill in the checksum
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                # Wait for the LUBA device to respond
                dev_settings = await asyncio.wait_for(
                    self._queue_rx_luba_cmd.get(),
                    timeout=DriverLubaRs232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(dev_settings, DriverLubaRs232.LubaDeviceSettings):
                _LOG.error(
                    f"Expected a LubaDeviceSettings, but got: {dev_settings}"
                )
                return
            if (
                dev_settings.mode != mode_settings
                or dev_settings.event_filter != event_settings
            ):
                msg = "Failed to set LUBA device settings!"
                _LOG.critical(msg)
                raise RuntimeError(msg)

            _LOG.trace("Successfully set LUBA device settings")

        def _process_byte(self, rx_int: int) -> None:
            if not isinstance(rx_int, int):
                raise TypeError(
                    f"Got an item of type: {type(rx_int)}, expected an integer"
                )

            # Handle each state of the state machine
            if self._rx_state == self.ReadState.WAIT_START:
                # In the 'WAIT_START' state we expect an ASCII 'Y', or hex 0x59
                self._buffer[0] = rx_int
                if rx_int == 0x59:
                    _LOG.trace("LUBA message start")
                    self._rx_state = self.ReadState.WAIT_COMMAND
                else:
                    _LOG.debug(f"LUBA invalid start pattern: 0x{rx_int:02x}")
                return

            elif self._rx_state == self.ReadState.WAIT_COMMAND:
                # In the 'WAIT_COMMAND' state the next byte will be the LUBA
                # command code
                self._buffer[1] = rx_int
                try:
                    rx_cmd = DriverLubaRs232.LubaCmd(self._buffer[1])
                    _LOG.trace(f"LUBA command number: {rx_cmd}")
                except ValueError:
                    _LOG.warning(
                        f"LUBA command number not understood: 0x{rx_int:02x}"
                    )
                self._rx_state = self.ReadState.WAIT_LENGTH
                return

            elif self._rx_state == self.ReadState.WAIT_LENGTH:
                # In the 'WAIT_LENGTH' state the next byte will be the length
                self._buffer[2] = rx_int
                if 0 < rx_int < self.MAX_LEN:
                    _LOG.trace(f"LUBA payload length: {rx_int}")
                    self._rx_expected_len = rx_int
                    self._rx_state = self.ReadState.LOOP_READ
                else:
                    _LOG.warning(f"LUBA payload length of {rx_int} is invalid!")
                    self.reset()
                return

            elif self._rx_state == self.ReadState.LOOP_READ:
                # Read bytes, up to the maximum expected length
                self._rx_received_len += 1
                self._buffer[2 + self._rx_received_len] = rx_int

                # Once all payload bytes are read, the final byte will be the
                # checksum
                if self._rx_received_len == self._rx_expected_len:
                    self._rx_state = self.ReadState.WAIT_CHECKSUM
                return

            elif self._rx_state == self.ReadState.WAIT_CHECKSUM:
                # In the 'WAIT_CHECKSUM' state, the next byte will be the
                # checksum
                self._buffer[self._rx_received_len + 3] = rx_int

                # We now have a full frame
                received_data = tuple(
                    self._buffer[0 : self._rx_received_len + 4]
                )
                _LOG.trace(
                    f"Raw data: {[f'0x{data:02x}' for data in received_data]}"
                )

                # Validate the checksum: XOR all values, excluding the
                # synchronisation and checksum
                check = reduce(xor, received_data[1:-1])

                if check != rx_int:
                    _LOG.warning(
                        f"LUBA checksum failure! Calculated: {check}, "
                        f"Expected: {rx_int}"
                    )
                    _LOG.trace(received_data)
                    self.reset()
                    return
                else:
                    _LOG.trace("LUBA checksum passed, full frame received")
                    try:
                        rx_cmd = DriverLubaRs232.LubaCmd(self._buffer[1])
                    except ValueError:
                        _LOG.exception(
                            f"LUBA unknown message type: 0x{self._buffer[1]:02x},"
                            f" data: {received_data}"
                        )
                        self.reset()
                        return

                    if rx_cmd == DriverLubaRs232.LubaCmd.EVENT_MESSAGE:
                        self._process_luba_event(received_data)
                    elif (
                        rx_cmd
                        == DriverLubaRs232.LubaCmd.ADD_DALI_FRAME_TO_TX_RSP
                    ):
                        self._process_luba_response_dali_frame_to_tx(
                            received_data
                        )
                    elif (
                        rx_cmd == DriverLubaRs232.LubaCmd.QUERY_DEVICE_INFO_RSP
                    ):
                        self._process_luba_response_device_info(received_data)
                    elif (
                        rx_cmd
                        == DriverLubaRs232.LubaCmd.QUERY_DEVICE_DESCRIPTOR_RSP
                    ):
                        self._process_luba_response_device_descriptor(
                            received_data
                        )
                    elif rx_cmd == DriverLubaRs232.LubaCmd.READ_STATUS_RSP:
                        self._process_luba_response_status(received_data)
                    elif (
                        rx_cmd
                        == DriverLubaRs232.LubaCmd.READ_WRITE_SETTINGS_RSP
                    ):
                        self._process_luba_response_settings(received_data)
                    else:
                        _LOG.error(
                            f"LUBA unexpected message, type 0x{self._buffer[1]:02x},"
                            f" data: {received_data}"
                        )

                    self.reset()
                    return
            else:
                raise RuntimeError(f"Invalid state: {self._rx_state}")

        def _process_luba_event(self, received_data: Sequence[int]) -> None:
            """
            Handle a LUBA 'event' message, typically these are received when
            a DALI frame was observed on the bus by the LUBA device
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.EVENT_MESSAGE
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x31"
                )

            payload = received_data[3:-1]

            # Bytes 0-1 of payload are the 'time tick'
            time_tick = int.from_bytes(bytes(payload[0:2]), byteorder="big")
            _LOG.trace(f"LUBA Event Time tick: {time_tick}")
            # Byte 2 of payload is the 'DALI line'
            _LOG.trace(f"LUBA Event DALI line: {payload[2]}")
            # Byte 3 of payload is the "Status", further broken down by bit
            # fields
            status_int = payload[3]
            event_type = (status_int & self.EVENT_TYPE_MASK) >> 6
            event_info = status_int & self.EVENT_INFO_MASK
            _LOG.trace(
                f"LUBA Event type: {event_type}, Event info: {event_info}"
            )

            # Event type 0: DALI frame was sent
            # Byte 4 is the transmitted frame ID
            # Bytes 5 onwards are the transmitted DALI frame
            if event_type == 0:
                tx_id = payload[4]
                tx_dali = payload[5:]
                # Decode the command, for logging and debugging
                try:
                    dali_command = command.Command.from_frame(
                        frame.ForwardFrame(bits=8 * len(tx_dali), data=tx_dali),
                        devicetype=self._prev_tx_enable_dt,
                        dev_inst_map=self._dev_inst_map,
                    )
                except Exception:
                    _LOG.debug(
                        "Failed to decode transmitted DALI frame "
                        f"{[f'0x{b:02x}' for b in tx_dali]} "
                        f"(devicetype {self._prev_tx_enable_dt})",
                        exc_info=True,
                    )
                    dali_command = None
                # Store the last seen Device Type command, there will likely
                # be a subsequent command that we transmit which relies on
                # this for decoding
                if isinstance(dali_command, dali.gear.general.EnableDeviceType):
                    self._prev_tx_enable_dt = dali_command.param
                else:
                    self._prev_tx_enable_dt = 0
                luba_tx_info = self.LubaMsgTxConf(
                    tx_id=tx_id, message=dali_command
                )
                _LOG.trace(
                    f"LUBA DALI frame {luba_tx_info.tx_id} "
                    f"transmitted: {luba_tx_info.message}"
                )
                self._queue_tx_conf.put_nowait(luba_tx_info)
            # Event type 2: DALI frame was received
            # Bytes 4 onwards are the received DALI frame
            if event_type == 2:
                # If 'Event Info' == 1-32: number of bits in frame
                if 1 <= event_info <= 32:
                    _LOG.trace(f"LUBA DALI frame length: {event_info}")
                # 'Event Info' == 62: received only start / stop bit combination
                elif event_info == 62:
                    _LOG.error(
                        "LUBA DALI frame error: received only start/stop bit"
                    )
                    return
                # 'Event Info' == 63: framing error
                elif event_info == 63:
                    _LOG.error("LUBA DALI frame error: framing error")
                    # Surface the error so a waiting query can distinguish a
                    # collision (several gear answering) from no answer at all.
                    self._queue_rx_raw_dali.put_nowait(_DALI_FRAMING_ERROR)
                    return
                else:
                    _LOG.critical(f"LUBA DALI unknown event info: {event_info}")
                    return

                rx_dali = payload[4:]
                _LOG.trace(
                    f"LUBA DALI frame received: {[f'0x{data:02x}' for data in rx_dali]}"
                )

                if len(rx_dali) == 0:
                    _LOG.error("LUBA DALI frame error, zero length!")
                elif len(rx_dali) == 1:
                    # An 8-bit frame is a response, don't try to decipher it
                    # here because it depends on context which the 'send()'
                    # routine will have to handle
                    _LOG.trace(
                        f"Adding raw DALI response to queue: '{rx_dali[0]}'"
                    )
                    self._queue_rx_raw_dali.put_nowait(rx_dali[0])
                else:
                    # A 16 or 24-bit frame is an intercepted DALI command,
                    # it can be deciphered into a Command object
                    dali_frame = frame.ForwardFrame(
                        bits=8 * len(rx_dali), data=rx_dali
                    )
                    try:
                        dali_command = command.Command.from_frame(
                            dali_frame,
                            devicetype=self._prev_rx_enable_dt,
                            dev_inst_map=self._dev_inst_map,
                        )
                    except TypeError:
                        _LOG.error(
                            f"Failed to decode DALI command! Frame: {dali_frame}"
                        )
                        return
                    if isinstance(
                        dali_command, dali.gear.general.EnableDeviceType
                    ):
                        self._prev_rx_enable_dt = dali_command.param
                    else:
                        self._prev_rx_enable_dt = 0

                    _LOG.debug(f"Adding DALI command to queue: {dali_command}")
                    self._queue_rx_dali.distribute(dali_command)

        def _process_luba_response_dali_frame_to_tx(self, received_data: Sequence[int]) -> None:
            """
            Handle a LUBA 'ADD DALI FRAME TO TX BUFFER' response message
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.ADD_DALI_FRAME_TO_TX_RSP
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x33"
                )

            payload_length = received_data[2]
            if payload_length == 1:
                error_code = received_data[3]
                _LOG.error(
                    f"LUBA device reports error in transmission: {error_code}"
                )
                # No DALI frame reaches the bus, so the "frame sent" event that
                # normally confirms a transmission will never arrive. Surface
                # the error to the waiting 'send_dali_command' so it fails fast
                # instead of blocking until the confirmation timeout.
                self._queue_tx_conf.put_nowait(
                    self.LubaMsgTxConf(tx_id=-1, error_code=error_code)
                )
            elif payload_length == 2:
                tx_id = received_data[3]
                _LOG.trace(
                    f"LUBA device reports transmission accepted, ID: {tx_id}"
                )
            else:
                raise ValueError(
                    f"Invalid LUBA response length: {payload_length}"
                )

        def _process_luba_response_device_info(self, received_data: Sequence[int]) -> None:
            """
            Handle a received "QUERY DEVICE INFO" response message
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.QUERY_DEVICE_INFO_RSP
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x21"
                )

            # QUERY DEVICE INFO supports two "sets" of data, and the only way
            # differentiate between them is to check for response length.
            # When querying request set "0", response length should be 20 bytes,
            # and for request set "1", response length should be 18 bytes.
            # Currently this driver only ever requests set "0", therefore the
            # harcoded response handling.
            try:
                payload_length = self._buffer[2]
            except IndexError:
                raise ValueError(
                    f"Invalid data for QUERY DEVICE INFO response packet"
                )

            if payload_length not in [20, 18]:
                raise ValueError(
                    f"Unexpected payload length {payload_length} for QUERY DEVICE INFO response"
                )

            if payload_length == 18:
                raise NotImplementedError(
                    f"QUERY DEVICE INFO with set \"1\" is not yet implemented"
                )

            info = DriverLubaRs232.LubaDeviceInfo(
                gtin=int.from_bytes(bytes(received_data[3:9]), byteorder="big"),
                id=int.from_bytes(bytes(received_data[9:17]), byteorder="big"),
                pcb_ver=received_data[17],
                assembly_ver=received_data[18],
                article_num=int.from_bytes(
                    bytes(received_data[19:23]), byteorder="big"
                ),
            )
            _LOG.info(f"Received device info: {info}")
            if info.article_num not in DriverLubaRs232.TESTED_ARTICLE_NUMBERS:
                tested = ", ".join(
                    str(num) for num in sorted(DriverLubaRs232.TESTED_ARTICLE_NUMBERS)
                )
                _LOG.warning(
                    "DriverLubaRs232 has only been tested with Lunatone article "
                    f"nr. {tested}, not nr. {info.article_num}"
                )
            self._dev_info = info
            self._queue_rx_luba_cmd.put_nowait(info)

        def _process_luba_response_device_descriptor(
            self, received_data: Sequence[int]
        ) -> None:
            """
            Handle a received "QUERY DEVICE DESCRIPTOR" response message
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.QUERY_DEVICE_DESCRIPTOR_RSP
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x29"
                )

            payload_length = received_data[2]
            # The DeviceDescriptor is 19 bytes, of which HardwareFeature is the
            # last one. Only its bit 7 (switchable bus power supply) is used.
            if payload_length < 19:
                raise ValueError(
                    f"Unexpected payload length {payload_length} for QUERY "
                    "DEVICE DESCRIPTOR response"
                )
            hardware_feature = received_data[3 + 18]
            descriptor = DriverLubaRs232.LubaDeviceDescriptor(
                has_bus_power_supply=bool(hardware_feature & 0b10000000),
            )
            _LOG.info(f"Received device descriptor: {descriptor}")
            self._queue_rx_luba_cmd.put_nowait(descriptor)

        def _process_luba_response_status(self, received_data: Sequence[int]) -> None:
            """
            Handle a received "READ STATUS" response message
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.READ_STATUS_RSP
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x2D"
                )

            payload_length = received_data[2]
            # Payload layout: Line, Tick (2), ID, NrOfEntries, Status. The
            # Status byte (payload index 5) is only present for an available
            # DALI line; a length of 1 means the requested line does not exist.
            if payload_length < 6:
                raise ValueError(
                    f"READ STATUS response without status byte (payload "
                    f"length {payload_length})"
                )
            status = received_data[3 + 5]
            line_status = DriverLubaRs232.LubaLineStatus(
                bus_voltage_error=bool(status & 0b10000000),
            )
            _LOG.info(f"Received line status: {line_status}")
            self._queue_rx_luba_cmd.put_nowait(line_status)

        def _process_luba_response_settings(self, received_data: Sequence[int]) -> None:
            """
            Handle a received "READ / WRITE SETTINGS" response message
            """
            if (
                DriverLubaRs232.LubaCmd(self._buffer[1])
                != DriverLubaRs232.LubaCmd.READ_WRITE_SETTINGS_RSP
            ):
                raise ValueError(
                    f"Wrong event type 0x{self._buffer[1]:02x}, expected 0x2B"
                )

            settings = DriverLubaRs232.LubaDeviceSettings(
                mode=received_data[3], event_filter=received_data[4]
            )
            _LOG.info(f"Received device settings: {settings}")
            self._queue_rx_luba_cmd.put_nowait(settings)

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            self.transport = cast(serialx.SerialTransport, transport)
            _LOG.info(f"Serial port opened: {transport}")
            self._connected.set()

        def data_received(self, data: bytes) -> None:
            _LOG.trace(f"Serial data received: {data!r}")
            for rx in data:
                self._process_byte(rx)

        def connection_lost(self, exc: Optional[Exception]) -> None:
            _LOG.info("Serial port closed")
            self._connected.clear()

        @property
        def connected(self) -> asyncio.Event:
            return self._connected

        @property
        def device_info(self) -> Optional[DriverLubaRs232.LubaDeviceInfo]:
            return self._dev_info

    def __init__(
        self,
        uri: str | ParseResult,
        dev_inst_map: Optional[DeviceInstanceTypeMapper] = None,
        bus_power: bool = False,
    ):
        super().__init__(uri=uri, dev_inst_map=dev_inst_map)

        self.serial_path = self.uri.path
        _LOG.info(f"Initialising luba232 driver for '{self.serial_path}'")
        # Whether to switch on the interface's integrated bus power supply
        self.bus_power = bus_power
        self._transport: Optional[serialx.SerialTransport] = None
        self._protocol: Optional[DriverLubaRs232.LubaProtocol] = None

    @property
    def _proto(self) -> DriverLubaRs232.LubaProtocol:
        """The connected protocol, or raise if the driver is not connected."""
        if self._protocol is None:
            raise IOError("DALI driver not connected")
        return self._protocol

    async def connect(self, *, scan_dev_inst: bool = False) -> None:
        if self.is_connected:
            _LOG.warning(
                f"'connect()' called but luba232 driver already connected"
            )
            return

        # TODO: Add failure/retry handling
        transport, protocol = await serialx.create_serial_connection(
            loop=asyncio.get_event_loop(),
            protocol_factory=DriverLubaRs232.LubaProtocol,
            url=self.serial_path,
            baudrate=38400,
        )
        self._transport = transport
        self._protocol = cast(DriverLubaRs232.LubaProtocol, protocol)
        try:
            await asyncio.wait_for(
                self._proto.connected.wait(),
                timeout=DriverLubaRs232.timeout_connect,
            )
        except asyncio.exceptions.TimeoutError as exc:
            _LOG.critical(f"Timeout waiting for driver to connect: {exc}")
            raise

        for attempt in range(1, DriverLubaRs232.handshake_attempts + 1):
            try:
                await self._proto.send_device_info_query()
                self._proto.bus_power = self.bus_power
                await self._proto.send_device_settings()
                break
            except (asyncio.TimeoutError, TimeoutError):
                if attempt >= DriverLubaRs232.handshake_attempts:
                    _LOG.error(
                        "LUBA handshake timed out after %d attempts",
                        DriverLubaRs232.handshake_attempts,
                    )
                    raise
                _LOG.warning(
                    "LUBA handshake attempt %d timed out, retrying", attempt
                )
                self._proto.reset_luba_response()
        self._proto.dev_inst_map = self.dev_inst_map

        self._connected.set()

        # After switching on the integrated power supply the bus voltage takes
        # a moment to rise; sending DALI frames before then fails, so wait for
        # the bus to be powered before scanning.
        if self.bus_power:
            await self._wait_for_bus_power()

        # Scan the bus for control devices, and create a mapping of addresses
        # to instance types
        if scan_dev_inst:
            _LOG.info("Scanning DALI bus for control devices")
            await self.send(self.dev_inst_map.autodiscover())
            _LOG.info(
                f"Found {len(self.dev_inst_map.mapping)} enabled control "
                "device instances"
            )

    async def _wait_for_bus_power(self) -> None:
        """Wait for the integrated power supply to bring up the bus voltage."""
        loop = asyncio.get_event_loop()
        deadline = loop.time() + DriverLubaRs232.timeout_bus_power
        while loop.time() < deadline:
            status = await self._proto.send_read_status()
            if status is not None and not status.bus_voltage_error:
                return
            await asyncio.sleep(0.1)
        _LOG.warning("DALI bus voltage not detected after enabling bus power")

    async def query_device_descriptor(
        self,
    ) -> Optional[DriverLubaRs232.LubaDeviceDescriptor]:
        """Return the interface's device descriptor (feature flags)."""
        if not self.is_connected:
            raise IOError("DALI driver cannot query, not connected")
        return await self._proto.send_device_descriptor_query()

    async def read_status(self) -> Optional[DriverLubaRs232.LubaLineStatus]:
        """Return the status of the DALI line (e.g. bus power state)."""
        if not self.is_connected:
            raise IOError("DALI driver cannot query, not connected")
        return await self._proto.send_read_status()

    async def _send_frame(
        self, cmd: command.Command, *, priority: int = 1
    ) -> Optional[command.Response]:
        # Only send if the driver is connected
        if not self.is_connected:
            _LOG.critical(f"DALI driver cannot send, not connected: {self}")
            raise IOError("DALI driver cannot send, not connected")

        response = None

        # Make sure the received command buffer is empty, so that an
        # unexpected response can't accidentally be used
        self._proto.reset_dali_response()
        await self._proto.send_dali_command(cmd, priority=priority)
        response_type = cmd.response
        if response_type is not None:
            # Default to the command's own response type so that a query
            # which times out is reported as a missing value; a bare
            # Response(None) passes check_bad_rsp and leaks None to callers.
            response = response_type(None)
            while True:
                try:
                    raw_rsp = await asyncio.wait_for(
                        self._proto.wait_dali_raw_response(),
                        timeout=DriverLubaRs232.timeout_rx,
                    )
                except asyncio.exceptions.TimeoutError:
                    _LOG.debug(f"DALI response timeout, from message: {cmd}")
                    break
                if raw_rsp is _DALI_FRAMING_ERROR:
                    response = response_type(frame.BackwardFrameError(255))
                    _LOG.debug(f"DALI framing error, from message: {cmd}")
                    break
                if isinstance(raw_rsp, int):
                    response = response_type(frame.BackwardFrame(raw_rsp))
                    _LOG.debug(f"DALI response received: {raw_rsp}")
                    break
                else:
                    _LOG.warning(
                        "DALI response expected to be 'int' but got type "
                        f"'{type(raw_rsp)}': {raw_rsp}"
                    )
                    raw_rsp = None
                    continue

        return response

    def new_dali_rx_queue(self) -> DistributorQueue:
        return DistributorQueue(self._proto.queue_rx_dali)



class DriverSCIRS232(DriverSerialBase):
    uri_scheme = "scirs232"
    timeout_rx = 0.03
    timeout_tx_confirm = 0.1
    timeout_connect = 1.0

    class SCIRS232Code(Enum):
        """
        All supported SCI mode codes and status codes. Refer Lunatone's
        documentation:
        hhttps://www.lunatone.com/wp-content/uploads/2018/03/22176438-HS_DALI_SCI_RS232_EN_D0045.pdf
        """
        STATUS_OK = 0x0
        STATUS_DALI_NO = 0x1
        SEND_DALI_8 = 0x2
        SEND_DALI_16 = 0x3
        SEND_EDALI = 0x4
        SEND_DSI = 0x5
        SEND_DALI_17 = 0x6
        ERROR = 0x7
        SEND_DALI2_24 = 0x8

    class SCIRS232DeviceReply(NamedTuple):
        """
        Named tuple for storing a set of information about the SCI RS232 device.

        This information is sent in every frame, but updates are ignored after
        initialisation of the software.
        """

        id: int
        code: int

    class SCIRS232DeviceSettings(NamedTuple):
        """
        Named tuple for storing a set of information about the SCI RS232 device.

        These are sent on a per-frame basis, so the device is state-less with
        respect to the DALI receive and transmit parameters.
        """

        monitor_enable: bool
        identify : bool
        echo:bool

    class SCIRS232Protocol(asyncio.Protocol):
        """
        This class is internally used by DriverSCIRS232 to implement a state
        machine for decoding the incoming serial bytes into SCI RS232 messages,
        which in turn wrap DALI frames. The class also handles encoding DALI
        frames into SCI RS232 messages, setting the appropriate flags etc.
        """

        MAX_LEN = 5
        CONTROL_ME_MASK         = 0b10000000
        CONTROL_IDENTIFY_MASK   = 0b01000000
        CONTROL_ECHO_MASK       = 0b00100000
        CONTROL_SEND_TWICE_MASK = 0b00010000
        CONTROL_MODE_MASK       = 0b00001111

        STATUS_ID_MASK   = 0b11110000
        STATUS_CODE_MASK = 0b00001111

        class ReadState(Enum):
            """
            Enum of states used in the receiver state machine
            """

            WAIT_STATUS = 1
            WAIT_DATA_HI = 2
            WAIT_DATA_MI = 3
            WAIT_DATA_LO = 4
            WAIT_CHECKSUM = 5

        class ErrorType(Enum):
            CHECKSUM = 1
            DALI_BUS_SHORT_CIRCUIT = 2
            DALI_RX_ERROR = 3
            UNKNOWN_COMMAND = 4
            COLLISION_DETECTED = 5

        class SCIRS232MsgTxConf(NamedTuple):
            """
            Named tuple used to enqueue messages
            """

            message: Optional[command.Command] = None

        def __init__(self) -> None:
            super().__init__()
            self.transport: Optional[serialx.SerialTransport] = None

            self._queue_rx_dali = DistributorQueue()
            self._queue_rx_raw_dali: asyncio.Queue[Any] = asyncio.Queue()
            self._queue_rx_info: asyncio.Queue[Any] = asyncio.Queue()
            self._prev_rx_enable_dt = 0
            self._prev_tx_enable_dt = 0
            self._tx_lock = asyncio.Lock()
            self._rx_state = self.ReadState.WAIT_STATUS
            self.rx_idle = asyncio.Event()
            self._buffer: list[int] = []
            self._rx_expected_len: Optional[int] = None
            self._rx_received_len: int = 0
            self._connected = asyncio.Event()
            self._dev_info: Optional[DriverSCIRS232.SCIRS232DeviceReply] = None
            self._dev_inst_map: Optional[DeviceInstanceTypeMapper] = None
            self._device_settings = DriverSCIRS232.SCIRS232DeviceSettings(
                monitor_enable=True,
                identify=False,
                echo=True)

            self.reset()

        @property
        def _tx(self) -> serialx.SerialTransport:
            """The connected serial transport, or raise if not connected."""
            if self.transport is None:
                raise IOError("serial transport not connected")
            return self.transport

        @property
        def rx_state(self) -> ReadState:
            assert self._rx_state is not None
            return self._rx_state

        @rx_state.setter
        def rx_state(self, state: ReadState) -> None:
            if not isinstance(state, self.ReadState):
                raise TypeError(
                    f"rx_state must be a ReadState enum, not {type(state)}"
                )

            self._rx_state = state
            if state == self.ReadState.WAIT_STATUS:
                self.rx_idle.set()
            else:
                self.rx_idle.clear()

        @property
        def dev_inst_map(self) -> Optional[DeviceInstanceTypeMapper]:
            return self._dev_inst_map

        @dev_inst_map.setter
        def dev_inst_map(self, value: DeviceInstanceTypeMapper) -> None:
            self._dev_inst_map = value

        @property
        def queue_rx_dali(self) -> DistributorQueue:
            return self._queue_rx_dali

        def reset(self) -> None:
            """
            Returns the state machine to "WAIT_STATUS"
            """
            self.rx_state = self.ReadState.WAIT_STATUS
            self._buffer = [0] * self.MAX_LEN
            self._rx_expected_len = None
            self._rx_received_len = 0

        async def wait_dali_raw_response(self) -> int:
            """
            Async method which waits for a raw (i.e. un-decoded) DALI frame
            to be received from the SCI RS232 device.

            :return: A received DALI frame, as an int
            """
            return cast(int, await self._queue_rx_raw_dali.get())

        def reset_dali_response(self) -> None:
            """Drop any DALI frames left buffered from a previous exchange.

            Backward frames and information frames that arrive after their
            query's receive timeout have no matching request, so they are
            cleared before the next transaction. On a busy bus this is routine
            housekeeping, hence debug level.
            """
            discarded = _drain_queue(self._queue_rx_raw_dali)
            if discarded:
                _LOG.debug(
                    "SCI RS232 RX DALI queue: discarded %d stale response(s): %s",
                    len(discarded),
                    discarded,
                )

            discarded_info = _drain_queue(self._queue_rx_info)
            if discarded_info:
                _LOG.debug(
                    "SCI RS232 RX info queue: discarded %d stale frame(s): %s",
                    len(discarded_info),
                    discarded_info,
                )

        @staticmethod
        def _insert_checksum(in_ints: list[int]) -> None:
            in_ints[-1] = reduce(xor, in_ints[0:-1])

        async def send_dali_command(self, tx: command.Command) -> None:
            """
            Sends a variable length DALI command (16 or 24 bits), waiting
            until the SCI RS232 device confirms it has sent the message before
            returning the frame ID.

            :param tx: A single DALI command to send
            """
            # Make sure the serial interface is not in the process of reading
            # data before we send
            await self.rx_idle.wait()

            dali_ints = list(tx.frame.as_byte_sequence)
            if not len(dali_ints) in (1, 2, 3):
                raise ValueError(
                    f"Only works with 8, 16 or 24 bit messages, not {8*len(dali_ints)}"
                )

            control_byte = (self._device_settings.monitor_enable << 7) | (self._device_settings.identify << 6) | (self._device_settings.echo << 5) | (tx.sendtwice << 4)
            if len(dali_ints) == 1:
                control_byte |= 2
            elif len(dali_ints) == 2:
                control_byte |= 3
            elif len(dali_ints) == 3:
                control_byte |= 8

            tx_ints = [
                control_byte,
                dali_ints[0],
                0 if len(dali_ints) < 2 else dali_ints[1],
                0 if len(dali_ints) < 3 else dali_ints[2],
                0,  # Checksum
            ]
            # Fill in the checksum
            self._insert_checksum(tx_ints)

            # Use a mutex to ensure only one message is sent at a time,
            # waiting for the SCI RS232 device to confirm before sending another
            async with self._tx_lock:
                _LOG.debug(f"DALI sending message: {tx}")
                _LOG.trace(
                    f"SCI RS232 frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                confirm = await asyncio.wait_for(
                    self._queue_rx_info.get(),
                    timeout=DriverSCIRS232.timeout_tx_confirm,
                )
                if isinstance(confirm, DriverSCIRS232.SCIRS232DeviceReply):
                    _LOG.trace(f"SCI RS232 confirmed data with code {confirm.code}")
                else:
                    _LOG.error(f"Received unexpected confirmation object {confirm}")
            return

        async def send_device_info_query(self) -> None:
            """
            Query some basic information from the SCI RS232 device
            """
            # Use a mutex to ensure only one message is sent at a time
            async with self._tx_lock:
                _LOG.debug("Querying SCI RS232 device info")
                tx_ints = [
                    0b11000010, # enable monitoring and identify
                    0,
                    0,
                    0,
                    0,  # Checksum
                ]
                # Fill in the checksum
                self._insert_checksum(tx_ints)

                # empty queue (just in case)
                while not self._queue_rx_info.empty():
                    dev_info = self._queue_rx_info.get_nowait()
                    _LOG.warning(f"SCI RS232 info queue not empty, discarting: {dev_info}")

                _LOG.trace(
                    f"SCI RS232 frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self._tx.write(bytearray(tx_ints))

                # Wait for the SCI RS232 device to respond
                dev_info = await asyncio.wait_for(
                    self._queue_rx_info.get(),
                    timeout=DriverSCIRS232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(dev_info, DriverSCIRS232.SCIRS232DeviceReply):
                _LOG.error(f"Expected a SCI RS232, but got: {dev_info}")
                return
            
            self._device_info = dev_info

        def _process_byte(self, rx_int: int) -> None:
            if not isinstance(rx_int, int):
                raise TypeError(
                    f"Got an item of type: {type(rx_int)}, expected an integer"
                )

            # Handle each state of the state machine
            if self._rx_state == self.ReadState.WAIT_STATUS:
                self._buffer[0] = rx_int
                self._rx_state = self.ReadState.WAIT_DATA_HI

                return

            elif self._rx_state == self.ReadState.WAIT_DATA_HI:
                # In the 'WAIT_DATA_HI' state the next byte will be data high
                self._buffer[1] = rx_int
                self._rx_state = self.ReadState.WAIT_DATA_MI
                return

            elif self._rx_state == self.ReadState.WAIT_DATA_MI:
                # In the 'WAIT_DATA_MI' state the next byte will be data mid
                self._buffer[2] = rx_int
                self._rx_state = self.ReadState.WAIT_DATA_LO
                return

            elif self._rx_state == self.ReadState.WAIT_DATA_LO:
                # Read bytes, up to the maximum expected length
                self._buffer[3] = rx_int
                self._rx_state = self.ReadState.WAIT_CHECKSUM
                return

            elif self._rx_state == self.ReadState.WAIT_CHECKSUM:
                # In the 'WAIT_CHECKSUM' state, the next byte will be the
                # checksum
                self._buffer[4] = rx_int

                # We now have a full frame
                _LOG.trace(
                    f"Raw data: {[f'0x{data:02x}' for data in self._buffer]}"
                )

                # Validate the checksum: XOR all values, excluding the
                # synchronisation and checksum
                check = reduce(xor, self._buffer[0:4])

                if check != rx_int:
                    _LOG.warning(
                        f"SCI RS232 checksum failure! Calculated: {check}, "
                        f"Expected: {rx_int}"
                    )
                    self.reset()
                    return
                else:
                    _LOG.trace("SCI RS232 checksum passed, full frame received")
                    try:
                        status = DriverSCIRS232.SCIRS232Code(self._buffer[0] & DriverSCIRS232.SCIRS232Protocol.STATUS_CODE_MASK)
                    except ValueError:
                        _LOG.exception(
                            f"SCI RS232 unknown status code: 0x{self._buffer[0]:02x}"
                        )
                        self.reset()
                        return
                    
                    #TODO: handle status codes / options here
                    if status == DriverSCIRS232.SCIRS232Code.ERROR:
                        self._process_error(tuple(self._buffer[:4]))
                    elif status == DriverSCIRS232.SCIRS232Code.STATUS_OK:
                        self._process_system_message(self._buffer[0])
                    elif status == DriverSCIRS232.SCIRS232Code.STATUS_DALI_NO:
                        self._process_system_message(self._buffer[0])
                    elif status == DriverSCIRS232.SCIRS232Code.SEND_DALI_8:
                        self._process_dali_frame((self._buffer[3],))
                    elif status == DriverSCIRS232.SCIRS232Code.SEND_DALI_16:
                        self._process_dali_frame(self._buffer[2:4])
                    elif status == DriverSCIRS232.SCIRS232Code.SEND_DALI2_24:
                        self._process_dali_frame(self._buffer[1:4])
                    elif (status == DriverSCIRS232.SCIRS232Code.SEND_EDALI) or \
                            (status == DriverSCIRS232.SCIRS232Code.SEND_DSI) or \
                            (status == DriverSCIRS232.SCIRS232Code.SEND_DALI_17):
                        _LOG.error(
                            f"SCI RS232 eDALI, DSI or 17-bit DALI message received. These are not supported."
                            f" data: {self._buffer[1:4]}"
                        )
                    else:
                        _LOG.error(
                            f"SCI RS232 unexpected message, status {self._buffer[0]:02x},"
                            f" data: {self._buffer[1:4]}"
                        )

                    self.reset()
                    return
            else:
                raise RuntimeError(f"Invalid state: {self._rx_state}")
            
        def _process_system_message(self, data: int) -> None:
            device_id_info = DriverSCIRS232.SCIRS232DeviceReply(
                id=(data & 0xf0) >> 4,code=data&0xf)
            self._queue_rx_info.put_nowait(device_id_info) 
        
        def _process_error(self, data: Sequence[int]) -> None:
            try:
                error_type = DriverSCIRS232.SCIRS232Protocol.ErrorType(data[3])
            except ValueError:
                _LOG.exception(
                    f"SCI RS232 unknown error code: 0x{data[3]:02x}"
                )
                self.reset()
                return
            if error_type == DriverSCIRS232.SCIRS232Protocol.ErrorType.CHECKSUM:
                error_str = "checksum"
            elif error_type == DriverSCIRS232.SCIRS232Protocol.ErrorType.DALI_BUS_SHORT_CIRCUIT:
                error_str = "short circuit on the DALI bus"
            elif error_type == DriverSCIRS232.SCIRS232Protocol.ErrorType.DALI_RX_ERROR:
                error_str = "DALI receive error"
            elif error_type == DriverSCIRS232.SCIRS232Protocol.ErrorType.UNKNOWN_COMMAND:
                error_str = "unknown command"
            else:
                error_str = "unknown"
                _LOG.error(
                    f"No string defined for SCI RS232 error code: 0x{data[3]:02x}"
                )
            _LOG.error(f"SCI RS232 reports {error_str} error ({error_type})")
            self._process_system_message(data[0])

        def _process_dali_frame(self, received_data: Sequence[int]) -> None:
            """
            Handle a DALI 'event' message, typically these are received when
            a DALI frame was observed on the bus by the SCI RS232 device
            """

            _LOG.trace(
                f"SCI RS232 DALI frame received: {[f'0x{data:02x}' for data in received_data]}"
            )

            if len(received_data) == 1:
                # An 8-bit frame is a response, don't try to decipher it
                # here because it depends on context which the 'send()'
                # routine will have to handle
                self._queue_rx_raw_dali.put_nowait(received_data[0])
                _LOG.trace(
                    f"Adding raw DALI response to queue: '{received_data[0]}'"
                )
            else:
                # A 16 or 24-bit frame is an intercepted DALI command,
                # it can be deciphered into a Command object
                dali_frame = frame.ForwardFrame(
                    bits=8 * len(received_data), data=received_data
                )
                try:
                    dali_command = command.Command.from_frame(
                        dali_frame,
                        devicetype=self._prev_rx_enable_dt,
                        dev_inst_map=self._dev_inst_map,
                    )
                except TypeError:
                    _LOG.error(
                        f"Failed to decode DALI command! Frame: {dali_frame}"
                    )
                    return
                if isinstance(
                    dali_command, dali.gear.general.EnableDeviceType
                ):
                    self._prev_rx_enable_dt = dali_command.param
                else:
                    self._prev_rx_enable_dt = 0

                _LOG.debug(f"Adding DALI command to queue: {dali_command}")
                self._queue_rx_dali.distribute(dali_command)

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            self.transport = cast(serialx.SerialTransport, transport)
            _LOG.info(f"Serial port opened: {transport}")
            self._connected.set()

        def data_received(self, data: bytes) -> None:
            _LOG.trace(f"Serial data received: {data!r}")
            for rx in data:
                self._process_byte(rx)

        def connection_lost(self, exc: Optional[Exception]) -> None:
            _LOG.info("Serial port closed")
            self._connected.clear()

        @property
        def connected(self) -> asyncio.Event:
            return self._connected

        @property
        def device_info(self) -> Optional[DriverSCIRS232.SCIRS232DeviceReply]:
            return self._dev_info


    def __init__(
        self,
        uri: str | ParseResult,
        dev_inst_map: Optional[DeviceInstanceTypeMapper] = None,
    ):
        super().__init__(uri=uri, dev_inst_map=dev_inst_map)

        self.serial_path = self.uri.path
        _LOG.info(f"Initialising SCI RS232 driver for '{self.serial_path}'")
        self._transport: Optional[serialx.SerialTransport] = None
        self._protocol: Optional[DriverSCIRS232.SCIRS232Protocol] = None

    @property
    def _proto(self) -> DriverSCIRS232.SCIRS232Protocol:
        """The connected protocol, or raise if the driver is not connected."""
        if self._protocol is None:
            raise IOError("DALI driver not connected")
        return self._protocol

    async def connect(self, *, scan_dev_inst: bool = False) -> None:
        if self.is_connected:
            _LOG.warning(
                f"'connect()' called but SCI RS232 driver already connected"
            )
            return

        _LOG.info(
                f"Creating serial connection to {self.serial_path}"
            )

        # TODO: Add failure/retry handling
        transport, protocol = await serialx.create_serial_connection(
            loop=asyncio.get_event_loop(),
            protocol_factory=DriverSCIRS232.SCIRS232Protocol,
            url=self.serial_path,
            baudrate=38400,
        )
        self._transport = transport
        self._protocol = cast(DriverSCIRS232.SCIRS232Protocol, protocol)

        try:
            await asyncio.wait_for(
                self._proto._connected.wait(),
                timeout=DriverSCIRS232.timeout_connect,
            )
        except asyncio.exceptions.TimeoutError as exc:
            _LOG.critical(f"Timeout waiting for driver to connect: {exc}")
            raise

        await self._proto.send_device_info_query()
        self._proto.dev_inst_map = self.dev_inst_map

        self._connected.set()

        # Scan the bus for control devices, and create a mapping of addresses
        # to instance types
        if scan_dev_inst:
            _LOG.info("Scanning DALI bus for control devices")
            await self.send(self.dev_inst_map.autodiscover())
            _LOG.info(
                f"Found {len(self.dev_inst_map.mapping)} enabled control "
                "device instances"
            )

    async def _send_frame(
        self, cmd: command.Command, *, priority: int = 1
    ) -> Optional[command.Response]:
        # The SCI RS232 protocol has no transmit priority field, so `priority`
        # is accepted for a uniform driver API but not used on the wire.
        # Only send if the driver is connected
        if not self.is_connected:
            _LOG.critical(f"DALI driver cannot send, not connected: {self}")
            raise IOError("DALI driver cannot send, not connected")

        response = None

        # Make sure the received command buffer is empty, so that an
        # unexpected response can't accidentally be used
        self._proto.reset_dali_response()
        await self._proto.send_dali_command(cmd)
        response_type = cmd.response
        if response_type is not None:
            # Default to the command's own response type so that a query
            # which times out is reported as a missing value; a bare
            # Response(None) passes check_bad_rsp and leaks None to callers.
            response = response_type(None)
            while True:
                try:
                    raw_rsp = await asyncio.wait_for(
                        self._proto._queue_rx_raw_dali.get(),
                        #self._proto.wait_dali_raw_response(),
                        timeout=DriverSCIRS232.timeout_rx,
                    )
                except asyncio.exceptions.TimeoutError:
                    _LOG.debug(f"DALI response timeout, from message: {cmd}")
                    break
                if isinstance(raw_rsp, int):
                    response = response_type(frame.BackwardFrame(raw_rsp))
                    _LOG.debug(f"DALI response received: {raw_rsp}")
                    break
                else:
                    _LOG.warning(
                        "DALI response expected to be 'int' but got type "
                        f"'{type(raw_rsp)}': {raw_rsp}"
                    )
                    raw_rsp = None
                    continue

        return response

    def new_dali_rx_queue(self) -> DistributorQueue:
        return DistributorQueue(self._proto.queue_rx_dali)
