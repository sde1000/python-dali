from dali.command import Command
from dali.driver.base import SyncDALIDriver, DALIDriver
from dali.frame import BackwardFrame
import logging
import sys

import serial
import threading
import time

DALI_PACKET_SIZE = {"j": 8, "h": 16, "l": 24, "m": 25}
DALI_PACKET_PREFIX = {v: k for k, v in DALI_PACKET_SIZE.items()}


class DaliHatSerialDriver(DALIDriver):
    """Driver for communicating with DALI devices over a serial connection."""

    def __init__(self, port="/dev/ttyS0", LOG=None):
        """Initialize the serial connection to the DALI interface."""
        self.port = port
        self.lock = threading.RLock()
        self.buffer = []
        if not LOG:
            self.LOG = logging.getLogger("AtxLedDaliDriver")
            handler = logging.StreamHandler(sys.stdout)
            self.LOG.addHandler(handler)
        else:
            self.LOG = LOG
        try:
            self.conn = serial.Serial(
                port=self.port,
                baudrate=19200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.2,
            )
        except Exception as e:
            self.LOG.exception("Could not open serial connection: %s", e)
            self.conn = None


    def read_line(self):
        """Read the next line from the buffer, refilling the buffer if necessary."""
        with self.lock:
            while not self.buffer:
                line = self.conn.read_until(b"\n").decode("ascii")
                if not line:
                    return ""
                self.buffer.append(line)
            return self.buffer.pop(0)

    def construct(self, command):
        """Construct a DALI command to be sent over the serial connection."""
        assert isinstance(command, Command)
        f = command.frame
        packet_size = len(f)
        prefix = DALI_PACKET_PREFIX[packet_size]
        if command.sendtwice and packet_size == 16:
            prefix = "t"
        data = "".join(["{:02X}".format(byte) for byte in f.pack])
        command_str = (f"{prefix}{data}\n").encode("ascii")
        return command_str

    def extract(self, data):
        """Parse the response from the serial device and return the corresponding frame."""
        if data.startswith("J"):
            try:
                data = int(data[1:], 16)
                return BackwardFrame(data)
            except ValueError as e:
                self.LOG.error(f"Failed to parse response '{data}': {e}")
        return None

    def close(self):
        """Close the serial connection."""
        if self.conn:
            self.conn.close()


class SyncDaliHatDriver(DaliHatSerialDriver, SyncDALIDriver):
    """Synchronous DALI driver."""

    def send(self, command: Command):
        """Send a command to the DALI interface and wait for a response."""
        with self.lock:
            lines = []
            last_resp = None
            send_twice = command.sendtwice
            cmd = self.construct(command)
            self.LOG.debug("command string sent: %r", cmd)
            self.conn.write(cmd)
            REPS = 5
            i = 0
            already_resent = False
            resent_times = 0
            resp = None
            while i < REPS:
                i += 1
                resp = self.read_line()
                self.LOG.debug("raw response received: %r", resp)
                resend = False
                if cmd[:3] not in ["hB1", "hB3", "hB5"]:
                    if resp and resp[0] in {"N", "J"}:
                        if send_twice:
                            if last_resp:
                                if last_resp == resp:
                                    resp = self.extract(resp)
                                    break
                                resend = True
                                last_resp = None
                            else:
                                last_resp = resp
                        else:
                            resp = self.extract(resp)
                            break
                    elif resp and resp[0] in {"X", "Z", ""}:
                        time.sleep(0.1)
                        collision_bytes = None
                        while collision_bytes != "":
                            collision_bytes = self.read_line()
                        if resp[0] == "X":
                            break
                        self.LOG.info(
                            "got conflict (%s) sending %r, sending again", resp, cmd
                        )
                        last_resp = None
                        resend = True
                    elif resp:
                        lines.append(resp)

                    resp = None
                    if resend and not already_resent:
                        self.conn.write((cmd).encode("ascii"))
                        REPS += 1 + send_twice
                        already_resent = True
                else:
                    if resp and resp[0] == "N":
                        resp = self.extract(resp)
                        break
                    elif resp and resp[0] in {"X", "Z", ""}:
                        time.sleep(0.1)
                        collision_bytes = None
                        while collision_bytes != "":
                            collision_bytes = self.read_line()
                    elif resp:
                        last_resp = None
                        resend = True
                if resend and resent_times < 5:
                    self.conn.write(cmd.encode("ascii"))
                    REPS += 1 + send_twice
                    resent_times += 1
            if command.is_query:
                return command.response(resp)
            return resp


if __name__ == "__main__":
    """Usage: python atxled.py address value"""
    from dali.gear.general import DAPC

    logging.basicConfig(level=logging.DEBUG)
    serial_port = "/dev/ttyS0"
    dali_driver = SyncDaliHatDriver()
    command = DAPC(int(sys.argv[1]), int(sys.argv[2]))
    response = dali_driver.send(command)
    print("DALI response:", response)
    dali_driver.close()
