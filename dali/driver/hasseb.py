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
#from dali.gear.general import Initialise
#from dali.gear.general import Randomise
#from dali.gear.general import SetSearchAddrH
#from dali.gear.general import SetSearchAddrL
#from dali.gear.general import SetSearchAddrM
#from dali.gear.general import Terminate
#from dali.gear.general import Withdraw

from PyQt5.QtWidgets import QApplication

import time

import hidapi

hidapi.hid_init()

HASSEB_USB_VENDOR = 0x04cc
HASSEB_USB_PRODUCT = 0x0802

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

class HassebDALIUSBNoAnswer:
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
        expect_reply = 0
        transmitter_settling_time = 0
        send_twice_settling_time  = 0
        frame = command.frame.as_byte_sequence
        byte_a, byte_b = frame
        data = struct.pack('BBBBBBBBBB', 7, sn,
                           frame_length, expect_reply,
                           transmitter_settling_time, send_twice_settling_time,
                           byte_a, byte_b,
                           0, 0)
        return data

    def extract(self, data):
        if data == None:
            return None
        if len(data) >= 2:
            response_status = data[0]
            if response_status == HASSEB_DRIVER_NO_DATA_AVAILABLE:
                # 0: "No Data Available"
                self.logger.debug("No Data Available")
                return HassebDALIUSBNoDataAvailable()
            elif response_status == HASSEB_DRIVER_NO_ANSWER:
                # 1: "No Answer"
                self.logger.debug("No Answer")
                return HassebDALIUSBNoAnswer()
            elif response_status == HASSEB_DRIVER_OK:
                # 2: "OK"
                return BackwardFrame(data[1])
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


class AsyncHassebDALIUSBDriver(HassebDALIUSBDriver, AsyncDALIDriver):
    """Asynchronous ``DALIDriver`` implementation for Hasseb DALI USB device.

    """
    device_found = None

    _pending = None
    _response_message = None
    send_message = None

    ballast_id = None
    ballast_short_address = None
    ballast_type = None

    _short_address = 0

    def __init__(self):
        try:
            self.device = hidapi.hid_open(1228, 2050, None)
            self.device_found = 1
        except:
            print("No USB DALI Master device found")
            self.device_found = None

    def send(self, command, callback=None, **kw):
        data = self.construct(command)
        self.send_message = struct.pack('BB', data[6], data[7])
        if command.response is not None:
            self._pending = command, callback, kw
            self._response_message = None
        else:
            self._pending = None
        hidapi.hid_write(self.device, data)

    def send_sync(self, command):
        self._response_message = None
        self.send(command)
        self.wait_for_response()
        return self._response_message

    def receive(self):
        data = hidapi.hid_read(self.device, 2)
        frame = self.extract(data)
        if isinstance(frame, HassebDALIUSBNoDataAvailable):
            return
        elif isinstance(frame, BackwardFrame) or isinstance(frame, HassebDALIUSBNoAnswer):
            if self._pending:
                self._response_message = data
                self._pending = None
            else:
                self.logger.error("Received frame for no pending command")
        return data

    def wait_for_response(self):
        """Wait for response message. Timeout 2000 ms.

        """
        for i in range(40):
            if not self._pending:
                return
            else:
                QApplication.processEvents()
                time.sleep(0.05)

    def set_search_addr(self, addr):
        self.send(SetSearchAddrH((addr >> 16) & 0xff))
        self.send(SetSearchAddrM((addr >> 8) & 0xff))
        self.send(SetSearchAddrL(addr & 0xff))

    def find_next(self, low, high):
        """Find the ballast with the lowest random address. The caller
        guarantees that there are no ballasts with an address lower than
        'low'.

        """
        QApplication.processEvents()
        print("Searching from {} to {}...".format(low, high))
        if low == high:
            self.set_search_addr(low)
            response = self.send_sync(Compare())

            if self.extract(response) == BackwardFrame(255):
                print("Found ballast at {}; withdrawing it...".format(low))
                self.send(Withdraw())
                self.send(ProgramShortAddress(self._short_address))
                response = self.send_sync(QueryDeviceType(self._short_address))
                try:
                    self.ballast_type = QueryDeviceTypeResponse(self.extract(response))
                except:
                    self.ballast_type = "NaN"
                if self.extract(self.send_sync(VerifyShortAddress(self._short_address))) == BackwardFrame(255):
                    self.ballast_short_address = self._short_address
                else:
                    self.ballast_short_address = "NaN"
                self.ballast_id = low
                QApplication.processEvents()
                return low
            return None

        self.set_search_addr(high)
        response = self.send_sync(Compare())

        if self.extract(response) == BackwardFrame(255):
            midpoint = (low + high) // 2
            return self.find_next(low, midpoint) or self.find_next(midpoint + 1, high)

    def find_ballasts(self, randomise=1):
        _ballasts = []
        self._short_address = 0
        self.ballast_id = None

        self.send(Terminate())
        self.send(Initialise(broadcast=True, address=None))
        if randomise:
            self.send(Randomise())
            time.sleep(0.1)  # Randomise may take up to 100ms

        low = 0
        high = 0xffffff
        while low is not None:
            low = self.find_next(low, high)
            if low is not None:
                _ballasts.append(low)
                low += 1

        self.send(Terminate())
        return _ballasts


#if __name__ == '__main__':
