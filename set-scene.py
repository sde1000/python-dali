#!/usr/bin/env python

import sys

from dali.address import *
from dali.commands import *
from dali.interface import DaliServer

if __name__ == "__main__":
    scene = int(sys.argv[1])
    d = DaliServer("localhost", 55825)
    cmd = GoToScene(Broadcast(), scene)
    d.send(cmd)
