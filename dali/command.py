from . import address

class CommandTracker(type):
    """
    Metaclass keeping track of all the types of Command we understand.

    """
    def __init__(cls,name,bases,attrs):
        if not hasattr(cls,'_commands'):
            cls._commands=[]
        else:
            cls._commands.append(cls)

class Response(object):
    """
    Some DALI commands cause a response from the addressed devices.
    The response is either an 8-bit frame encoding 8-bit data or 0xff
    for "Yes", or a lack of response encoding "No".

    """
    def __init__(self,val):
        """
        If there was no response, call with val=None.

        """
        self._value=val
    @property
    def value(self):
        return self._value
    def __unicode__(self):
        return unicode(self.value)

class YesNoResponse(Response):
    @property
    def value(self):
        return self._value!=None

class Command(object):
    """
    A standard DALI command defined in IEC-60929 annex E.

    Subclasses must provide a class method "from_bytes" which, when
    passed a (a,b) command tuple returns a new instance of the class
    corresponding to that command, or "None" if there is no match.

    """
    __metaclass__=CommandTracker
    _isconfig=False
    _isquery=False
    _response=None
    def __init__(self,a,b):
        self.a=a
        self.b=b
    @classmethod
    def from_bytes(cls,command):
        """
        Return a Command instance corresponding to the bytes in
        command.  Returns None if there is no match.

        """
        if cls!=Command: return None
        for dc in cls._commands:
            r=dc.from_bytes(command)
            if r: return r
        # At this point we can simply wrap the bytes we received.  We
        # don't know what kind of command this is (config, query,
        # etc.) so we're unlikely ever to want to transmit it!
        return cls(*command)
    @property
    def command(self):
        """
        The two bytes to be transmitted over the wire for this
        command, as a two-tuple of integers.

        """
        return (self.a,self.b)
    @property
    def is_config(self):
        """
        Is this a configuration command?  (Does it need repeating to
        take effect?)

        """
        return self._isconfig
    @property
    def is_query(self):
        """
        Does this command return a result?

        """
        return self._isquery
    @property
    def response(self):
        """
        If this command returns a result, use this class for the response.

        """
        return self._response
    def __unicode__(self):
        return u"Command(0x%02x,0x%02x)"%(self.a,self.b)

class ArcPower(Command):
    """
    A command to set the arc power level directly.
    
    destination is a dali.address.Address object
    power is either an integer in the range 0..255, or one of two
    special strings:
    
    "OFF" sets the ballast off (same as power level 0)
    "MASK" stops any fade in progress (same as power level 255)
    
    The lamp will fade to the specified power according to its
    programmed fade time.  The MAX LEVEL and MIN LEVEL settings will
    be respected.
    """
    def __init__(self,destination,power):
        if power=="OFF": power=0
        if power=="MASK": power=255
        if not isinstance(power,int):
            raise ValueError("power must be an integer or string")
        if power<0 or power>255:
            raise ValueError("power must be in the range 0..255")
        self.destination=destination
        self.power=power
        Command.__init__(self,destination.addrbyte,power)
    @classmethod
    def from_bytes(cls,command):
        a,b=command
        if a&0x01: return
        addr=address.from_byte(a)
        if addr is None: return
        return cls(addr,b)
    def __unicode__(self):
        if self.power==0: power="OFF"
        elif self.power==255: power="MASK"
        else: power=self.power
        return u"ArcPower(%s,%s)"%(self.destination,power)

class GeneralCommand(Command):
    """
    A command addressed to broadcast, short address or group, i.e. one
    with a destination as defined in E.4.3.2 and which is not a direct
    arc power command.

    """
    _cmdval=None
    _hasparam=False
    def __init__(self,destination,*args):
        if self._cmdval is None: raise NotImplementedError
        if self._hasparam:
            if len(args)!=1:
                raise TypeError(
                    "%s.__init__() takes exactly 3 arguments (%d given)"%(
                        self.__class__.__name__,len(args)+2))
            param=args[0]
            if not isinstance(param,int):
                raise ValueError("param must be an integer")
            if param<0 or param>15:
                raise ValueError("param must be in the range 0..15")
            self.param=param
        else:
            if len(args)!=0:
                raise TypeError(
                    "%s.__init__() takes exactly 2 arguments (%d given)"%(
                        self.__class__.__name__,len(args)+2))
            param=0
        Command.__init__(self,destination.addrbyte|0x01,self._cmdval|param)
        self.destination=destination
    @classmethod
    def from_bytes(cls,command):
        if cls==GeneralCommand: return
        a,b=command
        if a&0x01 == 0: return
        if cls._hasparam:
            if b&0xf0!=cls._cmdval: return
        else:
            if b!=cls._cmdval: return
        addr=address.from_byte(a)
        if addr is None: return
        if cls._hasparam:
            return cls(addr,b&0x0f)
        return cls(addr)
    def __unicode__(self):
        if self._hasparam:
            return u"%s(%s,%s)"%(self.__class__.__name__,self.destination,
                                 self.param)
        return u"%s(%s)"%(self.__class__.__name__,self.destination)

