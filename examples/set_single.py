#!/usr/bin/env python

from dali.address import Broadcast
from dali.address import Short
from dali.gear.general import DAPC
from dali.interface import DaliServer
import sys

if __name__ == "__main__":
    addr = Short(int(sys.argv[1])) if sys.argv[1] != "all" else Broadcast()
    level = int(sys.argv[2])
    d = DaliServer("localhost", 55825)
    cmd = DAPC(addr, level)
    d.send(cmd)
