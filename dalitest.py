import struct,socket
from dali.address import *
from dali.command import *
from dali.interface import daliserver

if __name__=="__main__":
    haymakers=daliserver("icarus.haymakers.i.individualpubs.co.uk",55825)
    for addr in range(0,64):
        cmd=QueryDeviceType(Short(addr))
        print "%d: %s"%(addr,unicode(haymakers.send(cmd)))
