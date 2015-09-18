"""DALI commands defined in IEC 62386-102 and IEC62386-202
"""

from dali import address
from dali.command import Command
from dali.command import ConfigCommand
from dali.command import GeneralCommand
from dali.command import QueryCommand
from dali.command import Response
from dali.command import ShortAddrSpecialCommand
from dali.command import SpecialCommand
from dali.command import YesNoResponse


class ArcPower(Command):
    """A command to set the arc power level directly.

    destination is a dali.address.Address or dali.device.Device object
    power is either an integer in the range 0..255, or one of two
    special strings:

    "OFF" sets the ballast off (same as power level 0)
    "MASK" stops any fade in progress (same as power level 255)

    The lamp will fade to the specified power according to its
    programmed fade time.  The MAX LEVEL and MIN LEVEL settings will
    be respected.
    """

    def __init__(self, destination, power):
        if power == "OFF":
            power = 0

        if power == "MASK":
            power = 255

        if not isinstance(power, int):
            raise ValueError("power must be an integer or string")

        if power < 0 or power > 255:
            raise ValueError("power must be in the range 0..255")

        self.destination = self._check_destination(destination)
        self.power = power

        Command.__init__(self, self.destination.addrbyte, power)

    @classmethod
    def from_bytes(cls, command):
        a, b = command
        if a & 0x01:
            return

        addr = address.from_byte(a)

        if addr is None:
            return

        return cls(addr, b)

    def __unicode__(self):
        if self.power == 0:
            power = "OFF"
        elif self.power == 255:
            power = "MASK"
        else:
            power = self.power
        return u"ArcPower(%s,%s)" % (self.destination, power)


class Off(GeneralCommand):
    """Extinguish the lamp immediately without fading.
    """
    _cmdval = 0x00


class Up(GeneralCommand):
    """Dim UP for 200ms at the selected FATE RATE.

    No change if the arc power output is already at the "MAX LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    This command shall only affect ballasts with burning lamps.
    No lamp shall be ignited with this command.
    """
    _cmdval = 0x01


class Down(GeneralCommand):
    """Dim DOWN for 200ms at the selected FADE RATE.

    No change if the arc power output is already at the "MIN LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    Lamp shall not be switched off via this command.
    """
    _cmdval = 0x02


class StepUp(GeneralCommand):
    """Set the actual arc power level one step higher immediately without
    fading.

    No change if the arc power output is already at the "MAX LEVEL".

    This command shall only affect ballasts with burning lamps.  No
    lamp shall be ignited with this command.
    """
    _cmdval = 0x03


class StepDown(GeneralCommand):
    """Set the actual arc power level one step lower immediately without
    fading.

    Lamps shall not be switched off via this command.

    No change if the arc power output is already at the "MIN LEVEL".
    """
    _cmdval = 0x04


class RecallMaxLevel(GeneralCommand):
    """Set the actual arc power level to the "MAX LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.
    """
    _cmdval = 0x05


class RecallMinLevel(GeneralCommand):
    """Set the actual arc power level to the "MIN LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.
    """
    _cmdval = 0x06


class StepDownAndOff(GeneralCommand):
    """Set the actual arc power level one step lower immediately without
    fading.

    If the actual arc power level is already at the "MIN LEVEL", the
    lamp shall be switched off by this command.
    """
    _cmdval = 0x07


class OnAndStepUp(GeneralCommand):
    """Set the actual arc power level one step higher immediately without
    fading.

    If the lamp is switched off, the lamp shall be ignited with this
    command and shall be set to the "MIN LEVEL".
    """
    _cmdval = 0x08


class GoToScene(GeneralCommand):
    """Set the actual arc power level to the value stored for the scene
    using the actual fade time.

    If the ballast does not belong to this scene, the arc power level
    remains unchanged.

    If the lamp is off, it shall be ignited with this command.

    If the value stored for this scene is zero and the lamp is lit
    then the lamp shall be switched off by this command after the fade
    time.
    """
    _cmdval = 0x10
    _hasparam = True


