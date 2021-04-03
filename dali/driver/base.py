import threading
from time import sleep, perf_counter


###############################################################################
# driver contracts
###############################################################################

class DALIDriver:
    """Object for handling wrapped DALI frames sent to and received from
    DALI drivers.

    A DALI driver represents a service or physical gateway which is able to
    communicate with a DALI bus.
    """

    backend = None
    """``Backend`` instance used for reading and writing."""

    def construct(self, command):
        """Construct raw data containing the packed DALI frame from command
        which can be sent to DALI driver.

        @param command: DALI command to send.
        @return data: Returns data which can be sent to backend.
        """
        raise NotImplementedError(
            'Abstract ``DaliDriver`` does not implement ```construct`')

    def extract(self, data):
        """Extract and return DALI Frame from data which has been received
        from DALI driver.

        @param data: Raw data received from gateway.
        @return frame: Returns ``dali.frame.Frame`` deriving object.
        """
        raise NotImplementedError(
            'Abstract ``DaliDriver`` does not implement ``extract``')


class SyncDALIDriver(DALIDriver):
    """Object for synchronously sending data to DALI drivers immediately
    expecting and returning a result.
    """

    def send(self, command, timeout=None):
        """Send command to gateway and return response.

        @param command: DALI command to send.
        @param timeout: Timeout in milliseconds.
        @return response: response to command.
        """
        raise NotImplementedError(
            'Abstract ``SyncDALIDriver`` does not implement ``send``')


class AsyncDALIDriver(DALIDriver):
    """Object for asynchronously handling data sent to and received from
    DALI drivers.
    """

    dispatcher = None
    """Callable used for dispatching incoming forward frames.
    """

    def send(self, command, callback=None, **kw):
        """Send command to gateway.

        @param command: DALI command to send.
        @param callback: Function which gets called with received response.
        @param **kw: Optional keyword arguments which get passed to response
                     callback
        """
        raise NotImplementedError(
            'Abstract ``AsyncDALIDriver`` does not implement ``send``')

    def receive(self, frame):
        """Receive DALI Frame.

        If a forward frame is received, ``self.dispatcher`` is used for
        delegating it.

        If a backward frame is received, the ``callback`` given in
        ``self.send`` is used.

        @param frame: ``dali.frame.Frame`` deriving object.
        """
        raise NotImplementedError(
            'Abstract ``AsyncDALIDriver`` does not implement ``receive``')


###############################################################################
# backend contracts
###############################################################################

class Backend:
    """Object representing a backend.
    """

    def read(self, timeout=None):
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``read``')

    def write(self, data):
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``write``')

    def close(self):
        raise NotImplementedError(
            'Abstract ``Backend`` does not implement ``close``')


class Listener(Backend):
    """Object representing a backend which is permanently listening for
    incoming frames.
    """

    driver = None
    """``AsyncDALIDriver`` instance.
    """

    def listen(self):
        """Listen to backend and dispatch receiced data to ``self.driver``.
        """
        raise NotImplementedError(
            'Abstract ``Listener`` does not implement ``listen``')


###############################################################################
# USB backends
###############################################################################

class USBBackend(Backend):
    """Backend implementation for communicating with USB devices.
    """

    def __init__(self, vendor, product, bus=None,
                 port_numbers=None, interface=0):
        try:
            import usb
        except ImportError:
            raise RuntimeError('{} requires pyusb but it is not installed'.format(self.__class__.__name__))
        
        self._device = None
        # lookup devices by vendor and product
        devices = [dev for dev in usb.core.find(
            find_all=True,
            idVendor=vendor,
            idProduct=product
        )]
        # use first device if bus or port_numers not defined
        if bus is None or port_numbers is None:
            self._device = devices[0]
        else:
            for dev in devices:
                if dev.bus == bus and dev.port_numbers == port_numbers:
                    self._device = dev
                    break
        # if queried device not found, raise
        if not self._device:
            raise usb.core.USBError('Device not found')
        # detach kernel driver if necessary
        if self._device.is_kernel_driver_active(interface) is True:
            self._device.detach_kernel_driver(interface)
        # set device configuration
        self._device.set_configuration()
        # claim interface
        usb.util.claim_interface(self._device, interface)
        # get active configuration
        cfg = self._device.get_active_configuration()
        intf = cfg[(0, 0)]
        # get write end point
        def match_ep_out(e):
            return usb.util.endpoint_direction(e.bEndpointAddress) == \
                   usb.util.ENDPOINT_OUT
        self._ep_write = usb.util.find_descriptor(
            intf, custom_match=match_ep_out)
        # get read end point
        def match_ep_in(e):
            return usb.util.endpoint_direction(e.bEndpointAddress) == \
                   usb.util.ENDPOINT_IN
        self._ep_read = usb.util.find_descriptor(
            intf, custom_match=match_ep_in)

    def read(self, timeout=None):
        """Read data from USB device.
        """
        return self._ep_read.read(self._ep_read.wMaxPacketSize, timeout=timeout)

    def write(self, data):
        """Write data to USB device.
        """
        return self._ep_write.write(data)

    def close(self):
        """Close connection to USB device.
        """
        usb.util.dispose_resources(self._device)


