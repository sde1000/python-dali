"""Commands and responses from IEC 62386 part 102.

Command names are given in the standard in ALL CAPS.  They have been
converted to CamelCase here, for example ALL CAPS -> AllCaps.

Where a command name is or contains an abbreviation, for example DAPC
or DTR0, the abbreviation has been kept in capitals.
"""

from dali import command
from dali import address
from dali import frame


class _GearCommand(command.Command):
    _framesize = 16

    _gearcommands = []

    @classmethod
    def _register_subclass(cls, subclass):
        cls._gearcommands.append(subclass)

    @classmethod
    def from_frame(cls, f, devicetype=0):
        for gc in cls._gearcommands:
            r = gc.from_frame(f, devicetype=devicetype)
            if r:
                return r
        return UnknownGearCommand(f)

class UnknownGearCommand(_GearCommand):
    """An unknown command addressed to control gear.
    """
    @classmethod
    def from_frame(cls, f, devicetype=0):
        return

###############################################################################
# Commands from Table 15 start here
###############################################################################

class _StandardCommand(_GearCommand):
    """A standard command as defined in Table 15 of IEC 62386-102

    A command addressed to control gear that has a destination address
    and which is not a direct arc power command.  Optionally has a
    4-bit parameter which is used to specify group or scene as
    appropriate.

    The commands are declared as subclasses which override _cmdval to
    specify the opcode byte and override _hasparam to True if the
    4-bit parameter is to be used as the least significant 4 bits of
    the opcode byte.
    """
    _cmdval = None
    _hasparam = False

    def __init__(self, destination, *args):
        if self._cmdval is None:
            raise NotImplementedError

        if self._hasparam:
            if len(args) != 1:
                raise TypeError(
                    "%s.__init__() takes exactly 3 arguments (%d given)" % (
                        self.__class__.__name__, len(args) + 2))

            param = args[0]

            if not isinstance(param, int):
                raise ValueError("param must be an integer")

            if param < 0 or param > 15:
                raise ValueError("param must be in the range 0..15")

            self.param = param

        else:
            if len(args) != 0:
                raise TypeError(
                    "%s.__init__() takes exactly 2 arguments (%d given)" % (
                        self.__class__.__name__, len(args) + 2))
            param = 0

        self.destination = self._check_destination(destination)

        f = frame.ForwardFrame(16, 0x100 | self._cmdval | param)
        self.destination.add_to_frame(f)

        super().__init__(f)

    # (devicetype, opcode) -> commandclass
    _opcodes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        if subclass.__name__[0] == '_':
            return
        if subclass._hasparam:
            for x in range(0, 0x10):
                cls._opcodes[(subclass.devicetype, subclass._cmdval + x)] = subclass
        else:
            cls._opcodes[(subclass.devicetype, subclass._cmdval)] = subclass

    @classmethod
    def from_frame(cls, frame, devicetype=0):
        if not frame[8]:
            # It's a direct arc power control command
            return

        addr = address.from_frame(frame)

        if addr is None:
            # It's probably a _SpecialCommand
            return

        opcode = frame[7:0]

        cc = cls._opcodes.get((devicetype, opcode))
        if not cc:
            return UnknownGearCommand(frame)

        if cc._hasparam:
            return cc(addr, opcode & 0x0f)

        return cc(addr)

    def __str__(self):
        if self._hasparam:
            return "%s(%s,%s)" % (
                self.__class__.__name__,
                self.destination,
                self.param
            )
        return "%s(%s)" % (self.__class__.__name__, self.destination)


