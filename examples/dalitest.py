#!/usr/bin/env python

from dali.address import Short
from dali.gear.general import EnableDeviceType
from dali.gear.general import QueryDeviceType
from dali.gear.emergency import QueryEmergencyFailureStatus
from dali.gear.emergency import QueryEmergencyFeatures
from dali.gear.emergency import QueryEmergencyMode
from dali.gear.emergency import QueryEmergencyStatus
from dali.interface import DaliServer
import logging

if __name__ == "__main__":
    log_format = '%(levelname)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)

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
