import logging
import struct
from time import sleep
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

    def read(self, timeout=None):
        self._serial.timeout = timeout
        # DALI backframes are max. 1 Byte long, so that is all that is needed
        data = self._serial.read(1)
        #print(f'retrieved {len(data)} Bytes') # XXX
        if len(data) <= 1:
            return data
        else:
            raise ValueError(f'read method returned too many bytes ({len(data)})')

    def write(self, data):
        bytes_written = self._serial.write(data)
        self._serial.flush()
        return bytes_written

    def close(self):
        self._serial.close()

REQUIRED_FIRMWARE_VERSION = 0o104

class SyncQuadDALIUSBDriver(QuadDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Quad-DALI-USB-Interface.
    """

    def __init__(self, port=None):
        self.backend = SerialBackend(port=port, baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE)

        # retrieve firmware version - ensures we're talking to the correct port
        self.backend.write(bytes.fromhex('facade00'))
        firmware_version = self.backend.read(timeout=0.010)
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

    def send(self, command, timeout=2000):
        # construct & send forward frame
        self.backend.write(self.construct(command))
        # wait until the forward frame has finished sending
        # 38 Te (sending) + 22 Te (backoff) = 60 Te ~= 25 ms
        sleep(0.030)

        if command.response is not None:
            # timeout 10 ms is approx. 22 Te as per 62386-102 8.9
            response = self.backend.read(timeout=timeout/1000)
            if response is None:
                #print('response was none') # XXX
                return command.response(self.extract(bytes([0])))
            else:
                #print(f'response was retrieved: {response}') # XXX
                return command.response(self.extract(response))

if __name__ == '__main__':
    from dali.address import Broadcast, Short
    from dali.gear.general import RecallMinLevel, RecallMaxLevel, EnableDeviceType
    from dali.gear.led import QueryGearType

    iface = SyncQuadDALIUSBDriver(port='/dev/ttyS24')

    #for i in range(3):
    #    iface.send(RecallMaxLevel(Short(0)))
    #    sleep(0.1)
    #    iface.send(RecallMinLevel(Broadcast()))
    #    sleep(0.1)
    for i in range(100):
        iface.send(EnableDeviceType(6))
        resp = iface.send(QueryGearType(Short(0)))
        #print(resp)

    iface.backend.close()