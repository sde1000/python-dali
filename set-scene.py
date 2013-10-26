import struct,socket,sys
from dali.address import *
from dali.command import *
from dali.interface import daliserver

if __name__=="__main__":
    scene=int(sys.argv[1])
    haymakers=daliserver("icarus.haymakers.i.individualpubs.co.uk",55825)
    cmd=GoToScene(Broadcast(),scene)
    haymakers.send(cmd)
