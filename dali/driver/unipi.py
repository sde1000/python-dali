from __future__ import print_function, unicode_literals

import ctypes as C
import logging
from time import sleep

from pymodbus.client.sync import (
    ModbusSerialClient as pySerial,
    ModbusTcpClient as pyRtu,
)

from dali.driver.base import DALIDriver, SyncDALIDriver
from dali.frame import BackwardFrame, ForwardFrame

HWNAMES = (
    "B-1000-1",
    "E-8Di8Ro-1",
    "E-14Ro-1",
    "E-16Di-1",
    "E-8Di8Ro-1_P-11DiMb485",
    "E-14Ro-1_P-11DiR485-1",
    "E-16Di-1_P-11DiR485-1",
    "E-14Ro-1_U-14Ro-1",
    "E-16Di-1_U-14Ro-1",
    "E-14Ro-1_U-14Di-1",
    "E-16Di-1_U-14Di-1",
    "E-4Ai3Ao-1",
)
DA_OPT_TWICE = 0x8
DA_OPT_17BIT = 0x4

# debug logging related
DRIVER_CONSTRUCT = 0x0
DRIVER_EXTRACT = 0x1
_exco_str = {DRIVER_CONSTRUCT: "CONSTRUCT", DRIVER_EXTRACT: "EXTRACT"}


class fi(C.Union):
    _fields_ = [("i", C.c_uint), ("f", C.c_float)]


def reg2_float(r1, r2):
    x = fi()
    x.i = (r2 << 16) | r1
    return x.f


def float2reg(f):
    x = fi()
    x.f = f
    return (x.i & 0xFFFF), (x.i >> 16)


def u32i(low, high):
    val = low | (high << 16)
    if val <= 0x7FFFFFFF:
        return val
    return val - 0x100000000


def i32u(val):
    if val < 0:
        val = val + 0x100000000
    return (val & 0xFFFF, val >> 16)


def u2i(val):
    if val <= 0x7FFF:
        return val
    return val - 0x10000


def i2u(val):
    if val >= 0:
        return val
    return val + 0x10000


class RemoteArm:
    def __init__(self, host, unit=1, baud=19200, timeout=1):
        if host.startswith("/"):
            self.pymc = pySerial(
                method="rtu", port=host, baudrate=baud, timeout=timeout
            )
        else:
            self.pymc = pyRtu(host=host, port=502)
        self.unit = unit

    def set_speed(self, x):
        pass

    def close(self):
        self.pymc.close()

    def write_regs(self, reg, values, unit=-1):
        try:
            len(values)
            return self.pymc.write_registers(
                reg, values, unit=self.unit if unit == -1 else unit
            )
        except TypeError:
            pass
        return self.pymc.write_register(
            reg, values, unit=self.unit if unit == -1 else unit
        )

    def read_regs(self, reg, cnt, unit=-1):
        rr = self.pymc.read_holding_registers(
            reg, cnt, unit=self.unit if unit == -1 else unit
        )
        return rr.registers

    def write_coil(self, reg, val, unit=-1):
        return self.pymc.write_coil(reg, val, unit=self.unit if unit == -1 else unit)

    def reboot(self, unit=-1):
        self.pymc.write_coil(1002, 1, unit=self.unit if unit == -1 else unit)

    def showver(self):
        reg = self.read_regs(1000, 4)
        ver = reg[0]
        swver = ver >> 8
        if (swver) < 4:
            hw = (ver & 0xFF) >> 4
            hwver = ver & 0xF
            swsub = 0
        else:
            hw = reg[3] >> 8
            hwver = reg[3] & 0xFF
            swsub = ver & 0xFF
        try:
            hwname = HWNAMES[hw]
        except IndexError:
            hwname = "UNKNOWN"
        print("SW v%d.%d HW %s v%d" % (swver, swsub, hwname, hwver))
        print(
            "hwconfig:        %d x DI, %d x DO, %d x AI, %d x AO, %d x RS485"
            % (
                reg[1] >> 8,
                reg[1] & 0xFF,
                reg[2] >> 8,
                (reg[2] >> 4) & 0x0F,
                reg[2] & 0x0F,
            )
        )

    def Vref(self):
        # find reference voltage
        rr = self.read_regs(5, 1)
        self.vr1 = rr[0]
        rr = self.read_regs(1009, 1)
        self.vr2 = rr[0]
        return 3.3 * self.vr2 / self.vr1


def _log_frame(logger, exco, opt, ad, cm, st):
    msg = "{}\n" "    Type: {}\n" "    Address: {}\n" "    Command: {}\n"
    logger.info(msg.format(_exco_str[exco], hex(opt), hex(ad), hex(cm)))


class DALINoResponse(object):
    def __repr__(self):
        return "NO_RESPONSE"

    __str__ = __repr__


DALI_NO_RESPONSE = DALINoResponse()


