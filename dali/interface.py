import struct,socket

class daliserver(object):
    """
    Communicate with daliserver (https://github.com/onitake/daliserver)

    """
    def __init__(self,host,port):
        self._target=(host,port)
    def send(self,command):
        message=struct.pack("BB",*command.command)
        s=socket.create_connection(self._target)
        result="\x01\x00"
        try:
            s.send(message)
            result=s.recv(2)
        finally:
            s.close()
        if command._response and result[0]=="\x00":
            return command._response(ord(result[1]))

__all__=["daliserver"]