class DAPC(_GearCommand):
    """Direct Arc Power Control

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

        f = frame.ForwardFrame(16, power)
        self.destination.add_to_frame(f)
        super().__init__(f)

    @classmethod
    def from_frame(cls, f, devicetype=0):
        if f[8]:
            return
        addr = address.from_frame(f)
        if addr is None:
            return
        return cls(addr, f[7:0])

    def __str__(self):
        if self.power == 0:
            power = "OFF"
        elif self.power == 255:
            power = "MASK"
        else:
            power = self.power
        return "ArcPower(%s,%s)" % (self.destination, power)


class Off(_StandardCommand):
    """Extinguish the lamp immediately without fading."""
    _cmdval = 0x00


class Up(_StandardCommand):
    """Dim UP for 200ms at the selected FATE RATE.

    No change if the arc power output is already at the "MAX LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    This command shall only affect ballasts with burning lamps.
    No lamp shall be ignited with this command.
    """
    _cmdval = 0x01


class Down(_StandardCommand):
    """Dim DOWN for 200ms at the selected FADE RATE.

    No change if the arc power output is already at the "MIN LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    Lamp shall not be switched off via this command.
    """
    _cmdval = 0x02


class StepUp(_StandardCommand):
    """Set the actual arc power level one step higher immediately without
    fading.

    No change if the arc power output is already at the "MAX LEVEL".

    This command shall only affect ballasts with burning lamps.  No
    lamp shall be ignited with this command.
    """
    _cmdval = 0x03


class StepDown(_StandardCommand):
    """Set the actual arc power level one step lower immediately without
    fading.

    Lamps shall not be switched off via this command.

    No change if the arc power output is already at the "MIN LEVEL".
    """
    _cmdval = 0x04


class RecallMaxLevel(_StandardCommand):
    """Set the actual arc power level to the "MAX LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.
    """
    _cmdval = 0x05


class RecallMinLevel(_StandardCommand):
    """Set the actual arc power level to the "MIN LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.
    """
    _cmdval = 0x06


class StepDownAndOff(_StandardCommand):
    """Set the actual arc power level one step lower immediately without
    fading.

    If the actual arc power level is already at the "MIN LEVEL", the
    lamp shall be switched off by this command.
    """
    _cmdval = 0x07


class OnAndStepUp(_StandardCommand):
    """Set the actual arc power level one step higher immediately without
    fading.

    If the lamp is switched off, the lamp shall be ignited with this
    command and shall be set to the "MIN LEVEL".
    """
    _cmdval = 0x08


class EnableDAPCSequence(_StandardCommand):
    """Enable DAPC Sequence

    Indicates the start of a command iteration of DAPC(level)
    commands.

    The control gear shall temporarily use a fade time of 200ms while
    the command iteration is active independent of the actual
    fade/extended fade time.

    The DAPC sequence shall end if 200ms elapse without the control
    gear receiving a DAPC(level) command.  The sequence shall be
    aborted on reception of an indirect arc power control command.
    """
    _cmdval = 0x09


class GoToLastActiveLevel(_StandardCommand):
    """Go to last active level

    targetLevel shall be calculated based on lastActiveLevel.  The
    transition from actualLevel to targetLevel shall start using the
    set fade time.
    """
    _cmdval = 0x0a


class ContinuousUp(_StandardCommand):
    """Dim up using the set fade rate.

    targetLevel shall be set to maxLevel and a fade shall be started
    using the set fade rate. The fade shall stop when maxLevel is
    reached.
    """
    _cmdval = 0x0b


class ContinuousDown(_StandardCommand):
    """Dim down using the set fade rate.

    targetLevel shall be set to minLevel and a fade shall be started
    using the set fade rate. The fade shall stop when minLevel is
    reached.
    """
    _cmdval = 0x0c


class GoToScene(_StandardCommand):
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


class Reset(_StandardCommand):
    """The variables in the persistent memory shall be changed to their
    reset values.  It is not guaranteed that any commands will be
    received properly within the next 300ms by a ballast acting on
    this command.
    """
    _cmdval = 0x20
    sendtwice = True


class StoreActualLevelInDTR0(_StandardCommand):
    """Store actual arc power level in the DTR without changing the
    current light intensity.
    """
    _cmdval = 0x21
    uses_dtr0 = True
    sendtwice = True


class SavePersistentVariables(_StandardCommand):
    """Save persistent variables to non-volatile memory

    All variables identified as non-volatile shall be stored to
    non-volatile memory.  The control gear might not react to commands
    for up to 300ms after reception of this command.  This command is
    recommended to be used typically after commissioning.
    """
    _cmdval = 0x22
    sendtwice = True


class SetOperatingMode(_StandardCommand):
    """Set operatingMode to DTR0.

    If DTR0 does not correspond to an implemented operating mode, the
    command shall be ignored.
    """
    _cmdval = 0x23
    uses_dtr0 = True
    sendtwice = True


class ResetMemoryBank(_StandardCommand):
    """Reset Memory Bank according to DTR0

    If DTR0 = 0 then all implemented and unlocked memory banks except
    memory bank 0 shall be reset.

    In all other cases, the memory bank identified by DTR0 will be
    reset provided it is implemented and unlocked.

    This command may cause control gear to react improperly to
    commands for up to 10s.
    """
    _cmdval = 0x24
    uses_dtr0 = True
    sendtwice = True


class IdentifyDevice(_StandardCommand):
    """Identify Device

    Start or restart a 10s timer.  While the timer is running the
    device will run a procedure to enable an observer to distinguish
    the device from other devices in which it is not running.  This
    procedure is manufacturer-dependent.

    Identification will be stopped immediately upon reception of any
    command other than Initialise, RecallMinLevel, RecallMaxLevel or
    IdentifyDevice.
    """
    _cmdval = 0x25
    sendtwice = True


class SetMaxLevel(_StandardCommand):
    """Save the value in DTR0 as the new "MAX LEVEL"."""
    _cmdval = 0x2a
    uses_dtr0 = True
    sendtwice = True


class SetMinLevel(_StandardCommand):
    """Save the value in DTR0 as the new "MIN LEVEL".  If this value is
    lower than the "PHYSICAL MIN LEVEL" of the ballast, then store the
    "PHYSICAL MIN LEVEL" as the new "MIN LEVEL".
    """
    _cmdval = 0x2b
    uses_dtr0 = True
    sendtwice = True


class SetSystemFailureLevel(_StandardCommand):
    """Save the value in DTR0 as the new "SYSTEM FAILURE LEVEL"."""
    _cmdval = 0x2c
    uses_dtr0 = True
    sendtwice = True


class SetPowerOnLevel(_StandardCommand):
    """Save the value in DTR0 as the new "POWER ON LEVEL"."""
    _cmdval = 0x2d
    uses_dtr0 = True
    sendtwice = True


class SetFadeTime(_StandardCommand):
    """Set the "FADE TIME" in seconds according to the following formula:

    T=0.5(sqrt(pow(2,DTR))) seconds

    with DTR0 in the range 1..15

    If DTR0 is 0 then the extended fade time will be used.

    The fade time specifies the time for changing the arc power level
    from the actual level to the requested level.  In the case of lamp
    off, the preheat and ignition time is not included in the fade
    time.

    The new fade time will be used after the reception of the next arc
    power command.  If a new fade time is set during a running fade
    process, the running fade process is not affected.
    """
    _cmdval = 0x2e
    uses_dtr0 = True
    sendtwice = True


class SetFadeRate(_StandardCommand):
    """Set the "FADE RATE" in steps per second according to the following
    formula:

    F = 506/(sqrt(pow(2,DTR))) steps/s

    with DTR in the range 1..15

    The new fade time will be used after the reception of the next arc
    power command.  If a new fade time is set during a running fade
    process, the running fade process is not affected.
    """
    _cmdval = 0x2f
    uses_dtr0 = True
    sendtwice = True


class SetExtendedFadeTime(_StandardCommand):
    """Set Extended Fade Time

    If DTR0 > 0x4f then extendedFadeTimeBase and
    extendedFadeTimeMultiplier are both set to 0.

    Otherwise, extendedFadeTimeBase will be set to DTR0[3:0] and
    extendedFadeTimeMultiplier will be set to DTR0[6:4].

    If a new fade time is set during a running fade process, the
    running fade process is not affected.
    """
    _cmdval = 0x30
    uses_dtr0 = True
    sendtwice = True


class SetScene(_StandardCommand):
    """Save the value in the DTR as the new level of the specified scene.
    The value 255 ("MASK") removes the ballast from the scene.
    """
    _cmdval = 0x40
    _hasparam = True
    uses_dtr0 = True
    sendtwice = True


class RemoveFromScene(_StandardCommand):
    """Remove the ballast from the specified scene.

    This stores 255 ("MASK") in the specified scene register.
    """
    _cmdval = 0x50
    _hasparam = True
    sendtwice = True


class AddToGroup(_StandardCommand):
    """Add the ballast to the specified group."""
    _cmdval = 0x60
    _hasparam = True
    sendtwice = True


class RemoveFromGroup(_StandardCommand):
    """Remove the ballast from the specified group."""
    _cmdval = 0x70
    _hasparam = True
    sendtwice = True


class SetShortAddress(_StandardCommand):
    """Save the value in DTR0 as the new short address.

    The DTR must contain either:
    - (address<<1)|1 (i.e. 0AAAAAA1) to set a short address
    - 255 (i.e. 11111111) to remove the short address
    """
    _cmdval = 0x80
    uses_dtr0 = True
    sendtwice = True


class EnableWriteMemory(_StandardCommand):
    """Enable Write Memory

    writeEnableState shall be set to ENABLED.

    NB there is no command to explicitly disable memory write access;
    any command that is not directly involved with writing to memory
    banks will set writeEnableState to DISABLED.
    """
    _cmdval = 0x81
    sendtwice = True


class QueryStatusResponse(command.BitmapResponse):
    bits = ["ballast status", "lamp failure", "arc power on", "limit error",
            "fade ready", "reset state", "missing short address",
            "power failure"]

    @property
    def error(self):
        """Is the ballast in any kind of error state?
        (Ballast not ok, lamp fail, missing short address)
        """
        return self.ballast_status or self.lamp_failure \
            or self.missing_short_address


class QueryStatus(_StandardCommand):
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
    response = QueryStatusResponse


class QueryControlGearPresent(_StandardCommand):
    """Ask if there is a ballast that is able to communicate."""
    _cmdval = 0x91
    response = command.YesNoResponse


class QueryLampFailure(_StandardCommand):
    """Ask if there is a lamp problem."""
    _cmdval = 0x92
    response = command.YesNoResponse


class QueryLampPowerOn(_StandardCommand):
    """Ask if there is a lamp operating."""
    _cmdval = 0x93
    response = command.YesNoResponse


class QueryLimitError(_StandardCommand):
    """Ask if the last requested arc power level could not be met because
    it was above the MAX LEVEL or below the MIN LEVEL.  (Power level
    of 0 is always "OFF" and is not an error.)
    """
    _cmdval = 0x94
    response = command.YesNoResponse


class QueryResetState(_StandardCommand):
    """Ask if the ballast is in "RESET STATE"."""
    _cmdval = 0x95
    response = command.YesNoResponse


class QueryMissingShortAddress(_StandardCommand):
    """Ask if the ballast has no short address.  The response "YES" means
    that the ballast has no short address.
    """
    _cmdval = 0x96
    response = command.YesNoResponse


class QueryVersionNumber(_StandardCommand):
    """Ask for the version number of the IEC standard document met by the
    software and hardware of the ballast.  The high four bits of the
    answer represent the version number of the standard.  IEC-60929 is
    version number 0.

    The answer shall be the content of memory bank 0 location 0x16.
    """
    _cmdval = 0x97
    response = command.NumericResponse


class QueryContentDTR0(_StandardCommand):
    """Return the contents of DTR0."""
    _cmdval = 0x98
    uses_dtr0 = True
    response = command.NumericResponse


class QueryDeviceTypeResponse(command.Response):
    _types = {0: "fluorescent lamp",
              1: "emergency lighting",
              2: "HID lamp",
              3: "low voltage halogen lamp",
              4: "incandescent lamp dimmer",
              5: "dc-controlled dimmer",
              6: "LED lamp",
              254: "none / end",
              255: "multiple"}

    def __str__(self):
        if self.value and self.value.as_integer in self._types:
            return self._types[self.value.as_integer]

        return "{}".format(self.value)


class QueryDeviceType(_StandardCommand):
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

    XXX this is updated for IEC 62386-102 and interacts with
    QueryNextDeviceType.  In this case:

    If the device does not implement any part 2xx device type then
    the response will be 254;

    If the device implements one part 2xx device type then the
    response will be the device type number;

    If the device implements multiple part 2xx device types then the
    response will be MASK (0xff).
    """
    _cmdval = 0x99
    response = QueryDeviceTypeResponse