class UnipiDALIDriver(DALIDriver):
    """``DALIDriver` implementation for UniPi DALI ModBus device.
    """

    debug = False
    logger = logging.getLogger("UnipiDALIDriver")
    # next sequence number
    _next_sn = 1

    def construct(self, command):
        """Data expected by DALI Modbus
             Reg_1 - 16bit - length, ...
             Reg_2 - 16bit - address,command
        """
        frame = command.frame
        if len(frame) == 16:
            opt = 0x2
            if command.is_config:
                opt |= DA_OPT_TWICE
            ad, cm1 = frame.as_byte_sequence
            reg2 = (ad << 8) | cm1
            reg1 = opt << 8
        elif len(frame) == 24:
            opt = 0x3
            if command.is_config:
                opt |= DA_OPT_TWICE
            ad, cm1, cm2 = frame.as_byte_sequence
            reg1 = (opt << 8) | ad
            reg2 = (cm1 << 8) | cm2
        else:
            raise ValueError("Unknown frame length: {}".format(len(frame)))

        if self.debug:
            _log_frame(self.logger, DRIVER_CONSTRUCT, opt, ad, cm1, 0)
        return (reg1, reg2)

    def extract(self, data):
        """ ----- """
        if data[0] == 0x100:
            return BackwardFrame(data[1])
        if data[0] == 0x200:
            return ForwardFrame(16, [data[1] >> 8, data[1] & 0xFF])
        else:
            return DALI_NO_RESPONSE

    def _get_sn(self):
        """Get next sequence number."""
        sn = self._next_sn
        if sn > 255:
            sn = self._next_sn = 1
        else:
            self._next_sn += 1
        return sn


class SyncUnipiDALIDriver(UnipiDALIDriver, SyncDALIDriver):
    """Synchronous implementation for UnipiDali"""

    def __init__(self, bus=0, unit=1):
        self.backend = RemoteArm("127.0.0.1", unit=unit)
        self.bus = bus
        self._sendreg = 13 + 2 * bus
        self._recvreg = 1 + 3 * bus
        self._fereg = 38 + int(bus / 2)

    def send(self, command, timeout=None):
        sleep(0.05)
        registers = self.construct(command)
        self.backend.write_regs(self._sendreg, registers)
        if command.is_config:
            sleep(0.05)
            self.backend.write_regs(self._sendreg, registers)
        counter1, = self.backend.read_regs(self._recvreg, 1)
        fe_counter1, = self.backend.read_regs(self._fereg, 1)
        try:
            needsResponse = command._response is not None
            frame = None
            # print(str(command) + str(needsResponse))
            if needsResponse:  # wait max 6*11ms
                for i in range(6):
                    sleep(0.011)
                    counter2, reg1, reg2 = self.backend.read_regs(self._recvreg, 3)
                    if counter1 != counter2:
                        # print ("%d %04x %04x" % (i, reg1, reg2))
                        frame = self.extract((reg1, reg2))
                        if isinstance(frame, BackwardFrame):
                            if command.response:
                                return command.response(frame)
                    if hasattr(command, "_cmdval") and command._cmdval == 0xA9:
                        fe_counter2, = self.backend.read_regs(self._fereg, 1)
                        if fe_counter1 != fe_counter2:
                            return command.response(BackwardFrame(0xFF))
                return command.response(None)
        except Exception as E:
            print(str(E))
        return DALI_NO_RESPONSE


def _test_sync(logger, command, bus=0, arg=0):
    print("Test sync driver")
    driver = SyncUnipiDALIDriver(bus=bus)
    driver.logger = logger
    driver.debug = True
    # driver.
    print("Response: {}".format(driver.send(command)))
    driver.backend.close()


if __name__ == "__main__":
    """Usage: python unipidali.py address value
    """
    from dali.gear.general import (
        Off,
        DAPC,
        Up,
        OnAndStepUp,
        IdentifyDevice,
        RecallMaxLevel,
    )
    from dali.gear.general import (
        QueryStatus,
        QueryDeviceType,
        QueryActualLevel,
        AddToGroup,
    )
    from dali.address import Short, Broadcast, Group
    from dali.bus import Bus
    import sys

    bus_driver = SyncUnipiDALIDriver(bus=1)
    logger = logging.getLogger("UnipiDALIDriver")
    bus_driver.logger = logger
    bus_driver.debug = True
    light_bus = Bus("1_01", bus_driver)
    # light_bus.assign_short_addresses()
    # sys.exit(0)
    # setup console logging
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

    # sync interface
    addr = Group(int(sys.argv[1]))
    # command to send
    # command = DAPC(addr, int(sys.argv[2]))
    # _test_sync(logger, command)
    command = QueryStatus(addr)
    _test_sync(logger, command, int(sys.argv[2]))
    # for i in range(20):
    command = DAPC(addr, 10)
    _test_sync(logger, command, int(sys.argv[2]))
    # #    sleep(1.00)
    # #   command = RecallMaxLevel(addr)
    #  #  _test_sync(logger, command, int(sys.argv[2]))
    #   # sleep(1.00)
    # command = OnAndStepUp(addr)
    # _test_sync(logger, command, int(sys.argv[2]))
    # command = QueryDeviceType(Broadcast())
    # _test_sync(logger, command)
    # command = QueryLightSourceType(addr)
    # _test_sync(logger, command)
    # command = QueryActualLevel(Broadcast())
    # _test_sync(logger, command)
    # command = RecallMaxLevel(addr)
    # command = RecallMinLevel(addr)
    # command = DAPC(Broadcast(), 235)
    # _test_sync(logger, command)