class Reset(ConfigCommand):
    """The variables in the persistent memory shall be changed to their
    reset values.  It is not guaranteed that any commands will be
    received properly within the next 300ms by a ballast acting on
    this command.
    """
    _cmdval = 0x20


class StoreActualLevelInDtr(ConfigCommand):
    """Store actual arc power level in the DTR without changing the
    current light intensity.
    """
    _cmdval = 0x21


class StoreDtrAsMaxLevel(ConfigCommand):
    """Save the value in the DTR as the new "MAX LEVEL".
    """
    _cmdval = 0x2a


class StoreDtrAsMinLevel(ConfigCommand):
    """Save the value in the DTR as the new "MIN LEVEL".  If this value
    is lower than the "PHYSICAL MIN LEVEL" of the ballast, then store
    the "PHYSICAL MIN LEVEL" as the new "MIN LEVEL".
    """
    _cmdval = 0x2b


class StoreDtrAsFailLevel(ConfigCommand):
    """Save the value in the DTR as the new "SYSTEM FAILURE LEVEL".
    """
    _cmdval = 0x2c


class StoreDtrAsPowerOnLevel(ConfigCommand):
    """Save the value in the DTR as the new "POWER ON LEVEL".
    """
    _cmdval = 0x2d


class StoreDtrAsFadeTime(ConfigCommand):
    """Set the "FADE TIME" in seconds according to the following formula:

    T=0.5(sqrt(pow(2,DTR))) seconds

    with DTR in the range 1..15

    If DTR is 0 then there will be no fade (<0.7s)

    The fade time specifies the time for changing the arc power level
    from the actual level to the requested level.  In the case of lamp
    off, the preheat and ignition time is not included in the fade
    time.

    The new fade time will be used after the reception of the next arc
    power command.  If a new fade time is set during a running fade
    process, the running fade process is not affected.
    """
    _cmdval = 0x2e


class StoreDtrAsFadeRate(ConfigCommand):
    """Set the "FADE RATE" in steps per second according to the following
    formula:

    F = 506/(sqrt(pow(2,DTR))) steps/s

    with DTR in the range 1..15

    The new fade time will be used after the reception of the next arc
    power command.  If a new fade time is set during a running fade
    process, the running fade process is not affected.
    """
    _cmdval = 0x2f


class StoreDtrAsScene(ConfigCommand):
    """Save the value in the DTR as the new level of the specified scene.
    The value 255 ("MASK") removes the ballast from the scene.
    """
    _cmdval = 0x40
    _hasparam = True


class RemoveFromScene(ConfigCommand):
    """Remove the ballast from the specified scene.

    This stores 255 ("MASK") in the specified scene register.
    """
    _cmdval = 0x50
    _hasparam = True


class AddToGroup(ConfigCommand):
    """Add the ballast to the specified group.
    """
    _cmdval = 0x60
    _hasparam = True


class RemoveFromGroup(ConfigCommand):
    """Remove the ballast from the specified group.
    """
    _cmdval = 0x70
    _hasparam = True


class StoreDtrAsShortAddress(ConfigCommand):
    """Save the value in the DTR as the new short address.

    The DTR must contain either:
    - (address<<1)|1 (i.e. 0AAAAAA1) to set a short address
    - 255 (i.e. 11111111) to remove the short address
    """
    _cmdval = 0x80


class QueryStatusResponse(Response):
    bits = ["status", "lamp failure", "arc power on", "limit error",
            "fade ready", "reset state", "missing short address",
            "power failure"]

    @property
    def status(self):
        v = self._value
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return l

    @property
    def ballast_status(self):
        return self._value & 0x01 != 0

    @property
    def lamp_failure(self):
        return self._value & 0x02 != 0

    @property
    def lamp_arc_power_on(self):
        return self._value & 0x04 != 0

    @property
    def limit_error(self):
        return self._value & 0x08 != 0

    @property
    def fade_ready(self):
        return self._value & 0x10 != 0

    @property
    def reset_state(self):
        return self._value & 0x20 != 0

    @property
    def missing_short_address(self):
        return self._value & 0x40 != 0

    @property
    def power_failure(self):
        return self._value & 0x80 != 0

    @property
    def error(self):
        """Is the ballast in any kind of error state?
        (Ballast not ok, lamp fail, missing short address)
        """
        return self._value & 0x43 != 0

    def __unicode__(self):
        return u",".join(self.status)


