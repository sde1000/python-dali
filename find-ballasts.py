#!/usr/bin/env python

from __future__ import print_function
from dali.command import *
from dali.interface import daliserver
import time

def set_search_addr(i,addr):
    i.send(SetSearchAddrH((addr>>16)&0xff))
    i.send(SetSearchAddrM((addr>>8)&0xff))
    i.send(SetSearchAddrL(addr&0xff))

def search_range(i,low,high,ballasts):
    """Search a range of random addresses from low to high inclusive for
    previously undiscovered ballasts.  There must be no previously
    undiscovered ballasts with addresses lower than "low" when this
    function is called.

    """
    print("Searching from {} to {}...".format(low,high))
    if low==high:
        set_search_addr(i,low)
        response=i.send(Compare())
        if response.value==True:
            print("Found ballast at {}; withdrawing it...".format(low))
            i.send(Withdraw())
            ballasts.append(low)
        return
    # See if there are any ballasts between low and high
    set_search_addr(i,high)
    response=i.send(Compare())
    if response.value==True:
        # There are.  Search each half of the range separately.
        midpoint=(low+high)/2
        search_range(i,low,midpoint,ballasts)
        search_range(i,midpoint+1,high,ballasts)

def find_ballasts(interface):
    i=interface
    ballasts=[]

    i.send(Terminate())
    i.send(Initialise(broadcast=True,address=None))
    i.send(Randomise())
    time.sleep(0.1) # Randomise may take up to 100ms

    search_range(i,0,0xffffff,ballasts)

    i.send(Terminate())
    return ballasts

if __name__=="__main__":
    haymakers=daliserver("icarus.haymakers.i.individualpubs.co.uk",55825,
                         verbose=True)

    ballasts=find_ballasts(haymakers)
    print("{} ballasts found:".format(len(ballasts)))
    print(ballasts)
