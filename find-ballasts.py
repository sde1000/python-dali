#!/usr/bin/env python

from __future__ import print_function
from dali.command import *
from dali.interface import daliserver
import time

def set_search_addr(i,addr):
    i.send(SetSearchAddrH((addr>>16)&0xff))
    i.send(SetSearchAddrM((addr>>8)&0xff))
    i.send(SetSearchAddrL(addr&0xff))

def find_next(i,low,high):
    """Find the ballast with the lowest random address.  The caller
    guarantees that there are no ballasts with an address lower than
    'low'.

    """
    print("Searching from {} to {}...".format(low,high))
    if low==high:
        set_search_addr(i,low)
        response=i.send(Compare())
        if response.value==True:
            print("Found ballast at {}; withdrawing it...".format(low))
            i.send(Withdraw())
            return low
        return None
    set_search_addr(i,high)
    response=i.send(Compare())
    if response.value==True:
        midpoint=(low+high)/2
        return find_next(i,low,midpoint) or find_next(i,midpoint+1,high)

def find_ballasts(interface):
    i=interface
    ballasts=[]

    i.send(Terminate())
    i.send(Initialise(broadcast=True,address=None))
    i.send(Randomise())
    time.sleep(0.1) # Randomise may take up to 100ms

    low=0
    high=0xffffff
    while low is not None:
        low=find_next(i,low,high)
        if low is not None:
            ballasts.append(low)
            low=low+1

    i.send(Terminate())
    return ballasts

if __name__=="__main__":
    d=daliserver("localhost",55825,verbose=True)

    ballasts=find_ballasts(d)
    print("{} ballasts found:".format(len(ballasts)))
    print(ballasts)
