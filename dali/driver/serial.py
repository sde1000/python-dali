"""
serial.py - Driver for serial-based DALI interfaces, including the
Lunatone RS232 LUBA device


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
from enum import Enum
from functools import reduce
from operator import xor
from typing import Any, Callable, Generator, NamedTuple, Optional
from urllib.parse import ParseResult, urlparse, urlunparse

import serial_asyncio

import dali.gear
from dali import command, frame, gear, sequences
from dali.driver import trace_logging  # noqa: F401
from dali.device.helpers import DeviceInstanceTypeMapper

_LOG = logging.getLogger("dali.driver")


class DistributorQueue(asyncio.Queue):
    def __init__(self, parent: Optional[DistributorQueue] = None, *, maxsize=0):
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

    def add_handler(self, handler: DistributorQueue):
        if self.is_parent:
            self._handlers[hash(handler)] = handler
        else:
            # Don't allow more than one layer of nesting, to avoid confusion
            raise RuntimeError(
                "Cannot add handler to DistributorQueue with a parent"
            )

    def del_handler(self, handler: DistributorQueue):
        self._handlers.pop(hash(handler), None)

    def distribute(self, item: Any):
        if self._parent is not None:
            self.put_nowait(item)
        for handler in self._handlers.values():
            handler.distribute(item)

    def __del__(self):
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

        try:
            uri.path
        except AttributeError:
            uri = urlparse(uri)

        if uri.scheme != self.uri_scheme:
            raise TypeError(
                f"Cannot create a {self.__class__.__name__} "
                f"instance with a scheme of {uri.scheme}"
            )

        self.uri = uri
        self.dev_inst_map: DeviceInstanceTypeMapper = dev_inst_map
        if dev_inst_map is None:
            self.dev_inst_map = DeviceInstanceTypeMapper()
        self._connected = asyncio.Event()
        self.transaction_lock = asyncio.Lock()

    def __repr__(self):
        return f'{self.__class__.__name__}("{urlunparse(self.uri)}")'

    def __hash__(self):
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

        :return: Boolean, true if connection is ready
        """
        return self._connected.is_set()

    async def wait_connected(self) -> None:
        """
        Blocks until the underlying transport is connected and ready for use

        :return: None
        """
        await self._connected.wait()

    async def send(
        self, msg: command.Command, in_transaction: bool = False
    ) -> Optional[command.Response]:
        """
        Send one DALI command over the bus using the driver. If the command
        expects a response this will be returned.

        :param msg: A Command object to send over the DALI bus
        :param in_transaction: Boolean flag to indicate if this `send()` call
        is part of a transaction, i.e. where the driver will block sending
        other messages until the transaction is complete. This is typically
        only needed internally, by the `run_sequence()` method.
        :return: Either None if no response is expected, or a Response object
        """
        raise NotImplementedError(
            "'send()' needs to be implemented in a subclass"
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
        Run a command sequence as a transaction. Implements the same API as
        the 'hid' drivers.

        :param seq: A "generator" function to use as a sequence. These are
        available in various places in the python-dali library.
        :param progress: A function to call with progress updates, used by
        some sequences to provide status information. The function must
        accept a single argument. A suitable example is `progress=print` to
        use the built-in `print()` function.
        :return: Depends on the sequence being used
        """
        async with self.transaction_lock:
            response = None
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
                            # The 'send()' calls here *do* refer to the DALI
                            # transmit method
                            await self.send(
                                gear.general.EnableDeviceType(cmd.devicetype),
                                in_transaction=True,
                            )
                        response = await self.send(cmd, in_transaction=True)
            finally:
                seq.close()


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
        EVENT_MESSAGE = 0x31
        ADD_DALI_FRAME_TO_TX_CMD = 0x32
        ADD_DALI_FRAME_TO_TX_RSP = 0x33
        ADD_16DALI_FRAME_TO_TX_CMD = 0x34
        ADD_16DALI_FRAME_TO_TX_RSP = 0x35
        ADD_24DALI_FRAME_TO_TX_CMD = 0x36
        ADD_24DALI_FRAME_TO_TX_RSP = 0x37

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

        def __init__(self) -> None:
            super().__init__()
            self.transport = None

            self._queue_rx_dali = DistributorQueue()
            self._queue_rx_raw_dali = asyncio.Queue()
            self._queue_rx_luba_cmd = asyncio.Queue()
            self._queue_tx_conf = asyncio.Queue()
            self._prev_rx_enable_dt = 0
            self._prev_tx_enable_dt = 0
            self._tx_lock = asyncio.Lock()
            self._rx_state = None
            self.rx_idle = asyncio.Event()
            self._buffer = None
            self._rx_expected_len = None
            self._rx_received_len = None
            self._connected = asyncio.Event()
            self._dev_info: Optional[DriverLubaRs232.LubaDeviceInfo] = None
            self._dev_inst_map: Optional[DeviceInstanceTypeMapper] = None

            self.reset()

        @property
        def rx_state(self) -> ReadState:
            return self._rx_state

        @rx_state.setter
        def rx_state(self, state: ReadState):
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
        def dev_inst_map(self, value: DeviceInstanceTypeMapper):
            self._dev_inst_map = value

        @property
        def queue_rx_dali(self) -> DistributorQueue:
            return self._queue_rx_dali

        def reset(self):
            """
            Returns the state machine to "WAIT_START"
            """
            self.rx_state = self.ReadState.WAIT_START
            self._buffer = [None] * self.MAX_LEN
            self._rx_expected_len = None
            self._rx_received_len = 0

        async def wait_dali_raw_response(self) -> int:
            """
            Async method which waits for a raw (i.e. un-decoded) DALI frame
            to be received from the LUBA device.

            :return: A received DALI frame, as an int
            """
            return await self._queue_rx_raw_dali.get()

        def reset_dali_raw_response(self) -> None:
            """
            Forces the queue of received DALI responses to be cleared, logging
            any responses that are dropped if the queue is not empty
            """
            qlen = self._queue_rx_raw_dali.qsize()
            if qlen:
                _LOG.critical(
                    f"LUBA RX DALI queue not empty! {qlen} items in queue!"
                )
                try:
                    item = self._queue_rx_raw_dali.get_nowait()
                    _LOG.critical(f"LUBA RX DALI queue discarding: {item}")
                except asyncio.QueueEmpty:
                    pass

        @staticmethod
        def _insert_checksum(in_ints: list[int]) -> None:
            in_ints[-1] = reduce(xor, in_ints[1:-1])

        async def send_dali_command(self, tx: command.Command) -> None:
            """
            Sends a variable length DALI command (16 or 24 bits), waiting
            until the LUBA device confirms it has sent the message before
            returning the frame ID.

            :param tx: A single DALI command to send
            """
            # Make sure the serial interface is not in the process of reading
            # data before we send
            await self.rx_idle.wait()

            dali_ints = tx.frame.as_byte_sequence
            if not len(dali_ints) in (2, 3):
                raise ValueError(
                    f"Only works with 16 or 24 bit messages, not {8*len(dali_ints)}"
                )
            # Determine the message priority - standard commands and DAPC are
            # high priority, others are low
            if (
                isinstance(tx, gear.general._StandardCommand)
                and not tx.response
                and not tx.sendtwice
            ) or isinstance(tx, gear.general.DAPC):
                priority = 0b00000010  # Priority 2 (second-highest)
            else:
                priority = 0b00000101  # Priority 5 (lowest)
            luba_mode = 0
            luba_mode |= priority
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
                None,  # Checksum
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
                self.transport.write(bytearray(tx_ints))

                # Wait for the LUBA device to respond, considering whether the
                # message is sent twice or not
                confirm_count = 2 if tx.sendtwice else 1
                while confirm_count > 0:
                    confirm = await asyncio.wait_for(
                        self._queue_tx_conf.get(),
                        timeout=DriverLubaRs232.timeout_tx_confirm,
                    )
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
                        _LOG.warning(
                            f"Unable to decode message id {confirm.tx_id}, but "
                            "LUBA device reports it was sent successfully"
                        )
                    confirm_count -= 1
            # Release the lock

            return confirm.tx_id

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
                    None,  # Checksum
                ]
                # Fill in the checksum
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self.transport.write(bytearray(tx_ints))

                # Wait for the LUBA device to respond
                dev_info = await asyncio.wait_for(
                    self._queue_rx_luba_cmd.get(),
                    timeout=DriverLubaRs232.timeout_tx_confirm,
                )
            # Release transmit mutex

            if not isinstance(dev_info, DriverLubaRs232.LubaDeviceInfo):
                _LOG.error(f"Expected a LubaDeviceInfo, but got: {dev_info}")
                return

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
                event_settings = 0b00010010
                tx_ints = [
                    0x59,  # ASCII 'Y'
                    DriverLubaRs232.LubaCmd.READ_WRITE_SETTINGS_CMD.value,  # LUBA Command
                    2,  # Length
                    mode_settings,
                    event_settings,
                    None,  # Checksum
                ]
                # Fill in the checksum
                self._insert_checksum(tx_ints)

                _LOG.trace(
                    f"LUBA frame to send: {[f'0x{data:02x}' for data in tx_ints]}"
                )
                self.transport.write(bytearray(tx_ints))

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

        def _process_luba_event(self, received_data: tuple):
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
                        frame.Frame(bits=8 * len(tx_dali), data=tx_dali),
                        devicetype=self._prev_tx_enable_dt,
                        dev_inst_map=self._dev_inst_map,
                    )
                except:
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
                    dali_frame = frame.Frame(
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

        def _process_luba_response_dali_frame_to_tx(self, received_data: tuple):
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
            elif payload_length == 2:
                tx_id = received_data[3]
                _LOG.trace(
                    f"LUBA device reports transmission accepted, ID: {tx_id}"
                )
            else:
                raise ValueError(
                    f"Invalid LUBA response length: {payload_length}"
                )

        def _process_luba_response_device_info(self, received_data: tuple):
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

            # QUERY DEVICE INFO supports two "sets" of data, this driver will
            # only ever request set "0", so it is safe enough to assume that
            # this is what the response refers to
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
            if info.article_num != 24166096:
                _LOG.warning(
                    "DriverLubaRs232 has only been tested with Lunatone article "
                    f"nr. 24166096, not nr. {info.article_num}"
                )
            self._dev_info = info
            self._queue_rx_luba_cmd.put_nowait(info)

        def _process_luba_response_settings(self, received_data: tuple):
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

        def connection_made(self, transport):
            self.transport = transport
            _LOG.info(f"Serial port opened: {transport}")
            self._connected.set()

        def data_received(self, data):
            _LOG.trace(f"Serial data received: {data}")
            for rx in data:
                self._process_byte(rx)

        def connection_lost(self, exc):
            _LOG.info("Serial port closed")
            self.transport.loop.stop()

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
    ):
        super().__init__(uri=uri, dev_inst_map=dev_inst_map)

        self.serial_path = self.uri.path
        _LOG.info(f"Initialising luba232 driver for '{self.serial_path}'")
        self._transport: Optional[serial_asyncio.SerialTransport] = None
        self._protocol: Optional[DriverLubaRs232.LubaProtocol] = None

    async def connect(self, *, scan_dev_inst: bool = False) -> None:
        if self.is_connected:
            _LOG.warning(
                f"'connect()' called but luba232 driver already connected"
            )
            return

        # TODO: Add failure/retry handling
        (
            self._transport,
            self._protocol,
        ) = await serial_asyncio.create_serial_connection(
            loop=asyncio.get_event_loop(),
            protocol_factory=DriverLubaRs232.LubaProtocol,
            url=self.serial_path,
            baudrate=38400,
        )
        try:
            await asyncio.wait_for(
                self._protocol.connected.wait(),
                timeout=DriverLubaRs232.timeout_connect,
            )
        except asyncio.exceptions.TimeoutError as exc:
            _LOG.critical(f"Timeout waiting for driver to connect: {exc}")
            raise

        await self._protocol.send_device_info_query()
        await self._protocol.send_device_settings()
        self._protocol.dev_inst_map = self.dev_inst_map

        self._connected.set()

        # Scan the bus for control devices, and create a mapping of addresses
        # to instance types
        if scan_dev_inst:
            _LOG.info("Scanning DALI bus for control devices")
            await self.run_sequence(self.dev_inst_map.autodiscover())
            _LOG.info(
                f"Found {len(self.dev_inst_map.mapping)} enabled control "
                "device instances"
            )

    async def send(
        self, msg: command.Command, in_transaction: bool = False
    ) -> Optional[command.Response]:
        # Only send if the driver is connected
        if not self.is_connected:
            _LOG.critical(f"DALI driver cannot send, not connected: {self}")
            raise IOError("DALI driver cannot send, not connected")

        response = None

        if not in_transaction:
            await self.transaction_lock.acquire()
        try:
            # Make sure the received command buffer is empty, so that an
            # unexpected response can't accidentally be used
            self._protocol.reset_dali_raw_response()
            await self._protocol.send_dali_command(msg)
            if msg.is_query:
                response = command.Response(None)
                while True:
                    try:
                        raw_rsp = await asyncio.wait_for(
                            self._protocol.wait_dali_raw_response(),
                            timeout=DriverLubaRs232.timeout_rx,
                        )
                    except asyncio.exceptions.TimeoutError:
                        _LOG.debug(
                            f"DALI response timeout, from message: {msg}"
                        )
                        break
                    if isinstance(raw_rsp, int):
                        response = msg.response(frame.BackwardFrame(raw_rsp))
                        _LOG.debug(f"DALI response received: {raw_rsp}")
                        break
                    else:
                        _LOG.warning(
                            "DALI response expected to be 'int' but got type "
                            f"'{type(raw_rsp)}': {raw_rsp}"
                        )
                        raw_rsp = None
                        continue
        finally:
            if not in_transaction:
                self.transaction_lock.release()

        return response

    def new_dali_rx_queue(self) -> DistributorQueue:
        return DistributorQueue(self._protocol.queue_rx_dali)
