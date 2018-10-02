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
from time import sleep
import logging
import struct


DALI_USB_VENDOR = 0x04cc
DALI_USB_PRODUCT = 0x0802

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

HASSEB_NO_DATA_AVAILABLE = HassebDALIUSBNoDataAvailable()
HASSEB_NO_ANSWER = HassebDALIUSBNoAnswer()

class HassebDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Hasseb DALI USB device.
    
    This code borrows from the HassebDALIUSBDriver.
    """
    logger = logging.getLogger('HassebDALIUSBDriver')

    def construct(self, command):
        a, b = command.frame.as_byte_sequence
        data = struct.pack('BB',a,b)

        return data

    def extract(self, data):
        if len(data) >= 2:
            responseStatus = data[0]
            if responseStatus == HASSEB_DRIVER_NO_DATA_AVAILABLE:
                # 0: "No Data Available"
                self.logger.debug("No Data Available")
                return HASSEB_NO_DATA_AVAILABLE
            elif responseStatus == HASSEB_DRIVER_NO_ANSWER:
                # 1: "No Answer"
                self.logger.debug("No Answer")
                return HASSEB_NO_ANSWER
            elif responseStatus == HASSEB_DRIVER_OK:
                # 2: "OK"
                return BackwardFrame(data[1])
            elif responseStatus == HASSEB_DRIVER_INVALID_ANSWER:
                # 3: "Invalid Answer"
                return BackwardFrameError(255)

        self.logger.error("Invalid Frame")

class SyncHassebDALIUSBDriver(HassebDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Hasseb DALI USB device.
    """

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.backend = USBBackend(
            DALI_USB_VENDOR,
            DALI_USB_PRODUCT,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )

    def send(self, command, timeout=2000):
        self.backend.write(self.construct(command))
        frame = None
        backoff = 0.010

        if command.response is not None:
            for i in range(10):
                frame = self.extract(self.backend.read(timeout=timeout))
                if isinstance(frame, HassebDALIUSBNoAnswer):
                    self.backend.write(self.construct(command))
                if isinstance(frame, BackwardFrame):
                    if command.response:
                        return command.response(frame)
                    return frame
                backoff+=backoff
                sleep(backoff)
            return MissingResponse
	
def _test_sync(logger, command):
    print('Test sync driver')
    driver = SyncHassebDALIUSBDriver()
    driver.logger = logger

    print('Response: {}'.format(driver.send(command)))
    driver.backend.close()

if __name__ == '__main__':
    """Usage: python hasseb.py address value
    """
    from dali.gear.general import DAPC
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
    command = DAPC(int(sys.argv[2]), int(sys.argv[3]))

    _test_sync(logger, command)
