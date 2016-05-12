from __future__ import unicode_literals
from dali.driver.base import DALIDriver
import logging
import struct


logger = logging.getLogger('dali')


DALI_USB_DIRECTION_DALI = 0x11,
DALI_USB_DIRECTION_USB = 0x12,
DALI_USB_TYPE_16BIT = 0x03,
DALI_USB_TYPE_24BIT = 0x04,
DALI_USB_TYPE_NO_RESPONSE = 0x71,
DALI_USB_TYPE_RESPONSE = 0x72,
DALI_USB_TYPE_COMPLETE = 0x73,
DALI_USB_TYPE_BROADCAST = 0x74,


class TridonicDALIUSBDriver(DALIDriver):
    """``DALIDriver`` implementation for Tridonic DALI USB device.

    This code borrows research and implementation details from ``daliserver``
    (https://github.com/onitake/daliserver). Thanks to Gregor Riepl.
    """
    # debug logging
    debug = True
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
        st = struct.unpack('h', data[6:8])
        sn = data[8]
        # DALI -> DALI
        if dr == DALI_USB_DIRECTION_DALI:
            if ty == DALI_USB_TYPE_COMPLETE:
                if self.debug:
                    logger.info('DALI -> DALI (TYPE_COMPLETE)')
                # DaliFramePtr frame = daliframe_new(in.address, in.command);
                # dali->bcast_callback(USBDALI_SUCCESS, frame, in.status, dali->bcast_arg);
                # XXX: how to construct?
                frame = ForwardFrame() # ?
                self._handle_dispatch(frame)
                return
            elif ty == DALI_USB_TYPE_BROADCAST:
                if self.debug:
                    logger.info('DALI -> DALI (TYPE_BROADCAST)')
                # DaliFramePtr frame = daliframe_enew(in.ecommand, in.address, in.command);
                # dali->bcast_callback(USBDALI_SUCCESS, frame, in.status, dali->bcast_arg);
                # XXX: how to construct?
                frame = ForwardFrame() # ?
                self._handle_dispatch(frame)
                return
            else:
                msg = 'Unknown type received: {}'.format(hex(ty))
                raise ValueError(msg)
        # USB -> DALI
        elif dr == DALI_USB_DIRECTION_USB:
            if ty == DALI_USB_TYPE_NO_RESPONSE:
                if self.debug:
                    logger.info('USB -> DALI (TYPE_NO_RESPONSE)')
                # DaliFramePtr frame = daliframe_new(in.address, in.command);
                # dali->req_callback(USBDALI_SUCCESS, frame, 0xff, in.status, dali->transaction->arg);
                # XXX: what's the difference between NO_RESPONSE and RESPONSE?
                #      same handling as RESPONSE? -> In daliserver actually
                #      it looks like this is the BackwardFrameError case, right?
                # XXX: how to construct?
                frame = BackwardFrameError() # ?
                self._handle_response(sn, frame)
                return
            elif ty == DALI_USB_TYPE_RESPONSE:
                if self.debug:
                    logger.info('USB -> DALI (TYPE_RESPONSE)')
                # DaliFramePtr frame = daliframe_new(in.address, in.command);
                # dali->req_callback(USBDALI_RESPONSE, frame, in.command, in.status, dali->transaction->arg);
                # XXX: how to construct?
                frame = BackwardFrame() # ?
                self._handle_response(sn, frame)
                return
            elif ty == DALI_USB_TYPE_COMPLETE:
                if self.debug:
                    logger.info('USB -> DALI (TYPE_COMPLETE)')
                # XXX: When does this happen? What should happen here?
                return
            else:
                msg = 'Unknown type received: {}'.format(hex(ty))
                raise ValueError(msg)
        # Unknown direction
        msg = 'Unknown direction received: {}'.format(hex(dr))
        raise ValueError(msg)

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
        dr = 0x12
        sn = self._get_sn()
        frame = command.frame
        ty = data = None
        ec = 0x0
        if len(frame) == 16:
            ty = 0x03
            ad, cm = frame.as_byte_sequence
            data = struct.pack(
                "BBBBBBBB" + (64 - 8) * 'x',
                dr, sn, 0x0, ty, 0x0, ec, ad, cm
            )
        elif len(frame) == 24:
            ty = 0x04
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
            logger.info(str(command))
        if self.dispatcher is None:
            msg = 'Ignore received command: {}'.format(command)
            logger.warning(msg)
        else:
            self.dispatcher(command)

    def _handle_response(self, sn, frame):
        request = self._transactions.get(sn)
        if not request:
            msg = 'Received response to unknown request: {}'.format(sn)
            logger.error(msg)
            return
        del self._transactions[sn]
        callback = request['callback']
        if not callback:
            if self.debug:
                logger.info('No callback given for received response')
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