class Off(GeneralCommand):
    """
    Extinguish the lamp immediately without fading.

    """
    _cmdval=0x00

class Up(GeneralCommand):
    """
    Dim UP for 200ms at the selected FATE RATE.

    No change if the arc power output is already at the "MAX LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    This command shall only affect ballasts with burning lamps.
    No lamp shall be ignited with this command.

    """
    _cmdval=0x01

class Down(GeneralCommand):
    """
    Dim DOWN for 200ms at the selected FADE RATE.

    No change if the arc power output is already at the "MIN LEVEL".

    If this command is received again while it is being executed, the
    execution time shall be re-triggered.

    Lamp shall not be switched off via this command.

    """
    _cmdval=0x02

class StepUp(GeneralCommand):
    """
    Set the actual arc power level one step higher immediately without
    fading.

    No change if the arc power output is already at the "MAX LEVEL".

    This command shall only affect ballasts with burning lamps.  No
    lamp shall be ignited with this command.

    """
    _cmdval=0x03

class StepDown(GeneralCommand):
    """
    Set the actual arc power level one step lower immediately without
    fading.

    Lamps shall not be switched off via this command.

    No change if the arc power output is already at the "MIN LEVEL".

    """
    _cmdval=0x04

class RecallMaxLevel(GeneralCommand):
    """
    Set the actual arc power level to the "MAX LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.

    """
    _cmdval=0x05

class RecallMinLevel(GeneralCommand):
    """
    Set the actual arc power level to the "MIN LEVEL" without fading.
    If the lamp is off it shall be ignited with this command.

    """
    _cmdval=0x06

class StepDownAndOff(GeneralCommand):
    """
    Set the actual arc power level one step lower immediately without
    fading.

    If the actual arc power level is already at the "MIN LEVEL", the
    lamp shall be switched off by this command.

    """
    _cmdval=0x07

class OnAndStepUp(GeneralCommand):
    """
    Set the actual arc power level one step higher immediately without
    fading.

    If the lamp is switched off, the lamp shall be ignited with this
    command and shall be set to the "MIN LEVEL".

    """
    _cmdval=0x08

class GoToScene(GeneralCommand):
    """
    Set the actual arc power level to the value stored for the scene
    using the actual fade time.

    If the ballast does not belong to this scene, the arc power level
    remains unchanged.

    If the lamp is off, it shall be ignited with this command.

    If the value stored for this scene is zero and the lamp is lit
    then the lamp shall be switched off by this command after the fade
    time.

    """
    _cmdval=0x10
    _hasparam=True

class ConfigCommand(GeneralCommand):
    """
    Configuration commands must be transmitted twice within 100ms,
    with no other commands addressing the same ballast being
    transmitted in between.

    """
    _isconfig=True

class Reset(ConfigCommand):
    """
    The variables in the persistent memory shall be changed to their
    reset values.  It is not guaranteed that any commands will be
    received properly within the next 300ms by a ballast acting on
    this command.

    """
    _cmdval=0x20

class StoreActualLevelInDtr(ConfigCommand):
    """
    Store actual arc power level in the DTR without changing the
    current light intensity.

    """
    _cmdval=0x21

class StoreDtrAsMaxLevel(ConfigCommand):
    """
    Save the value in the DTR as the new "MAX LEVEL".

    """
    _cmdval=0x2a

class StoreDtrAsMinLevel(ConfigCommand):
    """
    Save the value in the DTR as the new "MIN LEVEL".  If this value
    is lower than the "PHYSICAL MIN LEVEL" of the ballast, then store
    the "PHYSICAL MIN LEVEL" as the new "MIN LEVEL".
    
    """
    _cmdval=0x2b

class StoreDtrAsFailLevel(ConfigCommand):
    """
    Save the value in the DTR as the new "SYSTEM FAILURE LEVEL".

    """
    _cmdval=0x2c

