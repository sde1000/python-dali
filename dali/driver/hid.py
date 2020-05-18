# async device drivers for HID-based devices like Tridonic DALI-USB
# and hasseb DALI Master

# See examples/50-dali-hid.rules for udev rules that will make
# suitably-named symlinks to the hidraw devices on Linux

import asyncio
import os
import struct
import logging
import random
import glob
from dali.exceptions import UnsupportedFrameTypeError, CommunicationError
from dali.sequences import sleep as seq_sleep
from dali.sequences import progress as seq_progress
import dali.frame

# dali.command and dali.gear are required for the bus traffic callback
import dali.command
import dali.gear
from dali.gear.general import EnableDeviceType

def _hex(b):
    return ''.join("%02X" % x for x in b)

class _callback:
    """Helper class for callback registration
    """
    def __init__(self, parent):
        self._parent = parent
        self._callbacks = {}

    class _callback_handle:
        """Callback handle

        Call unregister() to remove this callback.
        """
        def __init__(self, callback):
            self._callback = callback

        def unregister(self):
            del self._callback._callbacks[self]

    def register(self, func):
        wrapper = self._callback_handle(self)
        self._callbacks[wrapper] = func
        return wrapper

    def _invoke(self, *args):
        for func in self._callbacks.values():
            self._parent.loop.call_soon(func, self._parent, *args)

class hid:
    """Shared code for drivers that work with HID devices
    """
    def __init__(self, path, reconnect_interval=1, reconnect_limit=None,
                 loop=None, glob=False):
        self._log = logging.getLogger()
        self._path = path
        self._reconnect_interval = reconnect_interval
        self._reconnect_limit = reconnect_limit
        self._reconnect_count = 0
        self._reconnect_task = None
        self.loop = loop or asyncio.get_event_loop()
        self._glob = glob
        self._f = None

        # Should the send() method raise an exception if there is a
        # problem communicating with the underlying device, or should
        # it catch the exception and keep trying?  Set this attribute
        # as required.
        self.exceptions_on_send = True

        # Acquire this lock to perform a series of commands as a
        # transaction.  While you hold the lock, you must call send()
        # with keyword argument in_transaction=True
        self.transaction_lock = asyncio.Lock(loop=self.loop)

        # Register to be called back with "connected", "disconnected"
        # or "failed" as appropriate ("failed" means the reconnect
        # limit has been reached; no more connections will be
        # attempted unless you call connect() explicitly.)
        self.connection_status_callback = _callback(self)

        # Register to be called back with bus traffic; three arguments are passed:
        # command, response, config_command_error

        # config_command_error is true if the config command has a response, or
        # if the command was not sent twice within the required time limit
        self.bus_traffic = _callback(self)

        # This event will be set when we are connected to the device
        # and cleared when the connection is lost
        self.connected = asyncio.Event(loop=self.loop)

        # firmware_version and serial may be populated on some
        # devices, and will read as None on devices that don't support
        # reading them.  They are only valid after self.connected is
        # set.
        self.firmware_version = None
        self.serial = None

    def connect(self):
        """Attempt to connect to the device.

        Attempts to open the device.  If this fails, schedules a
        reconnection attempt.

        Returns True if opening the device file succeded immediately,
        False otherwise.  NB you must still await connected.wait()
        before using the device, because there may be further
        initialisation for the driver to perform.

        If your application is (for example) a command-line script
        that wants to report failure as early as possible, you could
        do so if this returns False.
        """
        if self._f:
            return True
        self._log.debug("trying to connect to %s...", self._path)
        if self._glob:
            path = glob.glob(self._path)
        else:
            path = [self._path]
        if path:
            try:
                if self._glob:
                    self._log.debug("trying concrete path %s", path[0])
                self._f = os.open(path[0], os.O_RDWR | os.O_NONBLOCK)
            except:
                self._f = None
        else:
            self._log.debug("path %s not found", self._path)
        if not self._f:
            # It didn't work.  Schedule a reconnection attempt if we can.
            self._log.debug("hid failed to open %s - waiting to try again", self._path)
            self._reconnect_task = asyncio.ensure_future(self._reconnect(), loop=self.loop)
            return False
        self._reconnect_count = 0
        self._initialise_device()
        self._log.debug("hid opened %s", path[0])
        self.loop.add_reader(self._f, self._reader)
        self.connection_status_callback._invoke("connected")
        return True

    async def _reconnect(self):
        self._reconnect_count += 1
        if self._reconnect_limit is not None \
           and self._reconnect_count > self._reconnect_limit:
            # We have failed.
            self._log.debug("connection limit reached")
            self._reconnect_count = 0
            self._reconnect_task = None
            return
        await asyncio.sleep(self._reconnect_interval)
        self._reconnect_task = None
        self.connect()

    def disconnect(self, reconnect=False):
        self._log.debug("disconnecting")
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        if self._f:
            self.loop.remove_reader(self._f)
            os.close(self._f)
        self._shutdown_device()
        self._f = None
        self.connected.clear()
        self.connection_status_callback._invoke("disconnected")
        if reconnect:
            self._reconnect_task = asyncio.ensure_future(self._reconnect())

    async def send(self, command, in_transaction=False, exceptions=None):
        """Send a DALI command and receive a response

        Sends the command.  Returns a response, or None if the command
        does not expect a response.

        If you have acquired the transaction_lock to perform a
        transaction, you must set the in_transaction keyword argument
        to True.

        This call can raise dali.exceptions.CommunicationError if
        there is a problem sending the command to the device.  If you
        prefer to wait for the device to become available again, pass
        exceptions=False or set the exceptions_on_send attribute to False.
        """
        if exceptions is None:
            exceptions = self.exceptions_on_send

        if not in_transaction:
            await self.transaction_lock.acquire()
        try:
            command_sent = False
            while not command_sent:
                try:
                    if command.devicetype != 0:
                        await self._send_raw(EnableDeviceType(command.devicetype))
                    response = await self._send_raw(command)
                    command_sent = True
                except CommunicationError:
                    if exceptions:
                        raise
            return response
        finally:
            if not in_transaction:
                self.transaction_lock.release()

    async def run_sequence(self, seq, progress=None):
        """Run a command sequence as a transaction
        """
        await self.transaction_lock.acquire()
        response = None
        try:
            while True:
                try:
                    cmd = seq.send(response)
                except StopIteration as r:
                    return r.value
                response = None
                if isinstance(cmd, seq_sleep):
                    await asyncio.sleep(cmd.delay)
                elif isinstance(cmd, seq_progress):
                    if progress:
                        progress(cmd)
                else:
                    if cmd.devicetype != 0:
                        await self._send_raw(EnableDeviceType(cmd.devicetype))
                    response = await self._send_raw(cmd)
        finally:
            self.transaction_lock.release()
            seq.close()

    def _initialise_device(self):
        """Send any device-specific initialisation commands
        """
        # Some devices may need to send initialisation commands and await
        # responses.  Those devices should override this method, and make sure
        # they set self.connected once initialisation is complete
        self.connected.set()

    def _shutdown_device(self):
        """Shut down everything that is waiting for the device

        The device has gone away.  Everything that is waiting for the
        device needs to be shut down explicitly.
        """
        pass

    def _reader(self):
        try:
            # No need to retry on InterruptedError since 3.5
            data = os.read(self._f, 64)
        except OSError:
            # Device has gone away
            data = b''
        if len(data) == 0:
            self.disconnect(reconnect=True)
            return
        self._handle_read(data)

    def _handle_read(self, data):
        pass

class tridonic(hid):
    # Commands sent to the interface
    _cmdtmpl = struct.Struct(">4Bx3sB55x")
    # _CMD send in byte 0
    _CMD_INIT = 0x01
    _CMD_BOOTLOADER = 0x02
    _CMD_SEND = 0x12

    # For _CMD_INIT, send in byte 1:
    _CMD_INIT_READVERSION = 0x00
    _CMD_INIT_READSERIAL = 0x02

    # For _CMD_SEND, send in byte 2
    _SEND_FLAGS_SETDTR0 = 0x10
    _SEND_FLAGS_SENDTWICE = 0x20

    # For _CMD_SEND, send in byte 3
    _SEND_FRAMESIZE_16 = 0x03

    # Responses received from the interface
    # Decodes to mode, response type, frame, interval, seq
    _resptmpl = struct.Struct(">BBx3sHB55x")
    _MODE_INFO = 0x01 # Response to an init command
    _MODE_OBSERVE = 0x11 # Other traffic observed on the bus
    _MODE_RESPONSE = 0x12 # Response to a send command

    # Response types
    _RESPONSE_NO_FRAME = 0x71
    _RESPONSE_BACKWARD_FRAME = 0x72
    _RESPONSE_FORWARD_FRAME = 0x73
    _RESPONSE_BUS_STATUS = 0x77 # bus or framing error - see byte 5

    # Bus status in byte 5
    _BUS_STATUS_SHORTED = 0x02
    _BUS_STATUS_FRAMING_ERROR = 0x03
    _BUS_STATUS_OK = 0x04
    _BUS_STATUS_DSI_MODE = 0x05
    _BUS_STATUS_DALI_MODE = 0x06

    @staticmethod
    def _seqnum(i):
        """Sequence number generator
        """
        while True:
            yield i
            i += 1
            if i > 0xff:
                i = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = self._log.getChild("tridonic")

        # Initialise the command sequence number to a random value, avoiding zero
        self._cmd_seq = iter(self._seqnum(random.randint(0x01, 0xff)))

        # Outstanding command events and message queues indexed by sequence number
        self._outstanding = {}

        # Semaphore controlling number of outstanding commands
        self._command_semaphore = asyncio.BoundedSemaphore(2, loop=self.loop)

        # Bus watch task, event and message queue
        self._bus_watch_task = None
        self._bus_watch_data_available = asyncio.Event(loop=self.loop)
        self._bus_watch_data = []

    def _initialise_device(self):
        # Read firmware version; pick up the reply in _handle_read
        os.write(self._f, self._cmd(
            tridonic._CMD_INIT, tridonic._CMD_INIT_READVERSION))

    async def _send_raw(self, command):
        frame = command.frame
        if len(frame) != 16:
            raise UnsupportedFrameTypeError
        await self.connected.wait()
        async with self._command_semaphore:
            seq = next(self._cmd_seq)
            self._log.debug("Sending with seq %x", seq)
            event = asyncio.Event(loop=self.loop)
            messages = []
            # If seq is in self._outstanding this means we've wrapped
            # around the whole sequence number space with an event
            # still outstanding: clearly a bug!
            assert seq not in self._outstanding
            self._outstanding[seq] = (event, messages)
            data = self._cmd(self._CMD_SEND, seq,
                             flags=self._SEND_FLAGS_SENDTWICE if command.sendtwice else 0,
                             ftype=self._SEND_FRAMESIZE_16, frame=frame.pack_len(3))
            try:
                os.write(self._f, data)
            except OSError:
                # The device has failed.  Disconnect, schedule a
                # reconnection, and report this command as failed.
                self._log.debug("fail on transmit, disconnecting")
                self.disconnect(reconnect=True)
                raise CommunicationError

            outstanding_transmissions = 2 if command.sendtwice else 1
            response = None
            while outstanding_transmissions or response is None:
                if len(messages) == 0:
                    await event.wait()
                    event.clear()
                message = messages.pop(0)
                if message == "fail":
                    # The device has gone away, possibly in the middle of processing
                    # our command.
                    self._log.debug("processing queued fail on receive")
                    raise CommunicationError

                # The message mode is guaranteed to be _MODE_RESPONSE
                mode, rtype, frame, interval, seq = self._resptmpl.unpack(message)
                self._log.debug(f"mode={mode:02x} rtype={rtype:02x} frame={frame} interval={interval:04x} seq={seq:02x}")
                if rtype == self._RESPONSE_FORWARD_FRAME:
                    # XXX check the frame contents?
                    outstanding_transmissions -= 1
                elif rtype == self._RESPONSE_BACKWARD_FRAME:
                    response = dali.frame.BackwardFrame(frame)
                elif rtype == self._RESPONSE_BUS_STATUS \
                     and message[5] == self._BUS_STATUS_FRAMING_ERROR:
                    response = dali.frame.BackwardFrameError(255)
                elif rtype == self._RESPONSE_NO_FRAME:
                    response = "no"
            del self._outstanding[seq], event, messages
            if command.response:
                # Construct response and return it
                if response == "no":
                    return command.response(None)
                return command.response(response)

    async def _bus_watch(self):
        # Why is this a task, and not just run from _handle_read()?
        # It's so that when we see a forward frame on the bus that
        # didn't originate with us, we can apply a timeout after which
        # if we don't see another related frame (either a repeated
        # config command forward frame, or a backward frame) we can
        # assume there wasn't one.

        # Command awaiting repeat or reply
        current_command = None
        devicetype = 0

        while True:
            # Wait for data
            if len(self._bus_watch_data) == 0:
                if current_command:
                    self._log.debug("Bus watch waiting with timeout")
                    await asyncio.wait_for(self._bus_watch_data_available.wait(), 0.2)
                else:
                    self._log.debug("Bus watch waiting for data, no timeout")
                    await self._bus_watch_data_available.wait()
                self._bus_watch_data_available.clear()

            # Figure out why we've woken up
            if len(self._bus_watch_data) == 0:
                self._log.debug("bus_watch timeout")
                timeout = True
            else:
                timeout = False
                message = self._bus_watch_data.pop(0)
                self._log.debug("bus_watch message %s", _hex(message[0:9]))
                origin, rtype, raw_frame, interval, seq = self._resptmpl.unpack(message)
                if origin not in (self._MODE_OBSERVE, self._MODE_RESPONSE):
                    self._log.debug("bus_watch: unexpected packet mode, ignoring")
                    continue
                if rtype == self._RESPONSE_FORWARD_FRAME:
                    frame = dali.frame.ForwardFrame(16, raw_frame)
                elif rtype == self._RESPONSE_BACKWARD_FRAME:
                    frame = dali.frame.BackwardFrame(raw_frame)
                elif rtype == self._RESPONSE_NO_FRAME:
                    frame = "no"
                elif rtype == self._RESPONSE_BUS_STATUS \
                     and message[5] == self._BUS_STATUS_FRAMING_ERROR:
                    frame = dali.frame.BackwardFrameError(255)
                else:
                    # Probably a bus status message other than framing error
                    self._log.debug("bus_watch: ignoring packet")
                    continue

            # Resolve the current_command before considering anything else.
            if current_command:
                # current_command will be a config command or a
                # command that expects a response.  It cannot be
                # EnableDeviceType()
                if current_command.sendtwice:
                    # We are waiting for a repeat of the command
                    if timeout:
                        # We didn't get it: report a failed command
                        self._log.debug("Failed sendtwice command: %s", current_command)
                        self.bus_traffic._invoke(current_command, None, True)
                        current_command = None
                        continue
                    elif isinstance(frame, dali.frame.ForwardFrame):
                        # If frame matches command, it's a valid config command
                        if current_command.frame == frame:
                            self._log.debug("Config command: %s", current_command)
                            self.bus_traffic._invoke(current_command, None, False)
                            current_command = None
                            continue
                        else:
                            self._log.debug("Failed config command (second frame didn't match): %s", current_comment)
                            self.bus_traffic._invoke(current_command, None, True)
                            current_command = None
                            # Fall through to continue processing frame
                    elif isinstance(frame, dali.frame.BackwardFrame):
                        # Error: config commands don't get backward frames.
                        self._log.debug("Failed config command %s with backward frame",
                                        current_command)
                        self.bus_traffic._invoke(current_command, None, True)
                        current_command = None
                    else:
                        self._log.debug("Unexpected response waiting for retransmit of config command")
                elif current_command.response:
                    # We are waiting for a response
                    if timeout or frame == "no":
                        # The response is "No".
                        self._log.debug("Command %s response \'No\'", current_command)
                        self.bus_traffic._invoke(
                            current_command, current_command.response(None), False)
                        current_command = None
                        continue
                    elif isinstance(frame, dali.frame.BackwardFrame):
                        # There's a response
                        self._log.debug("Command %s response %s",
                                        current_command, current_command.response(frame))
                        self.bus_traffic._invoke(
                            current_command, current_command.response(frame), False)
                        current_command = None
                        continue
                    else:
                        # The response is "No" and we have a new frame to deal with;
                        # fall through to process it
                        self._log.debug("Command %s response \'No\' (on new frame)",
                                        current_command)
                        self.bus_traffic._invoke(
                            current_command, current_command.response(None), False)
                        current_command = None

            # If we reach here, there is no current_command and there
            # may still be a frame to process.
            assert current_command == None
            if timeout:
                pass
            elif isinstance(frame, dali.frame.ForwardFrame):
                command = dali.command.from_frame(frame, devicetype=devicetype)
                devicetype = 0
                if command.sendtwice or command.response:
                    # We need more information.  Stash the command and wait.
                    current_command = command
                else:
                    # We're good.  Report it.
                    self._log.debug("Command %s, immediate", command)
                    self.bus_traffic._invoke(command, None, False)
                if isinstance(command, EnableDeviceType):
                    devicetype = command.param
                    self._log.debug("remembering device type %s", devicetype)
            elif isinstance(frame, dali.frame.BackwardFrame):
                self._log.debug("Unexpected backward frame %s", frame)

    def _handle_read(self, data):
        self._log.debug("_handle_read %s", _hex(data[0:9]))
        if data[0] == self._MODE_INFO:
            # Response to initialisation command
            if not self.firmware_version:
                self.firmware_version = f"{data[3]}.{data[4]}"
                # Now read the serial number
                os.write(self._f, self._cmd(
                    tridonic._CMD_INIT, tridonic._CMD_INIT_READSERIAL))
            elif not self.serial:
                self.serial = _hex(data[1:5])
                self.connected.set()
                self._bus_watch_task = asyncio.ensure_future(
                    self._bus_watch(), loop=self.loop)
            else:
                self._log.debug("Unsolicited init command response")

        elif data[0] == self._MODE_OBSERVE:
            # Something happened that we didn't initiate with a command
            self._bus_watch_data.append(data)
            self._bus_watch_data_available.set()

        elif data[0] == self._MODE_RESPONSE:
            self._bus_watch_data.append(data)
            self._bus_watch_data_available.set()
            seq = data[8]
            # The Tridonic DALI USB has a firmware bug.  When it
            # observes a frame on the bus, not generated by itself,
            # that matches the most recent frame it transmitted, it
            # reports it as if it had transmitted it itself.  We
            # ignore this - the sequence number will have been removed
            # from self._outstanding.
            if seq in self._outstanding:
                event, messages = self._outstanding[seq]
                messages.append(data)
                event.set()
                del event, messages

        else:
            self._log.debug("Unknown response mode %x", data[0])

    def _shutdown_device(self):
        # All outstanding commands need to be woken up and told they've failed
        for event, messages in self._outstanding.values():
            messages.append("fail")
            event.set()
        self._outstanding_values = {}
        # Cancel the bus watch task
        if self._bus_watch_task is not None:
            self._bus_watch_task.cancel()
            self._bus_watch_task = None
        self._bus_watch_data_available.clear()
        self._bus_watch_data = []
        # Clear these so that we won't get confused when we reconnect
        self.firmware_version = None
        self.serial = None

    @staticmethod
    def _cmd(cmd, serial, flags=0, ftype=0, frame=bytes(), dtr0=0):
        """Return 64 bytes for the specified command
        """
        return tridonic._cmdtmpl.pack(cmd, serial, flags, ftype, frame, dtr0)

class hasseb(hid):
    """hasseb DALI Master based on NXP LPC11xx_LPC13xx

    This device doesn't support listening to the DALI bus for frames
    transmitted by other masters.  We only report our own frames and
    responses on the bus_traffic callback.

    It contains an internal table of commands that produce responses.
    This table doesn't cover device types other than zero.  If you
    send a command it doesn't know that expects a response, the driver
    will deadlock.
    """
    _cmdtmpl = struct.Struct("BB")
    _NO_DATA_AVAILABLE = 0
    _NO_ANSWER = 1
    _OK = 2
    _INVALID_ANSWER = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = self._log.getChild("hasseb")
        self._command_lock = asyncio.Lock(loop=self.loop)
        self._response_available = asyncio.Event(loop=self.loop)
        self._response = None

    async def _send_raw(self, command):
        frame = command.frame
        if len(frame) != 16:
            raise UnsupportedFrameTypeError
        await self.connected.wait()
        async with self._command_lock:
            times = 2 if command.sendtwice else 1
            for rep in range(times):
                os.write(self._f, frame.pack_len(2))
            # Earlier commands may have left a response available that
            # we need to ignore.  We're only interested in responses
            # that become available in the future.
            self._response_available.clear()
            response = None
            if command.response:
                # The hasseb device appears to have an internal table
                # of which commands require responses.  If a command
                # does not require a response, it won't reply to us at
                # all.  Only wait for a reply if one is needed.
                #
                # NB there is NO WAY that this can be reliable: it
                # won't understand commands from IEC-62386 part 202,
                # for example.
                await self._response_available.wait()
                self._response_available.clear()
                if self._response == "fail":
                    raise CommunicationError
                elif self._response[0] == self._NO_ANSWER:
                    response = command.response(None)
                elif self._response[0] == self._OK:
                    response = command.response(dali.frame.BackwardFrame(self._response[1]))
                elif self._response[0] == self._INVALID_ANSWER:
                    response = command._response(dali.frame.BackwardFrameError(
                        self._response[1]))
                else:
                    self._log.debug("Unknown response code %x", self._response[0])

            self.bus_traffic._invoke(command, response, False)
            return response

    def _handle_read(self, data):
        # Response should be two bytes.  First byte is status, second
        # byte is optional response data.  The hasseb appears to send
        # "NO DATA AVAILABLE" reports continuously when it is idle.
        if data[0] != self._NO_DATA_AVAILABLE:
            self._response = data
            self._response_available.set()

    def _shutdown_device(self):
        # If there's a command in progress, tell it it's failed
        self._response = "fail"
        self._response_available.set()