class QueryPhysicalMinimum(_StandardCommand):
    """Return the physical minimum level for this device."""
    _cmdval = 0x9a
    response = command.NumericResponseMask


class QueryPowerFailure(_StandardCommand):
    """Ask whether the device has not received a "RESET" or arc power
    control command since the last power-on.
    """
    _cmdval = 0x9b
    response = command.YesNoResponse


class QueryContentDTR1(_StandardCommand):
    """Return the contents of DTR1."""
    _cmdval = 0x9c
    uses_dtr1 = True
    response = command.NumericResponse


class QueryContentDTR2(_StandardCommand):
    """Return the contents of DTR2."""
    _cmdval = 0x9d
    uses_dtr2 = True
    response = command.NumericResponse


class QueryOperatingMode(_StandardCommand):
    """Query Operating Mode"""
    _cmdval = 0x9e
    response = command.NumericResponse


class QueryLightSourceType(_StandardCommand):
    """Query Light Source Type

    The answer shall be as follows:

    0 - low pressure fluorescent
    2 - HID
    3 - low voltage halogen
    4 - incandescent
    6 - LED
    7 - OLED
    252 - "other"
    253 - "unknown"
    254 - "none"
    MASK - multiple
    1,5,8..251 - reserved

    "unknown" will typically be used in case of signal conversion, for
    example to 1-10v dimming

    "none" will be used where no light source is connected, for
    example a relay

    When the response is "multiple" then the light source types shall
    be placed into DTR0, DTR1 and DTR2.  If there are exactly two
    light source types, DTR2 shall be "none".  If there are more than
    three then DTR2 shall be MASK.
    """
    _cmdval = 0x9f
    uses_dtr0 = True
    uses_dtr1 = True
    uses_dtr2 = True
    response = command.NumericResponseMask


