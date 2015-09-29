from __future__ import print_function
from dali.command import Command
import struct


class CommunicationError(Exception):
    pass


class ParameterError(Exception):
    pass

class DriverInterface(object):
    """
    Driver interface class
    Contains the common definition of functions for variousdrivers
    """

    def send(self):
        """
        Send command, and returns its response
        :return:
        """
        raise RuntimeError("Not implemented method")

    @staticmethod
    def _unpack_response(command, result):
        """
        Unpack result from the given bytestream and creates the corresponding
        response object

        :param command: the command which waiting for it's response
        :param result: the result bytestream which came back
        :return: the result object
        """

        assert isinstance(command, Command)
        assert isinstance(result, str)
        assert len(result) is 4

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

        return response

__all__ = ["DaliServer"]
