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

from dali.gear.general import Compare
from dali.gear.general import Initialise
from dali.gear.general import Randomise
from dali.gear.general import SetSearchAddrH
from dali.gear.general import SetSearchAddrL
from dali.gear.general import SetSearchAddrM
from dali.gear.general import Terminate
from dali.gear.general import Withdraw

import time

import hidapi

hidapi.hid_init()

HASSEB_USB_VENDOR = 0x04cc
HASSEB_USB_PRODUCT = 0x0802

HASSEB_DRIVER_NO_DATA_AVAILABLE = 0
HASSEB_DRIVER_NO_ANSWER = 1
HASSEB_DRIVER_OK = 2
HASSEB_DRIVER_INVALID_ANSWER = 3

class HassebDALIUSBNoDataAvailable:
    def __repr__(self):
        return 'NO DATA AVAILABLE'

    __str__ = __repr__

class HassebDALIUSBNoAnswer:
    def __repr__(self):
        return 'NO_ANSWER'

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
        self.logger.error("Invalid Frame")
        return None


class SyncHassebDALIUSBDriver(HassebDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
    """

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.backend = USBBackend(
            HASSEB_USB_VENDOR,
            HASSEB_USB_PRODUCT,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )

    def send(self, command, timeout=2000):
        self.backend.write(self.construct(command))
        frame = None
        backoff = 0.010

        if command.response is not None:
            for i in range(7):
                frame = self.extract(self.backend.read(timeout=timeout))
                if isinstance(frame, HassebDALIUSBNoAnswer):
                    self.backend.write(self.construct(command))
                if isinstance(frame, BackwardFrame):
                    if command.response:
                        return command.response(frame)
                    return frame
                backoff += backoff
                sleep(backoff)
            raise MissingResponse()
        return None


class AsyncHassebDALIUSBDriver(HassebDALIUSBDriver, AsyncDALIDriver):
    """Asynchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
    """
    _pending = None
    _response_message = None
    send_message = None

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.device = hidapi.hid_open(1228, 2050, None)

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
        self.send(command, callback=self._response_handler)
        self.wait_for_response()
        return self._response_message

    def receive(self):
        data = hidapi.hid_read(self.device, 2)
        frame = self.extract(data)
        if isinstance(frame, HassebDALIUSBNoDataAvailable):
            return
        elif isinstance(frame, BackwardFrame):
            if self._pending:
                command, callback, kw = self._pending
                callback(command.response(frame), **kw)
            else:
                self.logger.error("Received frame for no pending command")
        else:
            self.logger.error("Received frame is not BackwardFrame")
        return data

    def _response_handler(self, frame):
        """Response message handler

        """
        self._response_message = frame
        self._pending = None

    def wait_for_response(self):
        """Wait for response message. Timeout 200 ms.

        """
        for i in range(200):
            if not self._pending:
                return
            else:
                time.sleep(0.001)

    def set_search_addr(self, addr):
        self.send(SetSearchAddrH((addr >> 16) & 0xff))
        self.send(SetSearchAddrM((addr >> 8) & 0xff))
        self.send(SetSearchAddrL(addr & 0xff))

    def find_next(self, low, high):
        """Find the ballast with the lowest random address.  The caller
        guarantees that there are no ballasts with an address lower than
        'low'.

        """
        print("Searching from {} to {}...".format(low, high))
        if low == high:
            self.set_search_addr(low)
            response = self.send(Compare())

            if response != None:
                print("Found ballast at {}; withdrawing it...".format(low))
                self.send(Withdraw())
                return low
            return None

        self.set_search_addr(high)
        response = self.send_sync(Compare())

        if response != None:
            midpoint = (low + high) // 2
            return self.find_next(low, midpoint) or self.find_next(midpoint + 1, high)

    def find_ballasts(self):
        _ballasts = []

        self.send(Terminate())
        self.send(Initialise(broadcast=True, address=None))
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
