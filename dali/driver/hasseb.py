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


HASSEB_USB_VENDOR = 0x04cc
HASSEB_USB_PRODUCT = 0x0802

HASSEB_DRIVER_NO_DATA_AVAILABLE = 0
HASSEB_DRIVER_NO_ANSWER = 1
HASSEB_DRIVER_OK = 2
HASSEB_DRIVER_INVALID_ANSWER = 3

class HassebDALIUSBNoDataAvailable(object):
    def __repr__(self):
        return 'NO DATA AVAILABLE'

    __str__ = __repr__

class HassebDALIUSBNoAnswer(object):
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
       This driver is FAKE, since Hasseb does NOT support async communication.
    """
    _pending = None

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.backend = USBListener(
            self,
            HASSEB_USB_VENDOR,
            HASSEB_USB_PRODUCT,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )

    def send(self, command, callback=None, **kw):
        data = self.construct(command)
        if command.response is not None:
            self._pending = command, callback, kw
        else:
            self._pending = None
        self.backend.write(data)

    def receive(self, data):
        frame = self.extract(data)
        if isinstance(frame, HassebDALIUSBNoDataAvailable):
            return
        elif isinstance(frame, BackwardFrame):
            if self._pending:
                command, callback, kw = self._pending
                callback(command.response(frame), **kw)
            else:
                logger.error("Received frame for no pending command")
        else:
            logger.error("Received frame is not BackwardFrame")


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
