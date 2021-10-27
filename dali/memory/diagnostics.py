from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, \
    NumericValue, FixedScaleNumericValue, BinaryValue, TemperatureValue
from decimal import Decimal

# Memory bank definitions from DiiA Specification, DALI Part 253 -
# Diagnostics & Maintenance, Version 1.1, October 2019
BANK_205 = MemoryBank(205, 0x1C, has_lock=True, has_latch=True)
BANK_206 = MemoryBank(206, 0x20, has_lock=True, has_latch=True)
# NB Bank 207 is declared in the 'maintenance' module

# TMASK indicates the memory bank value may not be available
# temporarily. Depending on the size of the data, TMASK may take the
# value 0xfe, 0xfffe, 0xfffffe, 0xfffffffe, 0xfffffffffffe (unsigned
# types) or 0x7e, 0x7ffe, 0x7ffffffe (signed types)

# MASK indicates the memory bank value is read-protected. MASK may
# take the value 0xff, 0xffff, etc.


class ControlGearDiagnosticBankVersion(NumericValue):
    """Version of the gear diagnostics memory bank
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x03, default=0x01,
                               type_=MemoryType.ROM)


class ControlGearOperatingTime(NumericValue):
    """Control Gear Operating Time in s

    Counts the control gear operating time in seconds if the control
    gear is powered regardless of the status of lampOn bit.

    Valid in the range 0..0xfffffffd, TMASK
    """
    bank = BANK_205
    unit = 's'
    locations = MemoryRange(start=0x04, end=0x07, default=0x00,
                            type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffffd


class ControlGearStartCounter(NumericValue):
    """Control Gear Start Counter

    Counts the number of control gear starts that are induced by a
    power cycle of the external supply. A power cycle shall be counted
    if the power on time is at least 600ms.

    Valid in the range 0..0xfffffd, TMASK
    """
    bank = BANK_205
    locations = MemoryRange(start=0x08, end=0x0a, default=0x00,
                            type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffd


class ControlGearExternalSupplyVoltage(FixedScaleNumericValue):
    """Control Gear External Supply Voltage in Vrms

    RMS value of external supply voltage
    """
    bank = BANK_205
    unit = 'Vrms'
    scaling_factor = Decimal("0.1")
    locations = MemoryRange(start=0x0b, end=0x0c,
                            type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfffd


class ControlGearExternalSupplyVoltageFrequency(NumericValue):
    """Control Gear External Supply Voltage Frequency in Hz

    Frequency of external supply voltage.

    Indication as follows: 0 in case of 0 Hz (pure DC or rectified AC
    voltage).

    NOTE Examples for frequency indication:
    17 in case of 16,7 Hz
    50 in case of 50 Hz
    60 in case of 60 Hz
    """
    bank = BANK_205
    unit = 'Hz'
    locations = MemoryLocation(address=0x0d, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearPowerFactor(FixedScaleNumericValue):
    """Control Gear Power Factor
    """
    bank = BANK_205
    scaling_factor = Decimal("0.01")
    locations = MemoryLocation(address=0x0e, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 100


class ControlGearOverallFailureCondition(BinaryValue):
    """Control Gear Overall Failure Condition

    Failure condition flag indication as follows:

    ControlGearOverallFailureCondition reflects the status of
    ``controlGearFailure``.

    TMASK is supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x0f, type_=MemoryType.RAM_RO)
    tmask_supported = True


