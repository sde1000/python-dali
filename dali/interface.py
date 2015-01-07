from __future__ import print_function
import struct,socket

class CommunicationError(Exception):
    pass

class daliserver(object):
    """Communicate with daliserver
    (https://github.com/onitake/daliserver)

    NB this requires daliserver commit
    90e34a0cd2945dc7a15681f11647e708f858521e or later.

    """
    def __init__(self,host,port,verbose=False):
        self._target=(host,port)
        self._verbose=verbose
    def send(self,command):
        message=struct.pack("BBBB",2,0,*command.command)
        s=socket.create_connection(self._target)
        if self._verbose:
            print("{}{}".format(unicode(command)," (twice)" if command._isconfig else ""))
        result="\x02\xff\x00\x00"
        try:
            s.send(message)
            result=s.recv(4)
            if command._isconfig:
                s.send(message)
                result=s.recv(4)
        finally:
            s.close()
        ver,status,rval,pad=struct.unpack("BBBB",result)
        response=None
        if command._response:
            if status==0:
                response=command._response(None)
            elif status==1:
                response=command._response(rval)
            elif status==255:
                # This is "failure" - daliserver seems to be reporting this
                # for a garbled response when several ballasts reply.
                response=command._response(255)
            else:
                raise CommunicationError("status was %d"%status)
        if self._verbose:
            if response:
                print("  -> {}".format(unicode(response)))
        return response

__all__=["daliserver"]