class USBListener(USBBackend, Listener):
    """Listener implementation for communicating with USB devices.
    """

    def __init__(self, driver, vendor, product, bus=None,
                 port_numbers=None, interface=0):
        super(USBListener, self).__init__(
            vendor,
            product,
            bus=bus,
            port_numbers=port_numbers,
            interface=interface
        )
        self.driver = driver
        # flag whether actually disconnecting from device
        self._disconnecting = False
        # event to stop listening
        self._stop_listening = threading.Event()
        # create and start listener thread
        self._listener = threading.Thread(target=self.listen)
        self._listener.start()

    def listen(self):
        """Poll data from USB device.
        """
        while not self._stop_listening.is_set():
            try:
                self.driver.receive(self.read())
            except usb.core.USBError as e:
                # read timeout
                if e.errno == 110:
                    continue
                if not self._disconnecting:
                    self.close()

    def close(self):
        """Close connection to USB device.
        """
        self._disconnecting = True
        self._stop_listening.set()
        super(USBListener, self).close()

class SerialBackend(Backend):
    """``Backend`` implementation to communicate with DALI interfaces over a serial connection."""

    def __init__(self, port, baudrate=115200, bytesize=None, parity=None, stopbits=None):
        """Open connection to the DALI interface.

        @param port: valid serial port (e.g. /dev/ttyUSB0 or COM1)
        @param baudrate: serial baudrate; default is 115.200
        @param bytesize: number of bits per byte; default is 8
        @param parity: configures parity bit; default is none
        @param stopbits: number of stopbits per byte; default is one"""

        try:
            import serial
        except ImportError:
            raise RuntimeError('{} requires pyserial but it is not installed'.format(self.__class__.__name__))

        # constants from serial can't be use in the method's declaration as serial has not been imported yet
        # therefore the default is None and replaced with the proper constants below
        bytesize = bytesize if bytesize is not None else serial.EIGHTBITS
        parity = parity if parity is not None else serial.PARITY_NONE
        stopbits = stopbits if stopbits is not None else serial.STOPBITS_ONE

        # using serial_for_url makes it possible to talk to devices over the network (e.g. RFC2217)
        self._serial = serial.serial_for_url(url=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits)

        # for compatibility with older pyserial versions
        # background: the methods for flushing the in-/out-buffer were renamed in v3.0
        if serial.VERSION.split('.')[0] == '2':
            self._reset_input_buffer = self._serial.flushInput
            self._reset_output_buffer = self._serial.flushOutput
        elif serial.VERSION.split('.')[0] == '3':
            self._reset_input_buffer = self._serial.reset_input_buffer
            self._reset_output_buffer = self._serial.reset_output_buffer
        else:
            raise RuntimeError(f'pyserial={serial.VERSION} is not supported')

        # flush all buffers to remove old data before checking the port
        self._reset_output_buffer()
        sleep(0.050) # just a precaution if the previous command sent some data
        self._reset_input_buffer()
            
        # internal read timeout is set to 10 ms to increase responsiveness
        self._serial.timeout = 0.010

    def read(self, timeout=None):
        """Read data from the DALI interface.

        @param timeout: read timeout in seconds; set to 0 or None to disable
        @return data read from the interface (bytes)"""

        # to compensate for the short read timeout and to use the timeout argument, the read is repeated until
        # more time than specified has elapsed
        start = perf_counter()
        data = bytes()
        while timeout and abs(start-perf_counter()) < timeout:
            data = self._serial.read()
            if len(data) > 0:
                break
        return data

    def write(self, data):
        """Write data to the DALI interface.

        @param data: data to write
        @return number of bytes written"""

        bytes_written = self._serial.write(data)
        self._serial.flush()
        return bytes_written

    def close(self):
        """Close connection to the DALI interface."""
        self._serial.close()
