#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

from dali.gear.general import Compare
from dali.gear.general import Initialise
from dali.gear.general import Randomise
from dali.gear.general import SetSearchAddrH
from dali.gear.general import SetSearchAddrL
from dali.gear.general import SetSearchAddrM
from dali.gear.general import Terminate
from dali.gear.general import Withdraw
from dali.interface import DaliServer
import sys
import time


def set_search_addr(i, addr):
    i.send(SetSearchAddrH((addr >> 16) & 0xff))
    i.send(SetSearchAddrM((addr >> 8) & 0xff))
    i.send(SetSearchAddrL(addr & 0xff))


def find_next(i, low, high):
    """Find the ballast with the lowest random address.  The caller
    guarantees that there are no ballasts with an address lower than
    'low'.

    """
    print("Searching from {} to {}...".format(low, high))
    if low == high:
        set_search_addr(i, low)
        response = i.send(Compare())

        if response.value is True:
            print("Found ballast at {}; withdrawing it...".format(low))
            i.send(Withdraw())
            return low
        return None

    set_search_addr(i, high)
    response = i.send(Compare())

    if response.value is True:
        midpoint = (low + high) // 2
        return find_next(i, low, midpoint) or find_next(i, midpoint + 1, high)


def find_ballasts(interface):
    i = interface
    _ballasts = []

    i.send(Terminate())
    i.send(Initialise(broadcast=True, address=None))
    i.send(Randomise())
    time.sleep(0.1)  # Randomise may take up to 100ms

    low = 0
    high = 0xffffff
    while low is not None:
        low = find_next(i, low, high)
        if low is not None:
            _ballasts.append(low)
            low += 1

    i.send(Terminate())
    return _ballasts


if __name__ == "__main__":
    host = "localhost"
    port = 55825

    print("Usage: find-ballasts.py [host] [port]")

    if len(sys.argv) > 1:
        host = sys.argv[1]
        if len(sys.argv) > 2:
            port = int(sys.argv[2])

    print("Looking for ballast devices at {0}:{1}".format(host, port))

    with DaliServer(host, port) as d:
        ballasts = find_ballasts(d)

    print("{} ballasts found:".format(len(ballasts)))
    print(ballasts)
