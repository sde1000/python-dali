from __future__ import print_function
import struct
import socket
import logging

from .command import Command


class CommunicationError(Exception):
    pass


class DaliServer(object):
    """Communicate with daliserver
    (https://github.com/onitake/daliserver)

    NB this requires daliserver commit
    90e34a0cd2945dc7a15681f11647e708f858521e or later.

    """

    def __init__(self, host="localhost", port=55825):
        self._target = (host, port)

    def __enter__(self):
        self._s = socket.create_connection(self._target)
        return self

    def __exit__(self, *vpass):
        print(vpass)
        self._s.close()

    def send(self, command):
        assert isinstance(command, Command)
        # message = struct.pack("BBBB", 2, 0, *command.command)
        message = "\x02\x00" + command.pack

        logging.info("command: {}{}".format(command, " (twice)" if command._isconfig else ""))

        # result = "\x02\xff\x00\x00"

        try:
            self._s.send(message)
            result = self._s.recv(4)
            if command._isconfig:
                self._s.send(message)
                result = self._s.recv(4)
        except:
            raise

        finally:
            pass

        response = self.unpack_response(command, result)

        if response:
            logging.info("  -> {0}".format(response))

        return response

    def unpack_response(self, command, result):
        """
        Unpack result from the given bytestream and creates the corresponding
        response object

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
                response = command._response(rval)
            elif status == 255:
                # This is "failure" - daliserver seems to be reporting this
                # for a garbled response when several ballasts reply.
                response = command._response(255)
            else:
                raise CommunicationError("status was %d" % status)

        return response


__all__ = ["DaliServer"]
