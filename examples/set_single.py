#!/usr/bin/env python

from dali.address import Broadcast
from dali.address import Short
from dali.commands import ArcPower
from dali.interface import DaliServer
import sys

if __name__ == "__main__":
    addr = Short(int(sys.argv[1])) if sys.argv[1] != "all" else Broadcast()
    level = int(sys.argv[2])
    d = DaliServer("localhost", 55825)
    cmd = ArcPower(addr, level)
    d.send(cmd)
