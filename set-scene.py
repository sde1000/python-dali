#!/usr/bin/env python

import struct, socket, sys
from dali.address import *
from dali.commands import *
from dali.interface import daliserver

if __name__ == "__main__":
    scene = int(sys.argv[1])
    d = daliserver("localhost", 55825)
    cmd = GoToScene(Broadcast(), scene)
    d.send(cmd)
