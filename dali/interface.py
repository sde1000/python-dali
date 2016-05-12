from __future__ import print_function
from dali.command import Command
import dali.frame
import logging
import socket
import struct


# XXX: This should got into ``dali.driver.daliserver``


class CommunicationError(Exception):
    pass


class DaliServer(object):
    """Communicate with daliserver
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
        if self._multiple_frames_per_connection:
            self._s.close()
            self._s = None

    def send(self, command):
        if self._s:
            s = self._s
        else:
            s = socket.create_connection(self._target)

        assert isinstance(command, Command)
        message = struct.pack("BB", 2, 0) + command.frame.pack

        logging.info(u"command: {}{}".format(
            command, " (twice)" if command.is_config else ""))

        # Set a default result which may be used if the first send fails
        result = "\x02\xff\x00\x00"

        try:
            s.send(message)
            result = s.recv(4)
            if command.is_config:
                s.send(message)
                result = s.recv(4)
        except:
            raise
        finally:
            if not self._s:
                s.close()

        response = self.unpack_response(command, result)

        if response:
            logging.info(u"  -> {0}".format(response))

        return response

    def unpack_response(self, command, result):
        """Unpack result from the given bytestream and creates the
        corresponding response object

        :param command: the command which waiting for it's response
        :param result: the result bytestream which came back
        :return: the result object
        """

        assert isinstance(command, Command)

        ver, status, rval, pad = struct.unpack("BBBB", result)
        response = None

        if command._response:
            if status == 0:
                response = command._response(None)
            elif status == 1:
                response = command._response(dali.frame.BackwardFrame(rval))
            elif status == 255:
                # This is "failure" - daliserver seems to be reporting
                # this for a garbled response when several ballasts
                # reply.  It should be interpreted as "Yes".
                response = command._response(dali.frame.BackwardFrameError(255))
            else:
                raise CommunicationError("status was %d" % status)

        return response

__all__ = ["DaliServer"]
