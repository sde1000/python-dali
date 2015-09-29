"""
Daliserver
Communicates with daliserver through tcp
"""

__author__ = 'caiwan'

from __future__ import print_function
import socket
import logging
from dali.command import Command

from dali.interface import DriverInterface


class DaliServer(DriverInterface):
    """
    Communicate with daliserver
    (https://github.com/onitake/daliserver)

    NB this requires daliserver commit
    90e34a0cd2945dc7a15681f11647e708f858521e or later.

    """

    def __init__(self, host="localhost", port=55825,
                 multiple_frames_per_connection=False):
        self._target = (host, port)
        self._s = None
        self._multiple_frames_per_connection = multiple_frames_per_connection

    def __enter__(self):
        if self._multiple_frames_per_connection:
            self._s = socket.create_connection(self._target)
        return self

    def __exit__(self, *vpass):
        # print(vpass)
        if self._multiple_frames_per_connection:
            self._s.close()
            self._s = None

    def send(self, command):
        if self._s:
            s = self._s
        else:
            s = socket.create_connection(self._target)

        assert isinstance(command, Command)
        message = command.pack

        logging.info(u"command: {}{}".format(
            command, " (twice)" if command._isconfig else ""))

        # Set a default result which may be used if the first send fails
        result = "\x02\xff\x00\x00"

        try:
            s.send(message)
            result = s.recv(4)
            if command._isconfig:
                s.send(message)
                result = s.recv(4)
        except:
            raise
        finally:
            if not self._s:
                s.close()

        response = self._unpack_response(command, result)

        if response:
            logging.info(u"  -> {0}".format(response))

        return response


