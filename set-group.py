#!/usr/bin/env python

import struct,socket,sys
from dali.address import *
from dali.command import *
from dali.interface import daliserver

if __name__=="__main__":
    group=int(sys.argv[1])
    level=int(sys.argv[2])
    d=daliserver("localhost",55825)
    cmd=ArcPower(Group(group),level)
    d.send(cmd)
