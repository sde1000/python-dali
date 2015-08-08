from __future__ import print_function
import struct
import socket
import logging
from .command import Command
from .command import Response


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
        print(vpass)
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

        ver, status, rval, pad = struct.unpack("BBBB", result)
        response = None
        if command._response:
            if status == 0:
                response = command._response(None)
            elif status == 1:
                response = command._response(rval)
            elif status == 255:
                # This is "failure" - daliserver seems to be reporting
                # this for a garbled response when several ballasts
                # reply.  It should be interpreted as "Yes".
                response = command._response(255)
            else:
                raise CommunicationError("status was %d" % status)

            if response:
                logging.info(u"  -> {}".format(response))

        return response


__all__ = ["DaliServer"]
