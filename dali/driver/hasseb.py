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

    This code borrows from the HassebDALIUSBDriver.
    """
    logger = logging.getLogger('HassebDALIUSBDriver')

    def construct(self, command):
        frame = command.frame.as_byte_sequence
        byte_a, byte_b = frame
        data = struct.pack('BB', byte_a, byte_b)

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
        except:
            print("No USB DALI Master device found")

    def send(self, command, callback=None, **kw):
        data = self.construct(command)
        self.send_message = data
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
        """Wait for response message. Timeout 100 ms.

        """
        for i in range(60):
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
        """Find the ballast with the lowest random address.  The caller
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
                time.sleep(0.05)
                self.send(ProgramShortAddress(self._short_address))
                time.sleep(0.1)
                response = self.send_sync(QueryDeviceType(self._short_address))
                try:
                    self.ballast_type = QueryDeviceTypeResponse(self.extract(response))
                except:
                    self.ballast_type = "NaN"
                #if (self.send_sync(QueryShortAddress()) & 0x3f) == self._short_address:
                self.ballast_id = low
                if self.extract(self.send_sync(VerifyShortAddress(self._short_address))) == BackwardFrame(255):
                    self.ballast_short_address = self._short_address
                else:
                    self.ballast_short_address = "NaN"
                QApplication.processEvents()
                return low
            return None

        self.set_search_addr(high)
        response = self.send_sync(Compare())

        if self.extract(response) == BackwardFrame(255):
            midpoint = (low + high) // 2
            return self.find_next(low, midpoint) or self.find_next(midpoint + 1, high)

    def find_ballasts(self):
        _ballasts = []
        self._short_address = 0
        self.ballast_id = None

        self.send(Terminate())
        time.sleep(0.1)
        self.send(Initialise(broadcast=True, address=None))
        time.sleep(0.1)
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


def _test_async(logger, command):
    print('Test async driver')
    driver = AsyncHassebDALIUSBDriver()
    driver.logger = logger

    # async response callback
    def response_received(response):
        print('Response received: {}'.format(response))

    driver.send(command, callback=response_received)

    # exit callback
    def signal_handler(signal, frame):
        driver.backend.close()
        sys.exit(0)

    import signal
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C')
    signal.pause()


def _test_sync(logger, command):
    print('Test sync driver')
    driver = SyncHassebDALIUSBDriver()
    driver.logger = logger

    print('Response: {}'.format(driver.send(command)))
    driver.backend.close()


if __name__ == '__main__':
    """Usage: python tridonic.py sync|async address value."""
    from dali.gear.general import DAPC, QueryActualLevel
    import sys

    # setup console logging
    logger = logging.getLogger('HassebDALIDriver')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

    # command to send
    cmd = DAPC(int(sys.argv[2]), int(sys.argv[3]))

    # sync interface
    if sys.argv[1] == 'sync':
        _test_sync(logger, cmd)
    # async interface
    elif sys.argv[1] == 'async':
        _test_async(logger, cmd)
