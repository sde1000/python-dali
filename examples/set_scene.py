#!/usr/bin/env python

from dali.address import Broadcast
from dali.commands import GoToScene
from dali.interface import DaliServer
import sys

if __name__ == "__main__":
    scene = int(sys.argv[1])
    d = DaliServer("localhost", 55825)
    cmd = GoToScene(Broadcast(), scene)
    d.send(cmd)