class ControlGearOverallFailureConditionCounter(NumericValue):
    """Control Gear Overall Failure Condition Counter

    Valid in the range 0..0xfd; TMASK is supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x10, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfd


class ControlGearExternalSupplyUndervoltage(BinaryValue):
    """Control Gear External Supply Undervoltage

    Failure condition flag indication as follows:

    ControlGearExternalSupplyUndervoltage = 1 if
    ControlGearExternalSupplyVoltage <
    ControlGearExternalSupplyUndervoltage threshold.

    Otherwise: ControlGearExternalSupplyUndervoltage = 0.

    ControlGearExternalSupplyUndervoltage threshold shall fulfil the
    following conditions:

    ControlGearExternalSupplyUndervoltage threshold shall be lower
    than the lower end of the specified input voltage range of the
    control gear and the value of the
    ControlGearExternalSupplyUndervoltage threshold is such that
    lifetime and/or performance of the control gear could be affected
    if the ControlGearExternalSupplyVoltage is lower than the
    threshold.

    NOTE Two different thresholds can be implemented for AC and for DC
    supply voltage.

    Example:
    Control gear datasheet:
    Nominal input voltage: 220 – 240 V
    Input voltage ac: 198 – 264 V
    Input voltage dc: 176 – 276 V

    TMASK and MASK are supported.
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x11, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class ControlGearExternalSupplyUndervoltageCounter(NumericValue):
    """Control Gear External Supply Undervoltage Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x12, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearExternalSupplyOvervoltage(BinaryValue):
    """Control Gear External Supply Overvoltage

    Failure condition flag indication as follows:

    ControlGearExternalSupplyOvervoltage = 1 if
    ControlGearExternalSupplyVoltage >
    ControlGearExternalSupplyOvervoltage threshold.

    Otherwise: ControlGearExternalSupplyOvervoltage = 0.

    ControlGearExternalSupplyOvervoltage threshold shall fulfil the
    following conditions:

    ControlGearExternalSupplyOvervoltage threshold shall be higher
    than the higher end of the specified input voltage range of the
    control gear and the value of the
    ControlGearExternalSupplyOvervoltage threshold is such that
    lifetime and/or performance of the control gear could be affected
    if the ControlGearExternalSupplyVoltage is higher than the
    threshold.

    NOTE Two different thresholds can be implemented for AC and for DC
    supply voltage.

    Example:
    Control gear datasheet:
    Nominal input voltage: 220 – 240 V
    Input voltage ac: 198 – 264 V
    Input voltage dc: 176 – 276 V

    TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x13, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class ControlGearExternalSupplyOvervoltageCounter(NumericValue):
    """Control Gear External Supply Overvoltage Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x14, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearOutputPowerLimitation(BinaryValue):
    """Control Gear Output Power Limitation

    Failure condition flag indication as follows:

    ControlGearOutputPowerLimitation = 1 if control gear output power
    > ControlGearOutputPowerLimitation threshold.

    Otherwise: ControlGearOutputPowerLimitation = 0.

    ControlGearOutputPowerLimitation threshold represents the output
    power limit of the control gear.

    NOTE ControlGearOutputPowerLimitation = 1 if the control gear
    limits the output current due to its internal power
    limitation. This is the case if the LED voltage multiplied with
    the control gear output current is higher than the output power
    limit of the control gear.

    TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x15, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class ControlGearOutputPowerLimitationCounter(NumericValue):
    """Control Gear Output Power Limitation Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x16, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearThermalDerating(BinaryValue):
    """Control Gear Thermal Derating

    Failure condition flag indication as follows:

    ControlGearThermalDerating = 1 if
    ControlGearTemperature > ControlGearThermalDerating threshold.

    Otherwise: ControlGearThermalDerating = 0.

    ControlGearThermalDerating threshold shall fulfil the following conditions:

    The value of the ControlGearThermalDerating threshold is such that
    lifetime and/or performance of the control gear could be affected if
    the ControlGearTemperature is higher than the threshold.  If
    ControlGearThermalDerating = 1 the output current of the control gear
    may be reduced.

    TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x17, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class ControlGearThermalDeratingCounter(NumericValue):
    """Control Gear Thermal Derating Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x18, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearThermalShutdown(BinaryValue):
    """Control Gear Thermal Shutdown

    Failure condition flag indication as follows:

    ControlGearThermalShutdown = 1 if ControlGearTemperature >
    ControlGearThermalShutdown threshold.

    Otherwise: ControlGearThermalShutdown = 0.

    ControlGearThermalShutdown threshold shall fulfil the following
    conditions:

    The value of the ControlGearThermalShutdown threshold is such that
    lifetime and/or performance of the control gear could be affected
    if the ControlGearTemperature is higher than the threshold.
    ControlGearThermalShutdown threshold shall be higher than
    ControlGearThermalDerating threshold.

    If ControlGearThermalShutdown = 1 the output current of the
    control gear shall be reduced to zero.

    TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x19, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class ControlGearThermalShutdownCounter(NumericValue):
    """Control Gear Thermal Shutdown Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x1a, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class ControlGearTemperature(TemperatureValue):
    """Control Gear Temperature in °C

    Indicates the internal temperature of the control gear.

    NOTE The temperature indicated by ControlGearTemperature is an
    internal temperature and may be different from the Tc temperature.

    TMASK is supported
    """
    bank = BANK_205
    locations = MemoryLocation(address=0x1b, type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfd


class ControlGearOutputCurrentPercent(NumericValue):
    """Control Gear Output Current Percent

    Control gear output current in % related to the nominal output
    current setting of the control gear.

    ControlGearOutputCurrentPercent shall include all control gear
    internal reductions of output current except reduction by constant
    lumen functionality.

    NOTE Example:

    ControlGearOutputCurrentPercent includes the following reductions
    of output current:

    - Reduction due to external supply over/under voltage
    - Reduction due to power limitation
    - Reduction due to thermal overload of control gear
    - Reduction due to thermal overload of light source

    ControlGearOutputCurrentPercent excludes the following changes of
    nominal output current:

    - Changes due to constant lumen functionality

    Valid in the range 0..100; TMASK is supported
    """
    bank = BANK_205
    unit = '%'
    locations = MemoryLocation(address=0x1c, type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 100


class LightSourceDiagnosticBankVersion(NumericValue):
    """Version of the light source diagnostics memory bank
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x03, default=0x01,
                               type_=MemoryType.ROM)