class StoreDtrAsPowerOnLevel(ConfigCommand):
    """
    Save the value in the DTR as the new "POWER ON LEVEL".

    """
    _cmdval=0x2d

class StoreDtrAsFadeTime(ConfigCommand):
    """
    Set the "FADE TIME" in seconds according to the following formula:

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
    _cmdval=0x2e

class StoreDtrAsFadeRate(ConfigCommand):
    """
    Set the "FADE RATE" in steps per second according to the following
    formula:

    F = 506/(sqrt(pow(2,DTR))) steps/s

    with DTR in the range 1..15

    The new fade time will be used after the reception of the next arc
    power command.  If a new fade time is set during a running fade
    process, the running fade process is not affected.

    """
    _cmdval=0x2f

class StoreDtrAsScene(ConfigCommand):
    """
    Save the value in the DTR as the new level of the specified scene.
    The value 255 ("MASK") removes the ballast from the scene.

    """
    _cmdval=0x40
    _hasparam=True

class RemoveFromScene(ConfigCommand):
    """
    Remove the ballast from the specified scene.

    This stores 255 ("MASK") in the specified scene register.

    """
    _cmdval=0x50
    _hasparam=True

class AddToGroup(ConfigCommand):
    """
    Add the ballast to the specified group.

    """
    _cmdval=0x60
    _hasparam=True

class RemoveFromGroup(ConfigCommand):
    """
    Remove the ballast from the specified group.

    """
    _cmdval=0x70
    _hasparam=True

class StoreDtrAsShortAddress(ConfigCommand):
    """
    Save the value in the DTR as the new short address.

    The DTR must contain either:
    - (address<<1)|1 (i.e. 0AAAAAA1) to set a short address
    - 255 (i.e. 11111111) to remove the short address

    """
    _cmdval=0x80

class QueryCommand(GeneralCommand):
    """
    Query commands are answered with "Yes", "No" or 8-bit information.

    "Yes" is encoded as 0xff (255)
    "No" is encoded as no response

    Query commands addressed to more than one ballast may receive
    invalid answers as all ballasts addressed will answer.  It may be
    useful to do this to check whether any ballast in a group provides
    a "Yes" response, for example to "QueryLampFailure".

    """
    _isquery=True
    _response=Response

class QueryStatusResponse(Response):
    bits=["status","lamp failure","arc power on","limit error",
          "fade ready","reset state","missing short address","power failure"]
    @property
    def status(self):
        v=self._value
        l=[]
        for b in self.bits:
            if v&0x01: l.append(b)
            v=(v>>1)
        return l
    @property
    def ballast_status(self):
        return self._value&0x01!=0
    @property
    def lamp_failure(self):
        return self._value&0x02!=0
    @property
    def lamp_arc_power_on(self):
        return self._value&0x04!=0
    @property
    def limit_error(self):
        return self._value&0x08!=0
    @property
    def fade_ready(self):
        return self._value&0x10!=0
    @property
    def reset_state(self):
        return self._value&0x20!=0
    @property
    def missing_short_address(self):
        return self._value&0x40!=0
    @property
    def power_failure(self):
        return self._value&0x80!=0
    @property
    def error(self):
        """
        Is the ballast in any kind of error state?
        (Ballast not ok, lamp fail, missing short address)

        """
        return self._value&0x43!=0
    def __unicode__(self):
        return u",".join(self.status)

class QueryStatus(QueryCommand):
    """
    Retrieve a status byte from the ballast:

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
    _cmdval=0x90
    _response=QueryStatusResponse

class QueryBallast(QueryCommand):
    """
    Ask if there is a ballast that is able to communicate.

    """
    _cmdval=0x91
    _response=YesNoResponse

class QueryLampFailure(QueryCommand):
    """
    Ask if there is a lamp problem.

    """
    _cmdval=0x92
    _response=YesNoResponse

class QueryLampPowerOn(QueryCommand):
    """
    Ask if there is a lamp operating.

    """
    _cmdval=0x93
    _response=YesNoResponse

class QueryLimitError(QueryCommand):
    """
    Ask if the last requested arc power level could not be met because
    it was above the MAX LEVEL or below the MIN LEVEL.  (Power level
    of 0 is always "OFF" and is not an error.)

    """
    _cmdval=0x94
    _response=YesNoResponse

class QueryResetState(QueryCommand):
    """
    Ask if the ballast is in "RESET STATE".

    """
    _cmdval=0x95
    _response=YesNoResponse

