#!/usr/bin/env python

# import logger

from dali.address import *
from dali.commands import *
from dali.interface import DaliServer

if __name__ == "__main__":

    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)

    with DaliServer() as d:

        for addr in range(0, 64):

            cmd = QueryDeviceType(Short(addr))
            r = d.send(cmd)

            logging.info("[%d]: resp: %s" % (addr, r))

            if r.value == 1:
                d.send(EnableDeviceType(1))
                r = d.send(QueryEmergencyMode(Short(addr)))
                logging.info(" -- {0}".format(r))

                d.send(EnableDeviceType(1))
                r = d.send(QueryEmergencyFeatures(Short(addr)))
                logging.info(" -- {0}".format(r))

                d.send(EnableDeviceType(1))
                r = d.send(QueryEmergencyFailureStatus(Short(addr)))
                logging.info(" -- {0}".format(r))

                d.send(EnableDeviceType(1))
                r = d.send(QueryEmergencyStatus(Short(addr)))
                logging.info(" -- {0}".format(r))
