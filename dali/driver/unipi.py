"""Driver for [unipi axon] based on [unipi implementation]


[unipi axon]: https://kb.unipi.technology/en:hw:01-axon
[unipi implementation]: https://git.unipi.technology/UniPi/unipi-python-lighting/commit/0975401ba6358d475ef46532ff5271bee46d601a
"""

import logging
from time import sleep

from pymodbus.client.sync import (
    ModbusSerialClient as pySerial,
    ModbusTcpClient as pyRtu,
)

from dali.driver.base import DALIDriver, SyncDALIDriver
from dali.frame import BackwardFrame, ForwardFrame
from dali.gear.general import Compare

DA_OPT_TWICE = 0x8


class RemoteArm:
    """Modbus interface for Unipi backend"""

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

    def __init__(self, host, unit=1, baud=19200, timeout=1):
        if host.startswith("/"):
            self.pymc = pySerial(
                method="rtu", port=host, baudrate=baud, timeout=timeout
            )
        else:
            self.pymc = pyRtu(host=host, port=502)
        self.unit = unit

    def close(self):
        self.pymc.close()

    def write_regs(self, reg, values, unit=None):
        try:
            iter(values)
        except TypeError:
            return self.pymc.write_register(reg, values, unit=unit or self.unit)
        else:
            return self.pymc.write_registers(reg, values, unit=unit or self.unit)

    def read_regs(self, reg, cnt, unit=None):
        rr = self.pymc.read_holding_registers(reg, cnt, unit=unit or self.unit)
        return rr.registers

    def write_coil(self, reg, val, unit=None):
        return self.pymc.write_coil(reg, val, unit=unit or self.unit)

    def reboot(self, unit=None):
        self.pymc.write_coil(1002, 1, unit=unit or self.unit)

    def version_info(self):
        """Dictionary representing the version information"""
        reg = self.read_regs(1000, 4)
        ver = reg[0]
        swver = ver >> 8
        if swver < 4:
            hw = (ver & 0xFF) >> 4
            hwver = ver & 0xF
            swsub = 0
        else:
            hw = reg[3] >> 8
            hwver = reg[3] & 0xFF
            swsub = ver & 0xFF

        try:
            hwname = self.HWNAMES[hw]
        except IndexError:
            hwname = "UNKNOWN"

        return {
            "software_version": swver,
            "software_sub_version": swsub,
            "hardware_name": hwname,
            "hardware_version": hwver,
            "hardware_config": {
                "DI": reg[1] >> 8,
                "DO": reg[1] & 0xFF,
                "AI": reg[2] >> 8,
                "AO": (reg[2] >> 4) & 0x0F,
                "RS485": reg[2] & 0x0F,
            },
        }

    def Vref(self):
        """Find reference voltage"""
        rr = self.read_regs(5, 1)
        self.vr1 = rr[0]
        rr = self.read_regs(1009, 1)
        self.vr2 = rr[0]
        return 3.3 * self.vr2 / self.vr1


class DALINoResponse:
    def __repr__(self):
        return "NO_RESPONSE"

    __str__ = __repr__


DALI_NO_RESPONSE = DALINoResponse()


class UnipiDALIDriver(DALIDriver):
    """DALIDriver` implementation for UniPi DALI ModBus device"""

    debug = False
    logger = logging.getLogger("UnipiDALIDriver")

    def __init__(self):
        # next sequence number
        self._next_sn = 0
        super().__init__()

    def construct(self, command):
        """
        Data expected by DALI Modbus
        - Reg_1 - 16bit - length, ...
        - Reg_2 - 16bit - address,command
        """
        frame = command.frame
        if len(frame) == 16:
            opt = 0x2
            if command.sendtwice:
                opt |= DA_OPT_TWICE
            ad, cm1 = frame.as_byte_sequence
            reg1 = opt << 8
            reg2 = (ad << 8) | cm1
        elif len(frame) == 24:
            opt = 0x3
            if command.sendtwice:
                opt |= DA_OPT_TWICE
            ad, cm1, cm2 = frame.as_byte_sequence
            reg1 = (opt << 8) | ad
            reg2 = (cm1 << 8) | cm2
        else:
            raise ValueError("Unknown frame length: {}".format(len(frame)))

        return (reg1, reg2)

    def extract(self, data):
        """Frames from modbus data"""
        if data[0] == 0x100:
            return BackwardFrame(data[1])
        if data[0] == 0x200:
            return ForwardFrame(16, [data[1] >> 8, data[1] & 0xFF])
        else:
            return DALI_NO_RESPONSE

    def _get_sn(self):
        """Get next sequence number."""
        self._next_sn = self._next_sn % 255
        return self._next_sn + 1


class SyncUnipiDALIDriver(UnipiDALIDriver, SyncDALIDriver):
    """Synchronous implementation for UnipiDali"""

    def __init__(self, bus=0, unit=1):
        self.backend = RemoteArm("127.0.0.1", unit=unit)
        self.bus = bus
        self._sendreg = 13 + 2 * bus
        self._recvreg = 1 + 3 * bus
        self._fereg = 38 + int(bus / 2)

    def _send_command(self, command):
        """Push command out"""
        sleep(0.05)
        registers = self.construct(command)
        self.backend.write_regs(self._sendreg, registers)
        if command.sendtwice:
            sleep(0.05)
            self.backend.write_regs(self._sendreg, registers)

    def _read_returning_frame(self, counter1):
        """Check returning frames for replying to"""
        counter2, reg1, reg2 = self.backend.read_regs(self._recvreg, 3)
        if counter1 != counter2:
            return self.extract((reg1, reg2))

    def _reply_compare_frame(self, command, fe_counter1):
        if hasattr(command, "_cmdval") and command._cmdval == Compare._cmdval:
            fe_counter2, = self.backend.read_regs(self._fereg, 1)
            return fe_counter1 != fe_counter2
        return False

    def send(self, command, timeout=None):
        # Push out
        self._send_command(command)

        # If the command does not expect a response, we're done
        if command.response is None:
            return DALI_NO_RESPONSE

        # Check for command responses
        counter1, = self.backend.read_regs(self._recvreg, 1)
        fe_counter1, = self.backend.read_regs(self._fereg, 1)
        try:
            for i in range(6):
                sleep(0.011)

                # Check for backward frames
                frame = self._read_returning_frame(counter1)
                if isinstance(frame, BackwardFrame) and command.response:
                    return command.response(frame)

                # Check whether the command is a Compare command
                if self._reply_compare_frame(command, fe_counter1):
                    return command.response(BackwardFrame(0xFF))
            return command.response(None)
        except Exception:
            pass
        return DALI_NO_RESPONSE