class QueryStatus(QueryCommand):
    """Retrieve a status byte from the ballast:

    Bit 0: status of ballast; 0 = OK
    Bit 1: lamp failure; 0 = OK
    Bit 2: lamp arc power on; 0 = OFF
    Bit 3: limit error; 0 = "last requested power was OFF or was
      between MIN..MAX LEVEL"
    Bit 4: fade ready; 0 = ready, 1 = running
    Bit 5: reset state? 0 = NO
    Bit 6: missing short address? 0 = NO
    Bit 7: power failure? 0 = "RESET" or an arc power control command has
      been received since the last power-on
    """
    _cmdval = 0x90
    _response = QueryStatusResponse


class QueryBallast(QueryCommand):
    """Ask if there is a ballast that is able to communicate.
    """
    _cmdval = 0x91
    _response = YesNoResponse


class QueryLampFailure(QueryCommand):
    """Ask if there is a lamp problem.
    """
    _cmdval = 0x92
    _response = YesNoResponse


class QueryLampPowerOn(QueryCommand):
    """Ask if there is a lamp operating.
    """
    _cmdval = 0x93
    _response = YesNoResponse


class QueryLimitError(QueryCommand):
    """Ask if the last requested arc power level could not be met because
    it was above the MAX LEVEL or below the MIN LEVEL.  (Power level
    of 0 is always "OFF" and is not an error.)
    """
    _cmdval = 0x94
    _response = YesNoResponse


class QueryResetState(QueryCommand):
    """Ask if the ballast is in "RESET STATE".
    """
    _cmdval = 0x95
    _response = YesNoResponse


class QueryMissingShortAddress(QueryCommand):
    """Ask if the ballast has no short address.  The response "YES" means
    that the ballast has no short address.
    """
    _cmdval = 0x96
    _response = YesNoResponse


class QueryVersionNumber(QueryCommand):
    """Ask for the version number of the IEC standard document met by the
    software and hardware of the ballast.  The high four bits of the
    answer represent the version number of the standard.  IEC-60929 is
    version number 0.
    """
    _cmdval = 0x97


class QueryDtr(QueryCommand):
    """Return the contents of the DTR.
    """
    _cmdval = 0x98

QueryContentDtr = QueryDtr


class QueryDeviceTypeResponse(Response):
    _types = {0: u"fluorescent lamp",
              1: u"emergency lighting",
              2: u"HID lamp",
              3: u"low voltage halogen lamp",
              4: u"incandescent lamp dimmer",
              5: u"dc-controlled dimmer",
              6: u"LED lamp"}

    def __unicode__(self):
        if self.value in self._types:
            return self._types[self.value]

        return unicode(self.value)


class QueryDeviceType(QueryCommand):
    """Return the device type.  Currently defined:

    0: fluorescent lamps
    1: emergency lighting
    2: HID lamps
    3: low voltage halogen lamps
    4: incandescent lamps
    5: DC-controlled dimmers
    6: LED lamps

    The device type affects which application extended commands the
    device will respond to.
    """
    _cmdval = 0x99
    _response = QueryDeviceTypeResponse


class QueryPhysicalMinimumLevel(QueryCommand):
    """Return the physical minimum level for this device.
    """
    _cmdval = 0x9a


class QueryPowerFailure(QueryCommand):
    """Ask whether the device has not received a "RESET" or arc power
    control command since the last power-on.
    """
    _cmdval = 0x9b
    _response = YesNoResponse


class QueryDtr1(QueryCommand):
    """Return the contents of DTR1.

    NB not checked against IEC 62386
    """
    _cmdval = 0x9c

QueryContentDtr1 = QueryDtr1


class QueryDtr2(QueryCommand):
    """Return the contents of DTR2.

    NB not checked against IEC 62386

    """
    _cmdval = 0x9d

QueryContentDtr2 = QueryDtr2


class QueryActualLevel(QueryCommand):
    """Return the current actual power level.  During preheating and if a
    lamp error occurs the answer will be 0xff ("MASK").
    """
    _cmdval = 0xa0


class QueryMaxLevel(QueryCommand):
    """Return "MAX LEVEL".
    """
    _cmdval = 0xa1


class QueryMinLevel(QueryCommand):
    """Return "MIN LEVEL".
    """
    _cmdval = 0xa2


class QueryPowerOnLevel(QueryCommand):
    """Return "POWER ON LEVEL".
    """
    _cmdval = 0xa3


class QueryFailureLevel(QueryCommand):
    """Return "SYSTEM FAILURE LEVEL".
    """
    _cmdval = 0xa4


class QueryFadeTimeAndRateResponse(Response):

    @property
    def fade_time(self):
        return self._value >> 4

    @property
    def fade_rate(self):
        return self._value & 0x0f

    def __unicode__(self):
        return u"Fade time: {0}; Fade rate: {1}".format(
            self.fade_time,
            self.fade_rate
        )


class QueryFadeTimeAndRate(QueryCommand):
    """Return the configured fade time and rate.

    The fade time set by "StoreDtrAsFadeTime" is in the upper four
    bits of the response.  The rade rate set by "StoreDtrAsFadeRate"
    is in the lower four bits of the response.
    """
    _cmdval = 0xa5
    _response = QueryFadeTimeAndRateResponse


class QuerySceneLevel(QueryCommand):
    """Return the level set for the specified scene, or 255 ("MASK") if
    the device is not part of the scene.
    """
    _cmdval = 0xb0
    _hasparam = True


class QueryGroupsLSB(QueryCommand):
    """Return the device membership of groups 0-7 with group 0 in the
    least-significant bit of the response.
    """
    _cmdval = 0xc0


class QueryGroupsMSB(QueryCommand):
    """Return the device membership of groups 8-15 with group 8 in the
    least-significant bit of the response.
    """
    _cmdval = 0xc1


class QueryRandomAddressH(QueryCommand):
    """Return the 8 high bits of the random address.
    """
    _cmdval = 0xc2


class QueryRandomAddressM(QueryCommand):
    """Return the 8 mid bits of the random address.
    """
    _cmdval = 0xc3


class QueryRandomAddressL(QueryCommand):
    """Return the 8 low bits of the random address.
    """
    _cmdval = 0xc4


class ReadMemoryLocation(QueryCommand):
    """Read a byte from memory.  The bank is specified in DTR1.  The
    offset in the bank is specified in DTR.  The byte is returned as
    the response.  DTR is incremented.  Another byte is read into DTR2.

    NB not checked with IEC 62386
    """
    _cmdval = 0xc5


class Terminate(SpecialCommand):
    """All special mode processes shall be terminated.
    """
    _cmdval = 0xa1


class SetDtr(SpecialCommand):
    """This is a broadcast command to set the value of the DTR register.
    """
    _cmdval = 0xa3
    _hasparam = True


class Initialise(Command):
    """This command shall start or re-trigger a timer for 15 minutes; the
    addressing commands shall only be processed within this period.
    All other commands shall still be processed during this period.

    This time period shall be aborted with the "Terminate" command.

    Ballasts shall react as follows:

    * if broadcast is True then all ballasts shall react

    * if broadcast is False and address is None then ballasts without
      a short address shall react

    * if broadcast is False and address is an integer 0..63 then
      ballasts with the address supplied shall react
    """
    _isconfig = True
    _cmdval = 0xa5

    def __init__(self, broadcast=False, address=None):
        if broadcast and address is not None:
            raise ValueError("can't specify address when broadcasting")
        if address is not None:
            if not isinstance(address, int):
                raise ValueError("address must be an integer")
            if address < 0 or address > 63:
                raise ValueError("address must be in the range 0..63")
        self.broadcast = broadcast
        self.address = address

    @property
    def command(self):
        if self.broadcast:
            b = 0
        elif self.address is None:
            b = 0xff
        else:
            b = (self.address << 1) | 1
        return (self._cmdval, b)

    @classmethod
    def from_bytes(cls, command):
        a, b = command
        if a == cls._cmdval:
            if b == 0:
                return cls(broadcast=True)
            if b == 0xff:
                return cls(address=None)
            if (b & 0x81) == 0x01:
                return cls(address=(b >> 1))

    def __unicode__(self):
        if self.broadcast:
            return u"Initialise(broadcast=True)"
        return u"Initialise(address={})".format(self.address)


class Randomise(SpecialCommand):
    """The ballast shall generate a new 24-bit random address.  The new
    random address shall be available within a time period of 100ms.
    """
    _cmdval = 0xa7
    _isconfig = True


class Compare(SpecialCommand):
    """The ballast shall compare its 24-bit random address with the
    combined search address stored in SearchAddrH, SearchAddrM and
    SearchAddrL.  If its random address is smaller or equal to the
    search address and the ballast is not withdrawn then the ballast
    shall generate a query "YES".
    """
    _cmdval = 0xa9
    _isquery = True
    _response = YesNoResponse


class Withdraw(SpecialCommand):
    """The ballast that has a 24-bit random address equal to the combined
    search address stored in SearchAddrH, SearchAddrM and SearchAddrL
    snall no longer respond to the compare command.  This ballast
    shall not be excluded from the initialisation process.
    """
    _cmdval = 0xab


class SetSearchAddrH(SpecialCommand):
    """Set the high 8 bits of the search address.
    """
    _cmdval = 0xb1
    _hasparam = True


class SetSearchAddrM(SpecialCommand):
    """Set the mid 8 bits of the search address.
    """
    _cmdval = 0xb3
    _hasparam = True


class SetSearchAddrL(SpecialCommand):
    """Set the low 8 bits of the search address.
    """
    _cmdval = 0xb5
    _hasparam = True


class ProgramShortAddress(ShortAddrSpecialCommand):
    """The ballast shall store the received 6-bit address as its short
    address if it is selected.  It is selected if:

    * the ballast's 24-bit random address is equal to the address in
      SearchAddrH, SearchAddrM and SearchAddrL

    * physical selection has been detected (the lamp is electrically
      disconnected after reception of command PhysicalSelection())
    """
    _cmdval = 0xb7


class DeleteShortAddress(SpecialCommand):
    """The ballast shall delete its short address if it is selected.
    Selection criteria is as for ProgramShortAddress().
    """
    _cmdval = 0xb7

    @property
    def command(self):
        return (self._cmdval, 0xff)

    @classmethod
    def from_bytes(cls, command):
        a, b = command
        if a == cls._cmdval and b == 0xff:
            return cls()

    def __unicode__(self):
        return u"DeleteShortAddress()"


class VerifyShortAddress(ShortAddrSpecialCommand):
    """The ballast shall give an answer "YES" if the received short
    address is equal to its own short address.
    """
    _cmdval = 0xb9
    _isquery = True
    _response = YesNoResponse


class QueryShortAddress(SpecialCommand):
    """The ballast shall send the short address if the random address is
    the same as the search address or the ballast is physically
    selected.  The answer will be in the format (address<<1)|1 if the
    short address is programmed, or "MASK" (0xff) if there is no short
    address stored.
    """
    _cmdval = 0xbb
    _isquery = True


class PhysicalSelection(SpecialCommand):
    """The ballast shall cancel its selection and shall set "Physical
    Selection Mode".  In this mode the comparison of the random
    address and search address shall be disabled; the ballast becomes
    selected when its lamp is electrically disconnected.
    """
    _cmdval = 0xbd


class EnableDeviceType(SpecialCommand):
    """This command shall be sent before an application extended command.
    This command can be processed without the use of the Initialise()
    command.  This command shall not be used for device type 0.
    """
    _cmdval = 0xc1
    _hasparam = True


class SetDtr1(SpecialCommand):
    """This is a broadcast command to set the value of the DTR1 register.

    NB not checked against IEC 62386 yet
    """
    _cmdval = 0xc3
    _hasparam = True


class SetDtr2(SpecialCommand):
    """This is a broadcast command to set the value of the DTR2 register.

    NB not checked against IEC 62386 yet
    """
    _cmdval = 0xc5
    _hasparam = True


###############################################################################
# Application extended control commands for device type 1 (emergency lighting)
###############################################################################

class EmergencyLightingCommand(GeneralCommand):
    _devicetype = 1


class EmergencyLightingControlCommand(EmergencyLightingCommand):
    """An emergency lighting control command as defined in section
    11.3.4.1 of IEC 62386-202:2009
    """
    _isconfig = True


class Rest(EmergencyLightingControlCommand):
    """If this command is received when the control gear is in emergency
    mode then the lamp shall be extinguished.

    Rest mode shall revert to normal mode in the event of restoration
    of normal supply, or on receipt of command "ReLightResetInhibit"
    if re-light in rest mode is supported.
    """
    _cmdval = 0xe0


class Inhibit(EmergencyLightingControlCommand):
    """If the control gear is in normal mode on receipt of this command,
    bit 0 of the Emergency Status byte shall be set and the control
    gear shall go into inhibit mode.

    In inhibit mode, a 15 minute timer starts.  Normal mode is resumed
    on expiry of this timer, or on receipt of command
    "ReLightResetInhibit".

    If mains power is lost while in inhibit mode, rest mode will be entered.
    """
    _cmdval = 0xe1


class ReLightResetInhibit(EmergencyLightingControlCommand):
    """This command cancels the inhibit timer.  If the control gear is in
    rest mode and re-light in rest mode is supported then the control
    gear will enter emergency mode.
    """
    _cmdval = 0xe2


class StartFunctionTest(EmergencyLightingControlCommand):
    """The control gear is requested to perform a function test.  A
    function test is a brief test of the operation of the lamp, the
    battery and the changeover circuit.

    If a function test is already in progress then this command is
    ignored.

    If the function test cannot be started immediately then it will be
    set as pending until it can be performed.  Bit 4 of the Emergency
    Status byte will be set.
    """
    _cmdval = 0xe3


class StartDurationTest(EmergencyLightingControlCommand):
    """The control gear is requested to perform a duration test.  A
    duration test tests that the lamp can be operated for the rated
    duration from the battery.

    If a duration test is already in progress then this command is
    ignored.

    If the duration test cannot be started immediately then it will be
    set as pending until it can be performed.  Bit 5 of the Emergency
    Status byte will be set.
    """
    _cmdval = 0xe4


class StopTest(EmergencyLightingControlCommand):
    """Any running tests are stopped and any pending tests are cancelled.
    Bits 4 and 5 of the Emergency Status byte will be cleared.
    """
    _cmdval = 0xe5


class ResetFunctionTestDoneFlag(EmergencyLightingControlCommand):
    """The "function test done and result valid" flag (bit 1 of the
    Emergency Status byte) shall be cleared.
    """
    _cmdval = 0xe6


class ResetDurationTestDoneFlag(EmergencyLightingControlCommand):
    """The "duration test done and result valid" flag (bit 2 of the
    Emergency Status byte) shall be cleared.
    """
    _cmdval = 0xe7


class ResetLampTime(EmergencyLightingControlCommand):
    """The lamp emergency time and lamp total operation time counters
    shall be reset.
    """
    _cmdval = 0xe8


