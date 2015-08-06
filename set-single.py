#!/usr/bin/env python

import sys

from dali.address import *
from dali.command import *
from dali.interface import DaliServer

if __name__ == "__main__":
    addr = Short(int(sys.argv[1])) if sys.argv[1] != "all" else Broadcast()
    level = int(sys.argv[2])
    d = DaliServer("localhost", 55825)
    cmd = ArcPower(addr, level)
    d.send(cmd)
