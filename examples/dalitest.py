#!/usr/bin/env python

from dali.address import Short
from dali.gear.general import EnableDeviceType
from dali.gear.general import QueryDeviceType
from dali.gear.emergency import QueryEmergencyFailureStatus
from dali.gear.emergency import QueryEmergencyFeatures
from dali.gear.emergency import QueryEmergencyMode
from dali.gear.emergency import QueryEmergencyStatus
from dali.driver.daliserver import DaliServer
from dali.driver.uart import DaliUART
import logging

import time

if __name__ == "__main__":
    log_format = '%(levelname)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)

    d = DaliServer()
    #d = DaliUART('COM4')

    with d:

        """
        while True:
            for i in range(0, 254, 10):
                d.send(ArcPower(Broadcast(), i))
                time.sleep(0.300)
            for i in range(254, 0, 10):
                d.send(ArcPower(Broadcast(), i))
                time.sleep(0.300)
        """

        for addr in range(0, 64):
            cmd = QueryDeviceType(Short(addr))
            r = d.send(cmd)

            logging.info("[%d]: resp: %s" % (addr, r))

            if r and r.value is 1:
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

