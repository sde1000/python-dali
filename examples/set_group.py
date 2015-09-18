#!/usr/bin/env python

from dali.address import Group
from dali.commands import ArcPower
from dali.interface import DaliServer
import sys

if __name__ == "__main__":
    group = int(sys.argv[1])
    level = int(sys.argv[2])
    d = DaliServer("localhost", 55825)
    cmd = ArcPower(Group(group), level)
    d.send(cmd)
