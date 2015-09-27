# Experimental driver for Tridonic DALI-USB
# NB requires pyusb-1.0; pyusb-0.4 is not suitable
from __future__ import print_function
from __future__ import unicode_literals
import struct
import usb.core
import usb.util


class DeviceNotFound(Exception):
    pass


class DaliUSB(object):
    """A driver for a Tridonic/Lunatone DALI-USB interface."""

    id_list = [(0x17b5, 0x0020)]

    def __init__(self, address=None, serial=None):
        """Find a DALI-USB device to drive.  The first device found is driven.
        The arguments, if given, restrict the search:

        address is a (bus,device) tuple.
        serial is a serial number string
        """
        kwargs = {}
        if address:
            kwargs['bus'] = address[0]
            kwargs['address'] = address[1]
        if serial:
            kwargs['serial_number'] = serial

        def custom_match(x):
            return (x.idVendor, x.idProduct) in DaliUSB.id_list

        dev = usb.core.find(custom_match=custom_match, **kwargs)
        if not dev:
            raise DeviceNotFound
        self._dev = dev
        self._seqnum = 1
        if self._dev.is_kernel_driver_active(0):
            self._dev.detach_kernel_driver(0)

    @property
    def serial_number(self):
        return self._dev.serial_number

    def start(self):
        """Detach the kernel driver and configure the device."""
        self._dev.set_configuration()
        self._dev.set_interface_altsetting(0)

    def send(self, command):
        # Packets sent to the device appear to have the following format,
        # in bytes (8 bytes total):
        # 0x12   (direction - USB -> DALI)
        # seqnum
        # 0x00
        # type  (0x03 = 16bit, 0x04 = 24bit)
        # 0x00
        # ecommand (unused in 16bit mode)
        # a
        # b
        direction = 0x12
        seqnum = self._seqnum
        self._seqnum = self._seqnum+1
        mtype = 0x03
        ecommand = 0
        a, b = command.frame.as_byte_sequence
        msg = struct.pack(
            "BBBBBBBB" + (64-8) * 'x',
            direction, seqnum, 0, mtype, 0, ecommand, a, b
        )
        print(repr(msg))
        l = self._dev.write(0x02, msg, 1000)
        ret = self._dev.read(0x81, 64, 1000)
        print(ret)
        ret = self._dev.read(0x81, 64, 1000)
        print(ret)
        ret = self._dev.read(0x81, 64, 1000)
        print(ret)

    def stop(self):
        pass