class EmergencyLightingConfigCommand(EmergencyLightingCommand):
    """An emergency lighting configuration command as defined in section
    11.3.4.2 of IEC 62386-202:2009
    """
    _isconfig = True


class StoreDtrAsEmergencyLevel(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Emergency Level.
    """
    _cmdval = 0xe9


class StoreTestDelayTimeHighByte(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the high byte of Test Delay Time.

    Test Delay Time is a 16-bit quantity in quarters of an hour.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xea


class StoreTestDelayTimeLowByte(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the low byte of Test Delay Time.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xeb


class StoreFunctionTestInterval(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Function Test Interval.  This is the
    number of days (1..255) between automatic function tests.  0
    disables automatic function tests.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xec


class StoreDurationTestInterval(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Duration Test Interval.  This is the
    number of weeks (1..97) between automatic duration tests.  0
    disables automatic duration tests.

    This command is ignored if automatic testing is not supported.
    """
    _cmdval = 0xed


class StoreTestExecutionTimeout(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Test Execution Timeout.  This is
    defined in days (1..255).  A value of 0 means 15 minutes.

    The Test Execution Timeout period starts when a test becomes
    pending.  If the period expires without the test being finished,
    it shall be flagged as a failure in the Failure Status byte but
    the test shall remain pending.
    """
    _cmdval = 0xee


class StoreProlongTime(EmergencyLightingConfigCommand):
    """DTR0 shall be stored as the Prolong Time.  This is defined in 30s
    units (0..255) and is used to determine the length of time the
    control gear will remain in emergency mode after mains power is
    restored.
    """
    _cmdval = 0xef


class StartIdentification(EmergencyLightingConfigCommand):
    """The control gear shall start or restart a ten-second procedure
    intended to enable the operator to identify it.
    """
    _cmdval = 0xf0


class EmergencyLightingQueryCommand(EmergencyLightingCommand):
    """An emergency lighting query command as defined in section 11.3.4.3
    of IEC 62386-202:2009
    """
    _isquery = True
    _response = Response


class QueryBatteryCharge(EmergencyLightingQueryCommand):
    """Query the actual battery charge level from 0 (the deep discharge
    point) to 254 (fully charged).  255 (MASK) indicates the value is
    unknown, possibly because the control gear has not performed a
    successful duration test.
    """
    _cmdval = 0xf1


class QueryTestTiming(EmergencyLightingQueryCommand):
    """The answer depends on the content of DTR0:

    0 - time until the next function test in quarters of an hour (high byte)
    1 - time until the next function test in quarters of an hour (low byte)
    2 - time until the next duration test in quarters of an hour (high byte)
    3 - time until the next duration test in quarters of an hour (low byte)
    4 - function test interval time in days (or 0)
    5 - duration test interval time in weeks (or 0)
    6 - test execution timeout in days
    7 - prolong time in 30s intervals

    When the high byte of a 16-bit value is read, the low byte is
    placed in DTR1 to enable atomic reads.  If automatic testing is
    not supported then queries 0-3 will return 255 (MASK).
    """
    _cmdval = 0xf2


class QueryDurationTestResult(EmergencyLightingQueryCommand):
    """Returns the duration test result in 120s (2min) units.  255 means
    the maximum value or longer.
    """
    _cmdval = 0xf3


class QueryLampEmergencyTime(EmergencyLightingQueryCommand):
    """Returns the accumulated lamp functioning time with the battery as
    power source in hours.  255 means the maximum value or longer.
    """
    _cmdval = 0xf4


class QueryLampTotalOperationTime(EmergencyLightingQueryCommand):
    """Returns the accumulated lamp total functioning time in 4-hour
    units.  255 means the maximum value of 1016h or longer.

    If the lamp is operated by another control device (for example
    where the emercency lighting control device does not support
    operating the lamp from the mains) this time may not include the
    time the lamp is operated by the other control device.
    """
    _cmdval = 0xf5


class QueryEmergencyLevel(EmergencyLightingQueryCommand):
    """Return the Emergency Level, or MASK (255) if it is unknown.
    """
    _cmdval = 0xf6


class QueryEmergencyMinLevel(EmergencyLightingQueryCommand):
    """Return the Emergency Min Level, or MASK (255) if it is unknown.
    """
    _cmdval = 0xf7


class QueryEmergencyMaxLevel(EmergencyLightingQueryCommand):
    """Return the Emergency Max Level, or MASK (255) if it is unknown.
    """
    _cmdval = 0xf8


class QueryRatedDuration(EmergencyLightingQueryCommand):
    """Return the rated duration in units of 2min.  255 means 510 min or
    longer.
    """
    _cmdval = 0xf9


class QueryEmergencyModeResponse(Response):
    bits = ["rest mode", "normal mode", "emergency mode",
            "extended emergency mode", "function test", "duration test",
            "hardwired inhibit active", "hardwired switch on"]

    @property
    def status(self):
        v = self._value
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return l

    @property
    def hardwired_inhibit(self):
        return self._value & 0x40 != 0

    @property
    def hardwired_switch(self):
        return self._value & 0x80 != 0

    @property
    def mode(self):
        """Operating mode of the emergency control gear.  Only one of bits 0-5
        should be set at once, but we support returning a sensible
        response even when multiple bits are set.
        """
        v = self._value & 0x3f
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return ",".join(l)

    def __unicode__(self):
        return u",".join(self.status)


class QueryEmergencyMode(EmergencyLightingQueryCommand):
    """Return the Emergency Mode Information byte.
    """
    _cmdval = 0xfa
    _response = QueryEmergencyModeResponse


class QueryEmergencyFeaturesResponse(Response):
    bits = ["integral emergency control gear", "maintained control gear",
            "switched maintained control gear", "auto test capability",
            "adjustable emergency level", "hardwired inhibit supported",
            "physical selection supported", "re-light in rest mode supported"]

    @property
    def auto_test_supported(self):
        return self._value & 0x08 != 0

    @property
    def status(self):
        v = self._value
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return l

    def __unicode__(self):
        return u",".join(self.status)


class QueryEmergencyFeatures(EmergencyLightingQueryCommand):
    """Return the Features information byte.
    """
    _cmdval = 0xfb
    _response = QueryEmergencyFeaturesResponse


class QueryEmergencyFailureStatusResponse(Response):
    bits = ["circuit failure", "battery duration failure", "battery failure",
            "emergency lamp failure", "function test max delay exceeded",
            "duration test max delay exceeded", "function test failed",
            "duration test failed"]

    @property
    def status(self):
        v = self._value
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return l

    def __unicode__(self):
        return u",".join(self.status)


class QueryEmergencyFailureStatus(EmergencyLightingQueryCommand):
    """Return the Failure Status information byte.
    """
    _cmdval = 0xfc
    _response = QueryEmergencyFailureStatusResponse


class QueryEmergencyStatusResponse(Response):
    bits = ["inhibit mode", "function test done and result valid",
            "duration test done and result valid", "battery fully charged",
            "function test pending", "duration test pending",
            "identification active", "physically selected"]

    @property
    def status(self):
        v = self._value
        l = []
        for b in self.bits:
            if v & 0x01:
                l.append(b)
            v = (v >> 1)
        return l

    def __unicode__(self):
        return u",".join(self.status)


class QueryEmergencyStatus(EmergencyLightingQueryCommand):
    """Return the Emergency Status information byte.
    """
    _cmdval = 0xfd
    _response = QueryEmergencyStatusResponse


class PerformDtrSelectedFunction(EmergencyLightingControlCommand):
    """Perform a function depending on the value in DTR0:

    0 - restore factory default settings
    """
    _cmdval = 0xfe


class QueryExtendedVersionNumber(EmergencyLightingCommand):
    """Returns 1.
    """
    _cmdval = 0xff
