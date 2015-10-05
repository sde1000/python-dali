from __future__ import print_function
from dali.command import Command
import struct


class CommunicationError(Exception):
    pass


class ParameterError(Exception):
    pass


class InterfaceSimpleRawDriver(object):
    """
    Interface to create a low-level raw driver to communicate with devices using
    various protocols, using one method. Does not support async communication and
    not event-driven. 
    """

    def send(self):
        """
        Sends a command, and wait for it's answer if it was a query using
        a protocol implemented it's children classes.
        :return:
        """
        raise NotImplemented()

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
