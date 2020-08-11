import logging
import struct
from time import sleep

from dali.driver.base import AsyncDALIDriver
from dali.driver.base import DALIDriver
from dali.driver.base import SyncDALIDriver
from dali.frame import BackwardFrame
from dali.frame import BackwardFrameError

import dali.gear.general as gear

import time

import hidapi

hidapi.hid_init()

HASSEB_USB_VENDOR = 0x04cc
HASSEB_USB_PRODUCT = 0x0802

HASSEB_READ_FIRMWARE_VERSION    = 0x02
HASSEB_CONFIGURE_DEVICE         = 0x05
HASSEB_DALI_FRAME               = 0X07

HASSEB_DRIVER_NO_DATA_AVAILABLE = 0
HASSEB_DRIVER_NO_ANSWER = 1
HASSEB_DRIVER_OK = 2
HASSEB_DRIVER_INVALID_ANSWER = 3
HASSEB_DRIVER_TOO_EARLY = 4
HASSEB_DRIVER_SNIFFER_BYTE = 5
HASSEB_DRIVER_SNIFFER_BYTE_ERROR = 6


class HassebDALIUSBNoDataAvailable:
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
    device_found = None
    logger = logging.getLogger('HassebDALIUSBDriver')
    sn = 0
    send_message = None
    _pending = None
    _response_message = None

    def __init__(self):
        try:
            self.device = hidapi.hid_open(HASSEB_USB_VENDOR, HASSEB_USB_PRODUCT, None)
            self.device_found = 1
        except:
            self.device_found = None

    def wait_for_response(self):
        raise NotImplementedError()

    def construct(self, command):
        # sequence number
        self.sn = self.sn+1
        if self.sn > 255:
            self.sn = 1
        frame_length = 16
        if command.is_query:
            expect_reply = 1
        else:
            expect_reply = 0
        transmitter_settling_time = 0
        if command.is_config:
            send_twice = 10 # 10 ms delay between messages
        else:
            send_twice = 0
        frame = command.frame.as_byte_sequence
        byte_a, byte_b = frame
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_DALI_FRAME, self.sn,
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
            response_status = data[3]
            if response_status == HASSEB_DRIVER_NO_ANSWER:
                # 1: "No Answer"
                self.logger.debug("No Answer")
                return HassebDALIUSBNoAnswer()
            elif response_status == HASSEB_DRIVER_OK and data[4] == 1:
                # 2: "OK"
                return BackwardFrame(data[5])
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

    def send(self, command):
        time.sleep(0.02)    # a delay between sent messages need to be at lest 22*417 µs
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
        data = hidapi.hid_read(self.device, 10)
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
        return data

    def readFirmwareVersion(self):
        self.sn = self.sn + 1
        if self.sn > 255:
            self.sn = 1
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_READ_FIRMWARE_VERSION,
                            self.sn, 0, 0, 0, 0, 0, 0, 0)
        hidapi.hid_write(self.device, data)
        data = hidapi.hid_read(self.device, 10)
        for i in range(0,100):
            if len(data)==10:
                if data[1] != HASSEB_READ_FIRMWARE_VERSION:
                    data = hidapi.hid_read(self.device, 10)
                else:
                    return f"{data[3]}.{data[4]}"
            else:
                data = hidapi.hid_read(self.device, 10)
        return f"VERSION_ERROR"

    def enableSniffing(self):
        self.sn = self.sn + 1
        if self.sn > 255:
            self.sn = 1
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_CONFIGURE_DEVICE,
                            self.sn, 0x01, 0, 0, 0, 0, 0, 0)
        hidapi.hid_write(self.device, data)

    def disableSniffing(self):
        self.sn = self.sn + 1
        if self.sn > 255:
            self.sn = 1
        data = struct.pack('BBBBBBBBBB', 0xAA, HASSEB_CONFIGURE_DEVICE,
                            self.sn, 0, 0, 0, 0, 0, 0, 0)
        hidapi.hid_write(self.device, data)


class AsyncHassebDALIUSBDriver(HassebDALIUSBDriver, AsyncDALIDriver):
    """Asynchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
       Using asynchronous driver requires a separate thread for receiving
       DALI messages. receive() function needs to be called continously
       from the thread. You can also define an event processor function which
       is called when wating for a response to prevent hangin of the program.
    """

    #def __init__(self, processEvents):
    #    self._processEvents = processEvents

    def setEventHandler(self, processEvents):
        self._processEvents = processEvents

    def wait_for_response(self):
        """Wait for response message. Timeout 2000 ms.
        """
        for i in range(200):
            if not self._pending:
                return
            else:
                self._processEvents()
                time.sleep(0.01)


class SyncHassebDALIUSBDriver(HassebDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
    """

    def wait_for_response(self):
        """Wait for response message.
        """
        for i in range(200):
            if not self._pending:
                return
            else:
                self.receive()
