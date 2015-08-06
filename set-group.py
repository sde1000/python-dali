#!/usr/bin/env python

import sys

from dali.address import *
from dali.command import *
from dali.interface import DaliServer

if __name__ == "__main__":
    group = int(sys.argv[1])
    level = int(sys.argv[2])
    d = DaliServer("localhost", 55825)
    cmd = ArcPower(Group(group), level)
    d.send(cmd)
