#!/usr/bin/env python

# import logger

from dali.address import *
from dali.commands import *
from dali.interface import daliserver

if __name__ == "__main__":

    d = daliserver("localhost", 55825)

    for addr in range(0, 64):

        cmd = QueryDeviceType(Short(addr))
        r = d.send(cmd)
        print("%d: %s" % (addr, unicode(r)))

        if r.value == 1:
            d.send(EnableDeviceType(1))
            r = d.send(QueryEmergencyMode(Short(addr)))
            print(" -- {0}".format(unicode(r)))

            d.send(EnableDeviceType(1))
            r = d.send(QueryEmergencyFeatures(Short(addr)))
            print(" -- {0}".format(unicode(r)))

            d.send(EnableDeviceType(1))
            r = d.send(QueryEmergencyFailureStatus(Short(addr)))
            print(" -- {0}".format(unicode(r)))

            d.send(EnableDeviceType(1))
            r = d.send(QueryEmergencyStatus(Short(addr)))
            print(" -- {0}".format(unicode(r)))
