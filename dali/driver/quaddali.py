"""Driver implementation for Quad-DALI-USB-Interface with integrated DALI-PSU

Contains four [EFM8-DALI-UART-Bridge] modules and one Silabs CP2108.

[EFM8-DALI-UART-Bridge]: https://git.rwth-aachen.de/Ferdinand.Keil/efm8-dali-uart-bridge
"""

import asyncio
from time import sleep
import serial
from abc import ABC, abstractmethod

from dali.driver.base import SyncDALIDriver
from dali.driver.base import SerialBackend
from dali.frame import BackwardFrame
from dali.sequences import progress as seq_progress
from dali.sequences import sleep as seq_sleep

def construct(command):
    """Returns a sequence of bytes representing the given command to be sent to the interface.""" 
    data = None

    if len(command.frame) == 16:
        data = command.frame.pack
    elif len(command.frame) == 24:
        raise ValueError('24 Bit frames are not supported (yet)')
    else:
        raise ValueError(f'unknown frame length: {len(command.frame)}')

    return data

def extract(data):
    """Takes data from the interface and formats the response."""
    if len(data) == 1:
        return BackwardFrame(data[0])
    return None

"""Specifies the firmware version expected by this driver."""
REQUIRED_FIRMWARE_VERSION = 0o104

class QuadDALIUSBDriver(ABC):
    """Abstract base class for drivers supporting the Quad-DALI-USB-Interface.
    """

    def __init__(self, port):
        """Create a driver instance to communicate with the Quad-DALI-USB-Interface connected to the given port."""
        self._port = port

    @abstractmethod
    def connect(self):
        """Open the connection the interface."""
        pass

    @abstractmethod
    def send(self, command):
        """Send a given command over the bus. Waits for a response until timeout occurs.

        @param command: command to send
        @return Response coming from the bus (empty if none)
        """
        pass

    @abstractmethod
    def run_sequence(self, seq, progress=None):
        """Runs the given command sequence.

        @param seq: command sequence
        @param progress: consumer for the sequence's progress reports
        @return Response for the command sequence (default is None)
        """
        pass

