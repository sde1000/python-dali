"""Driver implementation for Quad-DALI-USB-Interface with integrated DALI-PSU

Contains four [EFM8-DALI-UART-Bridge] modules and one Silabs CP2108.

[EFM8-DALI-UART-Bridge]: https://git.rwth-aachen.de/Ferdinand.Keil/efm8-dali-uart-bridge
"""

import logging
import struct
from time import sleep, perf_counter
import serial

from dali.driver.base import DALIDriver
from dali.driver.base import SyncDALIDriver
from dali.driver.base import Backend
from dali.frame import BackwardFrame

class QuadDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Quad-DALI-USB-Interface.

    This code borrows from the HassebDALIUSBDriver.
    """

    def construct(self, command):
        data = None

        if len(command.frame) == 16:
            address, command = command.frame.as_byte_sequence
            data = struct.pack('BB', address, command)
        elif len(command.frame) == 24:
            raise ValueError('24 Bit frames are not supported (yet)')
        else:
            raise ValueError(f'unknown frame length: {len(command.frame)}')

        return data

    def extract(self, data):
        if len(data) == 1:
            return BackwardFrame(data[0])
        return None

class SerialBackend(Backend):
    """``Backend`` implementation for Quad-DALI-USB-Interface. Uses serial connection."""

    """Open connection to the DALI interface.

    @param port: valid serial port (e.g. /dev/ttyUSB0 or COM1)
    @param baudrate: serial baudrate; default is 115.200
    @param bytesize: number of bits per byte; default is 8
    @param parity: configures parity bit; default is none
    @param stopbits: number of stopbits per byte; default is one"""
    def __init__(self, port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE):
        self._serial = serial.Serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits)

        # for compatibility with older pyserial versions
        # background: the methods for flushing the in-/out-buffer were renamed in v3.0
        if serial.VERSION.split('.')[0] == '2':
            self._reset_input_buffer = self._serial.flushInput
            self._reset_output_buffer = self._serial.flushOutput
        elif serial.VERSION.split('.')[0] == '3':
            self._reset_input_buffer = self._serial.reset_input_buffer
            self._reset_output_buffer = self._serial.reset_output_buffer
        else:
            raise RuntimeError(f'pyserial={serial.VERSION} is not supported')

        # flush all buffers to remove old data before checking the port
        self._reset_output_buffer()
        sleep(0.050) # just a precaution if the previous command causes data to be sent
        self._reset_input_buffer()

    """Read data from the DALI interface.

    @param timeout: read timeout in seconds; set to 0 or None to disable
    @return data read from the interface"""
    def read(self, timeout=None):
        # internal read timeout is set to 10 ms to increase responsiveness
        self._serial.timeout = 0.010
        # to compensate for the short read timeout and to use the timeout argument, the read is repeated until
        # more time than specified has elapsed
        start = perf_counter()
        while timeout and abs(start-perf_counter()) < timeout:
            data = self._serial.read(1)
            if len(data) > 0:
                break
        # DALI backframes are max. 1 Byte long, so that is all that is needed
        if len(data) <= 1:
            return data
        else:
            raise ValueError(f'read method returned too many bytes ({len(data)})')

    """Write data to the DALI interface.

    @param data: data to write
    @return number of bytes written"""
    def write(self, data):
        bytes_written = self._serial.write(data)
        self._serial.flush()
        return bytes_written

    """Close connection to the DALI interface."""
    def close(self):
        self._serial.close()

"""Specifies the firmware version expected by this driver."""
REQUIRED_FIRMWARE_VERSION = 0o104

class SyncQuadDALIUSBDriver(QuadDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Quad-DALI-USB-Interface.
    """

    def __init__(self, port=None):
        self.backend = SerialBackend(port=port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE)

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

    def send(self, command, timeout=1000):
        # construct & send forward frame
        self.backend.write(self.construct(command))
        # wait until the forward frame has finished sending
        # 38 Te (sending) + 22 Te (backoff) = 60 Te ~= 25 ms
        sleep(0.050)

        if command.response is not None:
            # timeout 10 ms is approx. 22 Te as per 62386-102 8.9
            response = self.backend.read(timeout=timeout/1000.)
            if response is None:
                #print('response was none') # XXX
                return command.response(self.extract(bytes([0])))
            else:
                #print(f'response was retrieved: {response}') # XXX
                return command.response(self.extract(response))

if __name__ == '__main__':
    import argparse
    from dali.address import Broadcast, Short
    from dali.gear.general import RecallMinLevel, RecallMaxLevel, EnableDeviceType
    from dali.gear.led import QueryGearType

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='repeat query n times', type=int, default=1)
    parser.add_argument('port', help='serial port to connect to', type=str)
    args = parser.parse_args()

    iface = SyncQuadDALIUSBDriver(port=args.port)

    for i in range(args.n):
        print(f'Run #{i+1}')
        print('max level... ', end='')
        iface.send(RecallMaxLevel(Short(0)))
        sleep(0.3)
        print('min level...')
        iface.send(RecallMinLevel(Broadcast()))
        sleep(0.2)
        print()

    iface.backend.close()