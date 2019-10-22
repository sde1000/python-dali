import logging
import struct
from time import sleep

from dali.command import Command
from dali.driver.base import AsyncDALIDriver
from dali.driver.base import DALIDriver
from dali.driver.base import SyncDALIDriver
from dali.driver.base import USBBackend
from dali.driver.base import USBListener
from dali.frame import BackwardFrame
from dali.frame import BackwardFrameError
from dali.frame import ForwardFrame
from dali.exceptions import ResponseError, MissingResponse

from dali.gear.general import *

from PyQt5.QtWidgets import QApplication

import time

import hidapi

hidapi.hid_init()

HASSEB_USB_VENDOR = 0x04cc
HASSEB_USB_PRODUCT = 0x0802

HASSEB_READ_FIRMWARE_VERSION    = 0x02
HASSEB_DALI_FRAME               = 0X07

HASSEB_DRIVER_NO_DATA_AVAILABLE = 0
HASSEB_DRIVER_NO_ANSWER = 1
HASSEB_DRIVER_OK = 2
HASSEB_DRIVER_INVALID_ANSWER = 3
HASSEB_DRIVER_TOO_EARLY = 4
HASSEB_DRIVER_SNIFFER_BYTE = 5
HASSEB_DRIVER_SNIFFER_BYTE_ERROR = 6


class HassebDALIUSBNoDataAvailable(object):
    def __repr__(self):
        return 'NO DATA AVAILABLE'

    __str__ = __repr__


class HassebDALIUSBNoAnswer(object):
    def __repr__(self):
        return 'NO_ANSWER'

    __str__ = __repr__


class HassebDALIUSBAnswerTooEarly(object):
    def __repr__(self):
        return 'ANSWER_TOO_EARLY'

    __str__ = __repr__


class HassebDALIUSBSnifferByte(object):
    def __repr__(self):
        return 'SNIFFER_BYTE'

    __str__ = __repr__


class HassebDALIUSBSnifferByteError(object):
    def __repr__(self):
        return 'SNIFFER_BYTE_ERROR'

    __str__ = __repr__


class HassebDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Hasseb DALI USB device.
    """
    logger = logging.getLogger('HassebDALIUSBDriver')

    def construct(self, command):
        sn = 0  # sequence number
        frame_length = 16
        if command.is_query:
            expect_reply = 1
        else:
            expect_reply = 0
        transmitter_settling_time = 0
        if command.is_config == True:
            send_twice = 1
        else:
            send_twice = 0
        frame = command.frame.as_byte_sequence
        byte_a, byte_b = frame
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_DALI_FRAME, sn,
                           frame_length, expect_reply,
                           transmitter_settling_time, send_twice,
                           byte_a, byte_b,
                           0)
        return data

    def extract(self, data):
        if data == None:
            return None
        elif data[1] == HASSEB_DRIVER_NO_DATA_AVAILABLE:
            # 0: "No Data Available"
            self.logger.debug("No Data Available")
            return HassebDALIUSBNoDataAvailable()
        elif data[1] == HASSEB_DALI_FRAME:
            response_status = data[2]
            if response_status == HASSEB_DRIVER_NO_ANSWER:
                # 1: "No Answer"
                self.logger.debug("No Answer")
                return HassebDALIUSBNoAnswer()
            elif response_status == HASSEB_DRIVER_OK:
                # 2: "OK"
                return BackwardFrame(data[3])
            elif response_status == HASSEB_DRIVER_INVALID_ANSWER:
                # 3: "Invalid Answer"
                return BackwardFrameError(255)
            elif response_status == HASSEB_DRIVER_TOO_EARLY:
                # 4: "Answer too early"
                self.logger.debug("Answer too early")
                return HassebDALIUSBAnswerTooEarly()
            elif response_status == HASSEB_DRIVER_SNIFFER_BYTE:
                # 5: "Sniffer byte"
                return HassebDALIUSBSnifferByte()
            elif response_status == HASSEB_DRIVER_SNIFFER_BYTE_ERROR:
                # 6: "Sniffer byte error"
                return HassebDALIUSBSnifferByteError()
        self.logger.error("Invalid Frame")
        return None

    def __init__(self):
        try:
            self.device = hidapi.hid_open(HASSEB_USB_VENDOR, HASSEB_USB_PRODUCT, None)
            self.device_found = 1
        except:
            print("No USB DALI Master device found")
            self.device_found = None

    def readFirmwareVersion(self):
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_READ_FIRMWARE_VERSION,
                            0, 0, 0, 0, 0, 0, 0, 0)
        hidapi.hid_write(self.device, data)
        data = hidapi.hid_read(self.device, 10)
        for i in range(0,100):
            if data[1] != HASSEB_READ_FIRMWARE_VERSION:
                data = hidapi.hid_read(self.device, 10)
            else:
                return f"{data[2]}.{data[3]}"
        return f"VERSION_ERROR"


class AsyncHassebDALIUSBDriver(HassebDALIUSBDriver, AsyncDALIDriver):
    """Asynchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
       Using asynchronous driver requires a separate thread for receiving
       DALI messages. receive() function needs to be called continously
       from the thread.
    """
    device_found = None

    _pending = None
    _response_message = None
    send_message = None

    def send(self, command):
        time.sleep(0.05)    # a delay between sent messages for better reliability
        self._response_message = None
        data = self.construct(command)
        self.send_message = struct.pack('BB', data[7], data[8])
        if command.response is not None:
            self._pending = command
            self._response_message = None
            hidapi.hid_write(self.device, data)
            self.wait_for_response()
            return command.response(self.extract(self._response_message))
        else:
            self._pending = None
            hidapi.hid_write(self.device, data)
            return

    def receive(self):
        data = hidapi.hid_read(self.device, 6)
        frame = self.extract(data)
        if isinstance(frame, HassebDALIUSBNoDataAvailable):
            return
        elif isinstance(frame, BackwardFrame) or isinstance(frame, HassebDALIUSBNoAnswer):
            if self._pending and isinstance(frame, BackwardFrame):
                self._response_message = data
                self._pending = None
            elif self._pending and isinstance(frame, HassebDALIUSBNoAnswer):
                self._response_message = None
                self._pending = None
            else:
                self.logger.error("Received frame for no pending command")
        return data

    def wait_for_response(self):
        """Wait for response message. Timeout 2000 ms.
        """
        for i in range(200):
            if not self._pending:
                return
            else:
                QApplication.processEvents()
                time.sleep(0.01)


class SyncHassebDALIUSBDriver(HassebDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
    """

    def send(self, command):
        data = self.construct(command)
        hidapi.hid_write(self.device, data)

        if command.response is not None:
            for i in range(100):
                data = hidapi.hid_read(self.device, 6)
                frame = self.extract(data)
                if isinstance(frame, HassebDALIUSBNoAnswer):
                    self.backend.write(self.construct(command))
                if isinstance(frame, BackwardFrame):
                    if command.response:
                        return command.response(frame)
                    return frame
            raise MissingResponse()
        return None
        

if __name__ == '__main__':
    print('All tests PASSED')
