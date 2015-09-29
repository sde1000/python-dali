
"""
UART communication driver for DALI
"""

import logging
import serial
import struct
from dali.command import Command
from dali.interface import DriverInterface, ParameterError


class DaliUART(DriverInterface):
    """
    Uart driver for DALI
    """
    
    def __init__(self, com, baud=115200):
        """
        :param:com port name
        :param:baud baud rate - 11520 default
        """
        self._s = None
        self._uart = (com, baud)

    def __enter__(self):
        """
        Entry point of the context manager 
        """
        
        self._s = serial.Serial(self._uart[0], self._uart[1], timeout=0.001)

        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Teardown for context manager
        """
        
        self._s.close()
        
    def send(self, command):
        """
        Send a DALI command, and recv. response if there's any expected

        Data format:
            Data is sent and recieved in binary format.

            - 1 byte : length of the package
            - n byte : data of the package
            - 1 byte : XOR crc of the data

        :param command: Command object

        :returns: response object, if any

        :raise ParameterError: when the recv data is not matching or timeot occured
        """
        assert isinstance(command, Command)
        assert self._s is not None
        assert isinstance(self._s, serial.Serial)

        recv_data = None
        response = None

        try:
            #
            crc = 0
            for c in list(command.pack):
                crc ^= ord(c)

            # send data in reverse order
            data = struct.pack("B", len(command)) + command.pack + struct.pack("B", crc)
            logging.info("Send data: {0}".format(":".join("{:02x}".format(ord(c)) for c in data)))
            self._s.write(data)

            if command.is_query:
                logging.info("Query was sent, awaiting response")
                self._s.timeout = 1
                recv_data = self._s.read(4)

            if recv_data is not None:
                logging.info("Recv data: {0}".format(":".join("{:02x}".format(ord(c)) for c in recv_data)))
                try:
                    # If the recieved data is shorter than the shortest possible data, we fail unconditionally
                    if len(recv_data) < 3:
                        raise ParameterError

                    length = struct.unpack("B", recv_data[0])
                    crc = struct.unpack("B", recv_data[-1])

                    # The data is in between the first and the last byte
                    data = recv_data[1:-1]

                    # TODO --- at this point we have a chance to check the CRC of the response

                    response = self._unpack_response(command, data)
                except:
                    raise ParameterError

                if response:
                    logging.info(u"  -> {0}".format(response))

        except:
            # nothing to do here yet
            raise

        # no need to clean up connection here
        return response