class QueryActualLevel(_StandardCommand):
    """Return the current actual power level.  During preheating and if a
    lamp error occurs the answer will be 0xff ("MASK").
    """
    _cmdval = 0xa0
    response = command.NumericResponseMask


class QueryMaxLevel(_StandardCommand):
    """Return "MAX LEVEL"."""
    _cmdval = 0xa1
    response = command.NumericResponseMask


class QueryMinLevel(_StandardCommand):
    """Return "MIN LEVEL"."""
    _cmdval = 0xa2
    response = command.NumericResponseMask


class QueryPowerOnLevel(_StandardCommand):
    """Return "POWER ON LEVEL"."""
    _cmdval = 0xa3
    response = command.NumericResponseMask


class QuerySystemFailureLevel(_StandardCommand):
    """Return "SYSTEM FAILURE LEVEL"."""
    _cmdval = 0xa4
    response = command.NumericResponseMask


class QueryFadeTimeAndRateResponse(command.NumericResponse):
    @property
    def fade_time(self):
        if self._value:
            return self._value[7:4]

    @property
    def fade_rate(self):
        if self._value:
            return self._value[3:0]

    def __str__(self):
        return "Fade time: {0}; Fade rate: {1}".format(
            self.fade_time,
            self.fade_rate
        )


class QueryFadeTimeFadeRate(_StandardCommand):
    """Return the configured fade time and rate.

    The fade time set by "StoreDtrAsFadeTime" is in the upper four
    bits of the response.  The rade rate set by "StoreDtrAsFadeRate"
    is in the lower four bits of the response.
    """
    _cmdval = 0xa5
    response = QueryFadeTimeAndRateResponse