class LightSourceStartCounterResettable(NumericValue):
    """Light Source Start Counter Resettable

    Counts the starts of the light source.

    Counts one step up for every 0 to 1 transition of the lampOn bit.

    Valid in the range 0..0xfffffd; TMASK is supported

    An attempt to write a value ≥ (MASK-1) to
    LightSourceStartCounterResettable shall result in the same
    behaviour as if the memory location is not implemented.

    Note: This means NO REPLY to the WRITE MEMORY LOCATION command
    when attempting to write a value ≥ (MASK-1) to
    LightSourceStartCounterResettable. For this case, NO REPLY occurs
    when writing to the final byte of this multi-byte value (normally
    the LSB).
    """
    bank = BANK_206
    locations = MemoryRange(start=0x04, end=0x06, default=0x00,
                            type_=MemoryType.NVM_RW)
    tmask_supported = True
    max_value = 0xfffffd


class LightSourceStartCounter(NumericValue):
    """Light Source Start Counter

    Counts the starts of the light source.

    Counts one step up for every 0 to 1 transition of the lampOn bit.

    Valid in the range 0..0xfffffd; TMASK is supported
    """
    bank = BANK_206
    locations = MemoryRange(start=0x07, end=0x09, default=0x00,
                            type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffd


class LightSourceOnTimeResettable(NumericValue):
    """Light Source On Time Resettable in s

    Counts the light source operating time in seconds.

    Counts up during the time where lampOn bit = 1.

    Valid in the range 0..0xfffffffd; TMASK is supported

    An attempt to write a value ≥ (MASK-1) to
    LightSourceOnTimeResettable shall result in the same behaviour as
    if the memory location is not implemented.

    Note: This means NO REPLY to the WRITE MEMORY LOCATION command
    when attempting to write a value ≥ (MASK-1) to
    LightSourceOnTimeResettable.  For this case, NO REPLY occurs when
    writing to the final byte of this multi-byte value (normally the
    LSB).
    """
    bank = BANK_206
    unit = 's'
    locations = MemoryRange(start=0x0a, end=0x0d, default=0x00,
                            type_=MemoryType.NVM_RW)
    tmask_supported = True
    max_value = 0xfffffffd


class LightSourceOnTime(NumericValue):
    """Light Source On Time in s

    Counts the light source operating time in seconds.

    Counts up during the time where lampOn bit = 1.

    Valid in the range 0..0xfffffffd; TMASK is supported
    """
    bank = BANK_206
    unit = 's'
    locations = MemoryRange(start=0x0e, end=0x11, default=0x00,
                            type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffffd


class LightSourceVoltage(FixedScaleNumericValue):
    """Light Source Voltage in V

    Indicates the actual control gear output voltage

    TMASK is supported
    """
    bank = BANK_206
    unit = 'V'
    scaling_factor = Decimal("0.1")
    locations = MemoryRange(start=0x12, end=0x13,
                            type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfffd


class LightSourceCurrent(FixedScaleNumericValue):
    """Light Source Current in A

    Indicates the actual control gear output current

    TMASK is supported
    """
    bank = BANK_206
    unit = 'A'
    scaling_factor = Decimal("0.001")
    locations = MemoryRange(start=0x14, end=0x15,
                            type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfffd


class LightSourceOverallFailureCondition(BinaryValue):
    """Light Source Overall Failure Condition

    Failure condition flag indication as follows:
    LightSourceOverallFailureCondition reflects the status of “lampFailure”.

    TMASK is supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x16, type_=MemoryType.RAM_RO)
    tmask_supported = True


class LightSourceOverallFailureConditionCounter(NumericValue):
    """Light Source Overall Failure Condition Counter

    Valid in the range 0..0xfd; TMASK is supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x17, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfd


class LightSourceShortCircuit(BinaryValue):
    """Light Source Short Circuit

    Failure condition flag indication as follows:

    LightSourceShortCircuit = 1 if the light source has a lamp failure
    with short circuit according to QUERY LAMP FAILURE defined in
    IEC62386-102:2014.

    Otherwise: LightSourceShortCircuit = 0

    TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x18, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class LightSourceShortCircuitCounter(NumericValue):
    """Light Source Short Circuit Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x19, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class LightSourceOpenCircuit(BinaryValue):
    """Light Source Open Circuit

    Failure condition flag indication as follows:

    LightSourceOpenCircuit = 1 if the light source has a lamp failure
    with open circuit according to QUERY LAMP FAILURE defined in
    IEC62386-102:2014.

    Otherwise: LightSourceOpenCircuit = 0

    TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1a, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class LightSourceOpenCircuitCounter(NumericValue):
    """Light Source Open Circuit Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1b, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class LightSourceThermalDerating(BinaryValue):
    """Light Source Thermal Derating

    Failure condition flag indication as follows:

    LightSourceThermalDerating = 1 if LightSourceTemperature >
    LightSourceThermalDerating threshold.

    Otherwise: LightSourceThermalDerating = 0.

    LightSourceThermalDerating threshold shall fulfil the following
    conditions:

    The value of the LightSourceThermalDerating threshold is such that
    lifetime and/or performance of the light source could be affected
    if the LightSourceTemperature is higher than the threshold.

    If LightSourceThermalDerating = 1 the output current of the
    control gear may be reduced.

    TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1c, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class LightSourceThermalDeratingCounter(NumericValue):
    """Light Source Thermal Derating Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1d, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class LightSourceThermalShutdown(BinaryValue):
    """Light Source Thermal Shutdown

    Failure condition flag indication as follows:

    LightSourceThermalShutdown = 1 if control gear temperature >
    LightSourceThermalShutdown threshold.

    Otherwise: LightSourceThermalShutdown = 0.

    LightSourceThermalShutdown threshold shall fulfil the following
    conditions:

    The value of the LightSourceThermalShutdown threshold is such that
    lifetime and/or performance of the light source could be affected
    if the LightSourceTemperature is higher than the threshold.
    LightSourceThermalShutdown threshold shall be higher than
    LightSourceThermalDerating threshold.

    If LightSourceThermalShutdown = 1 the output current of the
    control gear shall be reduced to zero.

    TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1e, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True


class LightSourceThermalShutdownCounter(NumericValue):
    """Light Source Thermal Shutdown Counter

    Valid in the range 0..0xfd; TMASK and MASK are supported
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x1f, default=0x00,
                               reset=0x0e, type_=MemoryType.NVM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class LightSourceTemperature(TemperatureValue):
    """Light Source Temperature in °C

    Indicates the temperature of the light source.

    NOTE The temperature should be measured by an external sensor that is
    thermally coupled to the light source.

    NOTE The interface between sensor and controlgear is manufacturer
    specific and is configured in a manufacturer specific way.
    """
    bank = BANK_206
    locations = MemoryLocation(address=0x20, type_=MemoryType.RAM_RO)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd
