from dali.command import from_frame
from dali.driver.base import AsyncDALIDriver
from dali.driver.base import DALIDriver
from dali.driver.base import SyncDALIDriver
from dali.driver.base import USBBackend
from dali.driver.base import USBListener
from dali.frame import BackwardFrame
from dali.frame import BackwardFrameError
from dali.frame import ForwardFrame
import logging
import struct


DALI_USB_VENDOR = 0x17b5
DALI_USB_PRODUCT = 0x0020

DALI_USB_DIRECTION_DALI = 0x11
DALI_USB_DIRECTION_USB = 0x12
DALI_USB_TYPE_16BIT = 0x03
DALI_USB_TYPE_24BIT = 0x04
DALI_USB_TYPE_NO_RESPONSE = 0x71
DALI_USB_TYPE_RESPONSE = 0x72
DALI_USB_TYPE_COMPLETE = 0x73
DALI_USB_TYPE_BROADCAST = 0x74
# DALI_USB_TYPE_UNKNOWN = 0x77


# debug logging related
DRIVER_CONSTRUCT = 0x0
DRIVER_EXTRACT = 0x1
_exco_str = {
    DRIVER_CONSTRUCT: 'CONSTRUCT',
    DRIVER_EXTRACT: 'EXTRACT',
}
_dr_str = {
    DALI_USB_DIRECTION_DALI: 'DALI -> DALI',
    DALI_USB_DIRECTION_USB: 'USB -> DALI',
}
_ty_str = {
    DALI_USB_TYPE_COMPLETE: 'TYPE_COMPLETE',
    DALI_USB_TYPE_BROADCAST: 'TYPE_BROADCAST',
    DALI_USB_TYPE_RESPONSE: 'TYPE_RESPONSE',
    DALI_USB_TYPE_NO_RESPONSE: 'TYPE_NO_RESPONSE',
    DALI_USB_TYPE_16BIT: 'TYPE_16BIT',
    DALI_USB_TYPE_24BIT: 'TYPE_24BIT',
}


def _log_frame(logger, exco, dr, ty, ec, ad, cm, st, sn):
    msg = (
        '{}\n'
        '    Direction: {}\n'
        '    Type: {}\n'
        '    Ecommand: {}\n'
        '    Address: {}\n'
        '    Command: {}\n'
        '    Status: {}\n'
        '    Seqnum: {}\n'
    )
    logger.info(msg.format(
        _exco_str[exco],
        _dr_str.get(dr, 'UNKNOWN'),
        _ty_str.get(ty, 'UNKNOWN'),
        hex(ec),
        hex(ad),
        hex(cm),
        st is not None and st or 'NONE',
        hex(sn),
    ))


class TridonicDALIUSBNoResponse:

    def __repr__(self):
        return 'NO_RESPONSE'

    __str__ = __repr__


DALI_USB_NO_RESPONSE = TridonicDALIUSBNoResponse()


class TridonicDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Tridonic DALI USB device.

    This code borrows research and implementation details from ``daliserver``
    (https://github.com/onitake/daliserver). Thanks to Gregor Riepl.
    """
    # debug logging
    debug = False
    logger = logging.getLogger('TridonicDALIUSBDriver')
    # next sequence number
    _next_sn = 1

    def construct(self, command):
        """Data expected by DALI USB:

        dr sn ?? ty ?? ec ad cm .. .. .. .. .. .. .. ..
        12 1d 00 03 00 00 ff 08 00 00 00 00 00 00 00 00

        dr: direction
            0x12 = USB side
        sn: seqnum
        ty: type
            0x03 = 16bit
            0x04 = 24bit
        ec: ecommand
        ad: address
        cm: command
        """
        dr = DALI_USB_DIRECTION_USB
        sn = self._get_sn()
        frame = command.frame
        ty = data = None
        ec = 0x0
        if len(frame) == 16:
            ty = DALI_USB_TYPE_16BIT
            ad, cm = frame.as_byte_sequence
            data = struct.pack(
                "BBBBBBBB" + (64 - 8) * 'x',
                dr, sn, 0x0, ty, 0x0, ec, ad, cm
            )
        elif len(frame) == 24:
            ty = DALI_USB_TYPE_24BIT
            # XXX: not yet
            raise ValueError('24 Bit frames not yet')
        else:
            raise ValueError('Unknown frame length: {}'.format(len(frame)))
        if self.debug:
            _log_frame(
                self.logger, DRIVER_CONSTRUCT, dr, ty, ec, ad, cm, None, sn)
        return data

    def extract(self, data):
        """Raw data received from DALI USB:

        dr ty ?? ec ad cm st st sn .. .. .. .. .. .. ..
        11 73 00 00 ff 93 ff ff 00 00 00 00 00 00 00 00

        dr: direction
            0x11 = DALI side
            0x12 = USB side
        ty: type
            0x71 = transfer no response
            0x72 = transfer response
            0x73 = transfer complete
            0x74 = broadcast received (?)
            0x77 = ?
        ec: ecommand
        ad: address
        cm: command
            also serves as response code for 72
        st: status
            internal status code, value unknown
        sn: seqnum
        """
        dr = data[0]
        ty = data[1]
        ec = data[3]
        ad = data[4]
        cm = data[5]
        st = struct.unpack('H', data[6:8])[0]
        sn = data[8]
        if self.debug:
            _log_frame(self.logger, DRIVER_EXTRACT, dr, ty, ec, ad, cm, st, sn)
        # DALI -> DALI
        if dr == DALI_USB_DIRECTION_DALI:
            if ty == DALI_USB_TYPE_COMPLETE:
                return ForwardFrame(16, [ad, cm])
            elif ty == DALI_USB_TYPE_BROADCAST:
                return ForwardFrame(16, [ad, cm])
            elif ty == DALI_USB_TYPE_RESPONSE:
                # request not from us, ignore response
                return
            else:
                msg = 'DALI -> DALI | Unknown type received: {}'.format(hex(ty))
                self.logger.warning(msg)
            return
        # USB -> DALI
        elif dr == DALI_USB_DIRECTION_USB:
            if ty == DALI_USB_TYPE_NO_RESPONSE:
                return DALI_USB_NO_RESPONSE
            elif ty == DALI_USB_TYPE_RESPONSE:
                return BackwardFrame(cm)
            elif ty == DALI_USB_TYPE_COMPLETE:
                # XXX: Happens e.g after sending a DAPC command before
                #      receiving a response. What should we do with it?
                #      dispatch as ordinary forward frame?
                # return ForwardFrame(16, [ad, cm])
                pass
            else:
                msg = 'USB -> DALI | Unknown type received: {}'.format(hex(ty))
                self.logger.warning(msg)
            return
        # Unknown direction
        msg = 'Unknown direction received: {}'.format(hex(dr))
        self.logger.warning(msg)

    def _get_sn(self):
        """Get next sequence number."""
        sn = self._next_sn
        if sn > 255:
            sn = self._next_sn = 1
        else:
            self._next_sn += 1
        return sn


class SyncTridonicDALIUSBDriver(TridonicDALIUSBDriver, SyncDALIDriver):
    """Synchronous ``DALIDriver`` implementation for Tridonic DALI USB device.
    """

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.backend = USBBackend(
            DALI_USB_VENDOR,
            DALI_USB_PRODUCT,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )

    def send(self, command, timeout=None):
        self.backend.write(self.construct(command))
        frame = None
        # For now read up to 2 frames. This may not be reliable if forward
        # frames are passed between request and response from DALI side.
        # though this may not happen at all due to DALI USB implementation
        # details.
        for i in range(2):
            frame = self.extract(self.backend.read(timeout=timeout))
            if isinstance(frame, BackwardFrame):
                if command.response:
                    return command.response(frame)
                return frame
        return DALI_USB_NO_RESPONSE


class AsyncTridonicDALIUSBDriver(TridonicDALIUSBDriver, AsyncDALIDriver):
    """Asynchronous ``DALIDriver`` implementation for Tridonic DALI USB device.
    """
    # transaction mapping
    _transactions = dict()

    def __init__(self, bus=None, port_numbers=None, interface=0):
        self.backend = USBListener(
            self,
            DALI_USB_VENDOR,
            DALI_USB_PRODUCT,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )

    def send(self, command, callback=None, **kw):
        data = self.construct(command)
        sn = struct.unpack_from('B', data, 1)[0]
        self._transactions[sn] = {
            'command': command,
            'callback': callback,
            'kw': kw
        }
        self.backend.write(data)

    def receive(self, data):
        frame = self.extract(data)
        sn = data[8]
        if isinstance(frame, ForwardFrame):
            self._handle_dispatch(frame)
        elif isinstance(frame, BackwardFrame):
            self._handle_response(sn, frame)
        elif frame is DALI_USB_NO_RESPONSE:
            self._handle_response(sn, None)

    def _handle_dispatch(self, frame):
        command = from_frame(frame)
        if self.debug:
            self.logger.info(str(command))
        if self.dispatcher is None:
            if self.debug:
                msg = 'Ignore received command: {}'.format(command)
                self.logger.info(msg)
            return
        self.dispatcher(command)

    def _handle_response(self, sn, frame):
        request = self._transactions.get(sn)
        if not request:
            if self.debug:
                msg = 'Received response to unknown request: {}'.format(sn)
                self.logger.error(msg)
            return
        del self._transactions[sn]
        callback = request['callback']
        if not callback:
            if self.debug:
                self.logger.info('No callback given for received response')
            return
        command = request['command']
        if command.response:
            callback(command.response(frame), **request['kw'])
        else:
            callback(frame, **request['kw'])


def _test_sync(logger, command):
    print('Test sync driver')
    driver = SyncTridonicDALIUSBDriver()
    driver.logger = logger
    driver.debug = True

    print('Response: {}'.format(driver.send(command)))
    driver.backend.close()


def _test_async(logger, command):
    print('Test async driver')
    driver = AsyncTridonicDALIUSBDriver()
    driver.logger = logger
    driver.debug = True

    # async response callback
    def response_received(response):
        print('Response received: {}'.format(response))

    driver.send(command, callback=response_received)

    # exit callback
    def signal_handler(signal, frame):
        driver.backend.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C')
    signal.pause()


if __name__ == '__main__':
    """Usage: python tridonic.py sync|async address value
    """
    from dali.gear.general import DAPC
    import signal
    import sys
    import time

    # setup console logging
    logger = logging.getLogger('TridonicDALIDriver')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

    # command to send
    command = DAPC(int(sys.argv[2]), int(sys.argv[3]))

    # sync interface
    if sys.argv[1] == 'sync':
        _test_sync(logger, command)
    # async interface
    elif sys.argv[1] == 'async':
        _test_async(logger, command)
