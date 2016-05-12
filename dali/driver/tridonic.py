from __future__ import unicode_literals
from dali.command import from_frame
from dali.driver.base import DALIDriver
from dali.frame import BackwardFrame
# from dali.frame import BackwardFrameError
from dali.frame import ForwardFrame
import logging
import struct


DALI_USB_DIRECTION_DALI = 0x11
DALI_USB_DIRECTION_USB = 0x12
DALI_USB_TYPE_16BIT = 0x03
DALI_USB_TYPE_24BIT = 0x04
DALI_USB_TYPE_NO_RESPONSE = 0x71
DALI_USB_TYPE_RESPONSE = 0x72
DALI_USB_TYPE_COMPLETE = 0x73
DALI_USB_TYPE_BROADCAST = 0x74


# debug logging related
DRIVER_SEND = 0x0
DRIVER_RECEIVE = 0x1
_sr_str = {
    DRIVER_SEND: 'SEND',
    DRIVER_RECEIVE: 'RECEIVE',
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


def _log_frame(logger, sr, dr, ty, ec, ad, cm, st, sn):
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
        _sr_str[sr],
        _dr_str.get(dr, 'UNKNOWN'),
        _ty_str.get(ty, 'UNKNOWN'),
        hex(ec),
        hex(ad),
        hex(cm),
        st is not None and st or 'NONE',
        hex(sn),
    ))


class TridonicDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Tridonic DALI USB device.

    This code borrows research and implementation details from ``daliserver``
    (https://github.com/onitake/daliserver). Thanks to Gregor Riepl.
    """
    # debug logging
    debug = True
    logger = logging.getLogger('TridonicDALIUSBDriver')
    # transaction mapping
    _transactions = dict()
    # next sequence number
    _next_sn = 0

    def receive(self, data):
        """Data received from DALI USB:

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
        # XXX: why is unpacked value tuple?
        st = struct.unpack('>H', data[6:8])
        sn = data[8]
        if self.debug:
            _log_frame(self.logger, DRIVER_RECEIVE, dr, ty, ec, ad, cm, st, sn)
        # DALI -> DALI
        if dr == DALI_USB_DIRECTION_DALI:
            if ty == DALI_USB_TYPE_COMPLETE:
                frame = ForwardFrame(16, [ad, cm])
                self._handle_dispatch(frame)
                return
            elif ty == DALI_USB_TYPE_BROADCAST:
                frame = ForwardFrame(16, [ad, cm])
                self._handle_dispatch(frame)
                return
            elif ty == DALI_USB_TYPE_RESPONSE:
                # request not from us, ignore response
                return
            else:
                msg = 'DALI -> DALI | Unknown type received: {}'.format(hex(ty))
                self.logger.warning(msg)
        # USB -> DALI
        elif dr == DALI_USB_DIRECTION_USB:
            if ty == DALI_USB_TYPE_NO_RESPONSE:
                self._handle_response(sn, None)
                return
            elif ty == DALI_USB_TYPE_RESPONSE:
                frame = BackwardFrame(cm)
                self._handle_response(sn, frame)
                return
            elif ty == DALI_USB_TYPE_COMPLETE:
                # XXX: When does this happen? What should happen here?
                return
            else:
                msg = 'USB -> DALI | Unknown type received: {}'.format(hex(ty))
                self.logger.warning(msg)
        # Unknown direction
        msg = 'Unknown direction received: {}'.format(hex(dr))
        self.logger.warning(msg)

    def send(self, command, callback=None, **kw):
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
            if self.debug:
                _log_frame(
                    self.logger, DRIVER_SEND, dr, ty, ec, ad, cm, None, sn)
        elif len(frame) == 24:
            ty = DALI_USB_TYPE_24BIT
            # XXX: not yet
            raise ValueError('24 Bit frames not yet')
        else:
            raise ValueError('Unknown frame length: {}'.format(len(frame)))
        self._transactions[sn] = {
            'command': command,
            'callback': callback,
            'kw': kw
        }
        self.write(data)

    def write(self):
        """Write data to Gateway."""
        raise NotImplementedError(
            'Abstract ``TridonicDALIUSBDriver`` does not implement ``write``')

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
            callback(command._response(frame), **request['kw'])
        else:
            callback(frame, **request['kw'])

    def _get_sn(self):
        """Get next sequence number."""
        sn = self._next_sn
        if sn > 255:
            sn = self._next_sn = 0
        else:
            self._next_sn += 1
        return sn