class QueryManufacturerSpecificMode(_StandardCommand):
    """Query Manufacturer Specific Mode

    The answer shall be YES when operatingMode is in the range
    0x80..0xff and NO otherwise.
    """
    _cmdval = 0xa6
    response = command.YesNoResponse


class QueryNextDeviceType(_StandardCommand):
    """Query Next Device Type

    If directly preceded by QueryDeviceType and more than one device
    type is supported, returns the first and lowest device type
    number.

    If directly preceded by QueryNextDeviceType and not all device
    types have been reported, returns the next lowest device type
    number.

    If directly preceded by QueryNextDeviceType and all device types
    have been reported, returns 254.

    In all other cases returns NO (no response).

    Multi-master transmitters shall send the sequence
    QueryDeviceType,QueryNextDeviceType,... as a transaction.
    """
    _cmdval = 0xa7
    response = QueryDeviceTypeResponse


class QueryExtendedFadeTime(_StandardCommand):
    """Query Extended Fade Time

    Bits 6:4 of the answer are extendedFadeTimeMultiplier, and bits
    3:0 are extendedFadeTimeBase.
    """
    _cmdval = 0xa8
    response = command.Response


class QueryControlGearFailure(_StandardCommand):
    """Query Control Gear Failure

    The answer shall be YES if controlGearFailure is TRUE and NO
    otherwise.
    """
    _cmdval = 0xaa
    response = command.YesNoResponse


class QuerySceneLevel(_StandardCommand):
    """Return the level set for the specified scene, or 255 ("MASK") if
    the device is not part of the scene.
    """
    _cmdval = 0xb0
    _hasparam = True
    response = command.NumericResponseMask


class QueryGroupsZeroToSeven(_StandardCommand):
    """Return the device membership of groups 0-7 with group 0 in the
    least-significant bit of the response.
    """
    _cmdval = 0xc0
    response = command.Response


class QueryGroupsEightToFifteen(_StandardCommand):
    """Return the device membership of groups 8-15 with group 8 in the
    least-significant bit of the response.
    """
    _cmdval = 0xc1
    response = command.Response


class QueryRandomAddressH(_StandardCommand):
    """Return the 8 high bits of the random address."""
    _cmdval = 0xc2
    response = command.Response


class QueryRandomAddressM(_StandardCommand):
    """Return the 8 mid bits of the random address."""
    _cmdval = 0xc3
    response = command.Response


class QueryRandomAddressL(_StandardCommand):
    """Return the 8 low bits of the random address."""
    _cmdval = 0xc4
    response = command.Response


class ReadMemoryLocation(_StandardCommand):
    """Read Memory Location

    The query is ignored if the addressed memory bank is not
    implemented.

    If executed, the answer will be the content of the memory location
    identified by DTR0 in bank DTR1.  If the addressed location is
    below 0xff, then DTR0 is incremented by 1.
    """
    _cmdval = 0xc5
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.Response


class QueryExtendedVersionNumberMixin:
    """Query Extended Version Number

    This command must be preceded by an appropriate EnableDeviceType
    command; if it is not then it will be ignored.  Returns the
    version number of Part 2xx of IEC 62386 for the corresponding
    device type as an 8-bit number.

    Device type implementations must provide their own implementation
    of QueryExtendedVersionNumber using this mixin.
    """
    _cmdval = 0xff
    response = command.NumericResponse

class QueryExtendedVersionNumber(QueryExtendedVersionNumberMixin,
                                 _StandardCommand):
    """Query Extended Version Number

    For device type 0, this command is ignored.
    """
    pass

###############################################################################
# Commands from Table 16 start here
###############################################################################

class _SpecialCommand(_GearCommand):
    """A special command as defined in Table 16 of IEC 62386-102.

    Special commands are broadcast and are received by all devices.
    """
    _hasparam = False
    _cmdval = None

    def __init__(self, *args):
        if self._hasparam:
            if len(args) != 1:
                raise TypeError(
                    "{}.__init__() takes exactly 2 arguments ({} given)".format(
                        self.__class__.__name__, len(args) + 1))
            param = args[0]
            if not isinstance(param, int):
                raise ValueError("param must be an int")
            if param < 0 or param > 255:
                raise ValueError("param must be in range 0..255")
        else:
            if len(args) != 0:
                raise TypeError(
                    "{}.__init__() takes exactly 1 arguments ({} given)".format(
                        self.__class__.__name__, len(args) + 1))
            param = 0
        self.param = param
        super().__init__(frame.ForwardFrame(16, (self._cmdval, self.param)))

    # dict of frame[15:8] to cls
    _opcodes = {}

    @classmethod
    def _register_subclass(cls, subclass):
        if subclass.__name__[0] == '_':
            return
        cls._opcodes[subclass._cmdval] = subclass

    @classmethod
    def from_frame(cls, frame, devicetype=0):
        opcode = frame[15:8]
        if opcode == cls._cmdval:
            if cls._hasparam:
                return cls(frame[7:0])
            elif frame[7:0] == 0:
                return cls()
            else:
                return UnknownGearCommand(frame)

        cc = cls._opcodes.get(opcode)
        if not cc:
            return UnknownGearCommand(frame)
        return cc.from_frame(frame, devicetype=devicetype)

    def __str__(self):
        if self._hasparam:
            return "{}({})".format(self.__class__.__name__, self.param)
        return "{}()".format(self.__class__.__name__)


class _ShortAddrSpecialCommand(_SpecialCommand):
    """A special command that has a short address as its parameter."""
    _hasparam = True

    def __init__(self, address):
        if address == "MASK":
            self.address = address
        else:
            if not isinstance(address, int):
                raise ValueError("address must be an integer or 'MASK'")
            if address < 0 or address > 63:
                raise ValueError("address must be in the range 0..63")
        self.address = address
        data = 0xff if self.address == "MASK" else ((self.address << 1) | 1)
        super().__init__(data)

    @classmethod
    def from_frame(cls, frame, devicetype=0):
        if cls == _ShortAddrSpecialCommand:
            return
        if frame[15:8] == cls._cmdval:
            if frame[7:0] == 0xff:
                return cls("MASK")
            if frame[7] is False and frame[0] is True:
                return cls(frame[6:1])

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.address)


class Terminate(_SpecialCommand):
    """All special mode processes shall be terminated."""
    _cmdval = 0xa1


class DTR0(_SpecialCommand):
    """This is a broadcast command to set the value of the DTR0 register."""
    _cmdval = 0xa3
    _hasparam = True
    uses_dtr0 = True


class Initialise(_SpecialCommand):
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
    _cmdval = 0xa5
    _hasparam = True
    sendtwice = True

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
        if self.broadcast:
            b = 0
        elif self.address is None:
            b = 0xff
        else:
            b = (self.address << 1) | 1
        super().__init__(b)

    @classmethod
    def from_frame(cls, f, devicetype=0):
        if f[15:8] == cls._cmdval:
            if f[7:0] == 0:
                return cls(broadcast=True)
            if f[7:0] == 0xff:
                return cls(address=None)
            if f[7] is False and f[0] is True:
                return cls(address=f[6:1])

    def __str__(self):
        if self.broadcast:
            return "Initialise(broadcast=True)"
        return "Initialise(address={})".format(self.address)


class Randomise(_SpecialCommand):
    """The ballast shall generate a new 24-bit random address.  The new
    random address shall be available within a time period of 100ms.
    """
    _cmdval = 0xa7
    sendtwice = True