class SyncQuadDALIUSBDriver(QuadDALIUSBDriver):
    """Synchronous dali driver for the Quad-DALI-USB-Interface.
    """

    def connect(self):
        self.backend = SerialBackend(port=self._port, baudrate=115200, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

        # retrieve firmware version - ensures we're talking to the correct port
        self.backend.write(bytes.fromhex('facade00'))
        firmware_version = self.backend.read(timeout=2.000)
        try:
            self.firmware_version = f'{firmware_version[0]:o}'
        except (IndexError, ValueError, TypeError):
            print(firmware_version)
            self.backend.close()
            raise RuntimeError('unsupported device - did not return serial number') from None

        # ensure that the firmware version is supported by this driver
        if firmware_version[0] < REQUIRED_FIRMWARE_VERSION:
            self.backend.close()
            raise RuntimeError(f'unsupported device - firmware version too old ({self.firmware_version}<{REQUIRED_FIRMWARE_VERSION:o})')

    def send(self, command):
        # construct & send forward frame
        self.backend.write(construct(command))
        # wait until the forward frame has finished sending
        # 38 Te (sending) + 22 Te (backoff) = 60 Te ~= 25 ms
        sleep(0.050)

        if command.response is not None:
            # timeout 10 ms is approx. 22 Te as per 62386-102 8.9
            # the default USB polling interval is 10 ms
            # timeout = t_dali + t_usb = 20 ms
            response = self.backend.read(timeout=0.020)
            # expects a DALI backframe, so fails if more data is received
            if len(response) > 1:
                raise ValueError('bus returned more than one byte as response')
            elif len(response) == 1:
                return command.response(extract(response))
            else:
                return command.response(extract(bytes([0])))

    def run_sequence(self, seq, progress=None):
        response = None
        try:
            while True:
                try:
                    cmd = seq.send(response)
                except StopIteration as r:
                    return r.value
                response = None
                if isinstance(cmd, seq_sleep):
                    sleep(cmd.delay)
                elif isinstance(cmd, seq_progress):
                    if progress:
                        progress(cmd)
                else:
                    if cmd.devicetype != 0:
                        self.send(EnableDeviceType(cmd.devicetype))
                    response = self.send(cmd)
        finally:
            seq.close()
        return None

class AsyncQuadDALIUSBDriver(QuadDALIUSBDriver):
    """Asynchronous dali driver for the Quad-DALI-USB-Interface.
    """

    class _SerialProtocol(asyncio.Protocol):
        """This Protocol handles the asynchronous serial communication.
        pyserial-asyncio calls the methods herein like callbacks. asyncio primitives are used so that the parent
        can interface with the Protocol asynchronously.
        """

        def __init__(self):
            self.connected = asyncio.Event()
            self.can_write = asyncio.Event()

        def connection_made(self, transport):
            self.connected.set()
            self.can_write.set()

        async def data_received(self, data):
            """This method will be monkey patched by the parent."""
            pass

        def pause_writing(self):
            self.can_write.clear()

        def resume_writing(self):
            self.can_write.set()
    
    async def _data_received_cb(self, data):
        # data is stored bytewise, as DALI responses are only one Byte
        for byte in data:
            asyncio.ensure_future(self._received_data.put(byte))

    def __init__(self, port):
        # import serial_asyncio class late, so that the driver is usable without them
        try:
            import serial_asyncio
        except ImportError:
            raise RuntimeError('{} requires serial_asyncio but it is not installed'.format(self.__class__.__name__))

        self._received_data = asyncio.Queue()
        self._bus_lock = asyncio.Lock()
        # this creates a coroutine generator that will establish a connection once run
        self._connect = serial_asyncio.create_serial_connection(
            asyncio.get_event_loop(),
            self._SerialProtocol,
            port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE)

    async def connect(self):
        # runs the coroutine to create the connection
        self._transport, self._protocol = await self._connect
        self._protocol.data_received = self._data_received_cb
        await self._protocol.connected.wait()

    async def send(self, command):
        async with self._bus_lock:
            # wait if writing has been paused
            await self._protocol.can_write.wait()
            # construct & send forward frame
            self._transport.write(construct(command))
            # wait until the forward frame has finished sending
            # 38 Te (sending) + 22 Te (backoff) = 60 Te ~= 25 ms
            await asyncio.sleep(0.025)

            if command.response is not None:
                # timeout 10 ms is approx. 22 Te as per 62386-102 8.9
                # the default USB polling interval is 10 ms
                # timeout = t_dali + t_usb = 20 ms
                try:
                    response = await asyncio.wait_for(self._received_data.get(), 0.020)
                except TimeoutError:
                    return command.response(extract(bytes([0])))
                else:
                    return command.response(extract(response))

    async def run_sequence(self, seq, progress=None):
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
                        await self.send(EnableDeviceType(cmd.devicetype))
                    response = await self.send(cmd)
        finally:
            seq.close()
        return None

if __name__ == '__main__':
    import argparse
    from dali.address import Broadcast, Short
    from dali.gear.general import RecallMinLevel, RecallMaxLevel, EnableDeviceType
    from dali.gear.led import QueryGearType

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='repeat query n times', type=int, default=1)
    parser.add_argument('--async', help='use the asyncio library', action='store_true', dest='async_')
    parser.add_argument('port', help='serial port to connect to', type=str)
    args = parser.parse_args()

    if args.async_:
        async def main(args):
            iface = AsyncQuadDALIUSBDriver(port=args.port)
            await iface.connect()

            for i in range(args.n):
                print(f'Run #{i+1}')
                print('max level... ', end='')
                await iface.send(RecallMaxLevel(Short(0)))
                sleep(0.3)
                print('min level...')
                await iface.send(RecallMinLevel(Broadcast()))
                sleep(0.2)
                print()
        
        asyncio.run(main(args))
    else:
        iface = SyncQuadDALIUSBDriver(port=args.port)
        iface.connect()

        for i in range(args.n):
            print(f'Run #{i+1}')
            print('max level... ', end='')
            iface.send(RecallMaxLevel(Short(0)))
            sleep(0.3)
            print('min level...')
            iface.send(RecallMinLevel(Broadcast()))
            sleep(0.2)
            print()