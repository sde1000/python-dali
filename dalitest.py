import struct,socket
from dali.address import *
from dali.command import *

def dalicmd(address,value):
    """
    Very hackily send a message to the lighting system.  Does not
    check for errors.

    """
    message=struct.pack("BB",address,value)
    try:
        s=socket.create_connection(
            ("icarus.haymakers.i.individualpubs.co.uk",55825))
        s.send(message)
        result=s.recv(2)
        s.close()
        return result
    except:
        pass

if __name__=="__main__":
    for addr in range(0,64):
        r=dalicmd(*QueryStatus(Short(addr)).command)
        print "%d: %s"%(addr,repr(r))
#    dalicmd(*ArcPower(Broadcast(),254).command)