class Compare(_SpecialCommand):
    """The ballast shall compare its 24-bit random address with the
    combined search address stored in SearchAddrH, SearchAddrM and
    SearchAddrL.  If its random address is smaller or equal to the
    search address and the ballast is not withdrawn then the ballast
    shall generate a query "YES".
    """
    _cmdval = 0xa9
    response = command.YesNoResponse


class Withdraw(_SpecialCommand):
    """The ballast that has a 24-bit random address equal to the combined
    search address stored in SearchAddrH, SearchAddrM and SearchAddrL
    snall no longer respond to the compare command.  This ballast
    shall not be excluded from the initialisation process.
    """
    _cmdval = 0xab


class Ping(_SpecialCommand):
    """Ping

    Transmitted at 10 minute intervals by single master application
    controllers (that cannot perform collision detection) to indicate
    their presence.  Ignored by control gear.
    """
    _cmdval = 0xad


class SearchaddrH(_SpecialCommand):
    """Set the high 8 bits of the search address."""
    _cmdval = 0xb1
    _hasparam = True

SetSearchAddrH = SearchaddrH


class SearchaddrM(_SpecialCommand):
    """Set the mid 8 bits of the search address."""
    _cmdval = 0xb3
    _hasparam = True

SetSearchAddrM = SearchaddrM


class SearchaddrL(_SpecialCommand):
    """Set the low 8 bits of the search address."""
    _cmdval = 0xb5
    _hasparam = True

SetSearchAddrL = SearchaddrL


class ProgramShortAddress(_ShortAddrSpecialCommand):
    """The ballast shall store the received 6-bit address as its short
    address if it is selected.  It is selected if:

    * the ballast's 24-bit random address is equal to the address in
      SearchAddrH, SearchAddrM and SearchAddrL

    * physical selection has been detected (the lamp is electrically
      disconnected after reception of command PhysicalSelection())

    If address is the string "MASK" then the short address shall be
    deleted.
    """
    _cmdval = 0xb7


class VerifyShortAddress(_ShortAddrSpecialCommand):
    """The ballast shall give an answer "YES" if the received short
    address is equal to its own short address.
    """
    _cmdval = 0xb9
    response = command.YesNoResponse


# XXX response class for QueryShortAddress here?

class QueryShortAddress(_SpecialCommand):
    """The ballast shall send the short address if the random address is
    the same as the search address or the ballast is physically
    selected.  The answer will be in the format (address<<1)|1 if the
    short address is programmed, or "MASK" (0xff) if there is no short
    address stored.
    """
    _cmdval = 0xbb
    response = command.NumericResponseMask


class EnableDeviceType(_SpecialCommand):
    """This command shall be sent before an application extended command.
    This command can be processed without the use of the Initialise()
    command.  This command shall not be used for device type 0.
    """
    _cmdval = 0xc1
    _hasparam = True


class DTR1(_SpecialCommand):
    """This is a broadcast command to set the value of the DTR1 register."""
    _cmdval = 0xc3
    _hasparam = True
    uses_dtr1 = True


class DTR2(_SpecialCommand):
    """This is a broadcast command to set the value of the DTR2 register."""
    _cmdval = 0xc5
    _hasparam = True
    uses_dtr2 = True


class WriteMemoryLocation(_SpecialCommand):
    """Write Memory Location

    This instruction will be ignored if the addressed memory bank is
    not implemented, or writeEnableState is DISABLED.

    If the instruction is executed then the control gear will write
    data into the memory location identified by DTR0 in bank DTR1 and
    return data as an answer.

    If the location is not implemented, above the last accessible
    location, locked or not writeable, the answer will be NO.

    If the location addressed is below 0xff, then DTR0 will be
    incremented by 1.
    """
    _cmdval = 0xc7
    _hasparam = True
    uses_dtr0 = True
    uses_dtr1 = True
    response = command.Response


class WriteMemoryLocationNoReply(_SpecialCommand):
    """Write Memory Location No Reply

    Identical to WriteMemoryLocation except no response will ever be
    generated.
    """
    _cmdval = 0xc9
    _hasparam = True
    uses_dtr0 = True
    uses_dtr1 = True