class QueryMissingShortAddress(QueryCommand):
    """
    Ask if the ballast has no short address.  The response "YES" means
    that the ballast has no short address.

    """
    _cmdval=0x96
    _response=YesNoResponse

class QueryVersionNumber(QueryCommand):
    """
    Ask for the version number of the IEC standard document met by the
    software and hardware of the ballast.  The high four bits of the
    answer represent the version number of the standard.  IEC-60929 is
    version number 0.

    """
    _cmdval=0x97

class QueryDtr(QueryCommand):
    """
    Return the contents of the DTR.

    """
    _cmdval=0x98

QueryContentDtr=QueryDtr

class QueryDeviceTypeResponse(Response):
    _types={0: u"fluorescent lamp",
            1: u"emergency lighting",
            2: u"HID lamp",
            3: u"low voltage halogen lamp",
            4: u"incandescent lamp dimmer",
            5: u"dc-controlled dimmer",
            6: u"LED lamp"}
    def __unicode__(self):
        if self.value in self._types: return self._types[self.value]
        return unicode(self.value)

class QueryDeviceType(QueryCommand):
    """
    Return the device type.  Currently defined:

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
    _cmdval=0x99
    _response=QueryDeviceTypeResponse

class QueryPhysicalMinimumLevel(QueryCommand):
    """
    Return the physical minimum level for this device.

    """
    _cmdval=0x9a

class QueryPowerFailure(QueryCommand):
    """
    Ask whether the device has not received a "RESET" or arc power
    control command since the last power-on.

    """
    _cmdval=0x9b
    _response=YesNoResponse

class QueryActualLevel(QueryCommand):
    """
    Return the current actual power level.  During preheating and if a
    lamp error occurs the answer will be 0xff ("MASK").

    """
    _cmdval=0xa0

class QueryMaxLevel(QueryCommand):
    """
    Return "MAX LEVEL".

    """
    _cmdval=0xa1

class QueryMinLevel(QueryCommand):
    """
    Return "MIN LEVEL".

    """
    _cmdval=0xa2

class QueryPowerOnLevel(QueryCommand):
    """
    Return "POWER ON LEVEL".

    """
    _cmdval=0xa3

class QueryFailureLevel(QueryCommand):
    """
    Return "SYSTEM FAILURE LEVEL".

    """
    _cmdval=0xa4

class QueryFadeTimeAndRateResponse(Response):
    @property
    def fade_time(self):
        return self._value>>4
    @property
    def fade_rate(self):
        return self._value&0x0f
    def __unicode__(self):
        return u"Fade time: %s; Fade rate: %s"%(self.fade_time,self.fade_rate)

class QueryFadeTimeAndRate(QueryCommand):
    """
    Return the configured fade time and rate.

    The fade time set by "StoreDtrAsFadeTime" is in the upper four
    bits of the response.  The rade rate set by "StoreDtrAsFadeRate"
    is in the lower four bits of the response.

    """
    _cmdval=0xa5
    _response=QueryFadeTimeAndRateResponse

class QuerySceneLevel(QueryCommand):
    """
    Return the level set for the specified scene, or 255 ("MASK") if
    the device is not part of the scene.

    """
    _cmdval=0xb0
    _hasparam=True

class QueryGroupsLSB(QueryCommand):
    """
    Return the device membership of groups 0-7 with group 0 in the
    least-significant bit of the response.

    """
    _cmdval=0xc0

class QueryGroupsMSB(QueryCommand):
    """
    Return the device membership of groups 8-15 with group 8 in the
    least-significant bit of the response.

    """
    _cmdval=0xc1

class QueryRandomAddressH(QueryCommand):
    """
    Return the 8 high bits of the random address.

    """
    _cmdval=0xc2

class QueryRandomAddressM(QueryCommand):
    """
    Return the 8 mid bits of the random address.

    """
    _cmdval=0xc3

class QueryRandomAddressL(QueryCommand):
    """
    Return the 8 low bits of the random address.

    """
    _cmdval=0xc4

class SpecialCommand(Command):
    """
    Special commands are broadcast and are received by all devices.

    """
    pass

class SetDtr(SpecialCommand):
    """
    This is a broadcast command to set the value of the DTR register."

    """
    def __init__(self,value):
        if not isinstance(value,int):
            raise ValueError("value must be an int")
        if value<0 or value>255:
            raise ValueError("value must be in range 0..255")
        self.value=value
    @property
    def command(self):
        return (0xa3,self.value)

from_bytes=Command.from_bytes
