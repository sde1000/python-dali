from .location import MemoryLocation, MemoryType, NumericValue, LockableValueMixin, FixedScaleNumericValue, \
    BinaryValue, TemperatureValue

"""The mememory bank definitions from
DiiA Specification, DALI Part 253 - Diagnostics & Maintenance, Version 1.1, October 2019"""

class ControlGearOperatingTime(NumericValue):
    """Control Gear Operating Time in s
    Counts the control gear operating time in seconds if the control gear is powered regardless of the
    status of lampOn bit."""

    unit = 's'

    locations = (
        MemoryLocation(bank=205, address=0x04, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=205, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=205, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=205, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

class ControlGearStartCounter(NumericValue):
    """Control Gear Start Counter
    Counts the number of control gear starts that are induced by a power cycle of the external supply. A
    power cycle shall be counted if the power on time is at least 600ms."""

    locations = (
        MemoryLocation(bank=205, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=205, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=205, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

class ControlGearExternalSupplyVoltage(FixedScaleNumericValue):
    """Control Gear External Supply Voltage in Vrms
    RMS value of external supply voltage"""

    unit = 'Vrms'

    scaling_factor = 0.1

    locations = (
        MemoryLocation(bank=205, address=0x0b, default=0x0c, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=205, address=0x0c, default=0x0c, reset=None, type_=MemoryType.RAM_RO)
    )

class ControlGearExternalSupplyVoltageFrequency(NumericValue):
    """Control Gear External Supply Voltag Frequency in Hz
    Frequency of external supply voltage.
    Indication as follows: 0 in case of 0 Hz (pure DC or rectified AC voltage).
    NOTE Examples for frequency indication:
    17 in case of 16,7 Hz
    50 in case of 50 Hz
    60 in case of 60 Hz"""

    unit = 'Hz'

    locations = (MemoryLocation(bank=205, address=0x0d, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearPowerFactor(FixedScaleNumericValue):
    """Control Gear Power Factor"""

    scaling_factor = 0.01

    locations = (MemoryLocation(bank=205, address=0x0e, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearOverallFailureCondition(BinaryValue):
    """Control Gear Overall Failure Condition
    Failure condition flag indication as follows:
    ControlGearOverallFailureCondition reflects the status of ``controlGearFailure``."""

    locations = (MemoryLocation(bank=205, address=0x0f, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearOverallFailureConditionCounter(NumericValue):
    """Control Gear Overall Failure Condition Counter"""

    locations = (MemoryLocation(bank=205, address=0x10, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearExternalSupplyUndervoltage(BinaryValue):
    """Control Gear External Supply Undervoltage
    Failure condition flag indication as follows:
    ControlGearExternalSupplyUndervoltage = 1 if
    ControlGearExternalSupplyVoltage < ControlGearExternalSupplyUndervoltage threshold.
    Otherwise: ControlGearExternalSupplyUndervoltage = 0.
    ControlGearExternalSupplyUndervoltage threshold shall fulfil the following conditions:
    ControlGearExternalSupplyUndervoltage threshold shall be lower than the lower end of the specified input voltage
    range of the control gear and the value of the ControlGearExternalSupplyUndervoltage threshold is such that
    lifetime and/or performance of the control gear could be affected if the ControlGearExternalSupplyVoltageis lower
    than the threshold.
    NOTE Two different thresholds can be implemented for AC and for DC supply voltage.
    Example:
    Control gear datasheet:
    Nominal input voltage: 220 – 240 V
    Input voltage ac: 198 – 264 V
    Input voltage dc: 176 – 276 V"""

    locations = (MemoryLocation(bank=205, address=0x11, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearExternalSupplyUndervoltageCounter(NumericValue):
    """Control Gear External Supply Undervoltage Counter"""

    locations = (MemoryLocation(bank=205, address=0x12, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearExternalSupplyOvervoltage(BinaryValue):
    """Control Gear External Supply Overvoltage
    Failure condition flag indication as follows: 
    ControlGearExternalSupplyOvervoltage = 1 if
    ControlGearExternalSupplyVoltage > ControlGearExternalSupplyOvervoltage threshold.
    Otherwise: ControlGearExternalSupplyOvervoltage = 0.
    ControlGearExternalSupplyOvervoltage threshold shall fulfil the following conditions:
    ControlGearExternalSupplyOvervoltage threshold shall be higher than the higher end of the specified input voltage
    range of the control gear and the value of the ControlGearExternalSupplyOvervoltage threshold is such that
    lifetime and/or performance of the control gear could be affected if the ControlGearExternalSupplyVoltage is
    higher than the threshold.
    NOTE Two different thresholds can be implemented for AC and for DC supply voltage.
    Example:
    Control gear datasheet:
    Nominal input voltage: 220 – 240 V
    Input voltage ac: 198 – 264 V
    Input voltage dc: 176 – 276 V"""

    locations = (MemoryLocation(bank=205, address=0x13, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearExternalSupplyOvervoltageCounter(NumericValue):
    """Control Gear External Supply Overvoltage Counter"""

    locations = (MemoryLocation(bank=205, address=0x14, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearOutputPowerLimitation(BinaryValue):
    """Control Gear Output Power Limitation
    Failure condition flag indication as follows:
    ControlGearOutputPowerLimitation = 1 if 
    control gear output power > ControlGearOutputPowerLimitation threshold.
    Otherwise: ControlGearOutputPowerLimitation = 0.
    ControlGearOutputPowerLimitation threshold represents the output power limit of the control gear.
    NOTE ControlGearOutputPowerLimitation = 1 if the control gear limits the output current due to its internal power
    limitation. This is the case if the LED voltage multiplied with the control gear output current is higher than the
    output power limit of the control gear."""

    locations = (MemoryLocation(bank=205, address=0x15, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearOutputPowerLimitationCounter(NumericValue):
    """Control Gear Output Power Limitation Counter"""

    locations = (MemoryLocation(bank=205, address=0x16, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearThermalDerating(BinaryValue):
    """Control Gear Thermal Derating
    Failure condition flag indication as follows: 
    ControlGearThermalDerating = 1 if
    ControlGearTemperature > ControlGearThermalDerating threshold.
    Otherwise: ControlGearThermalDerating = 0.
    ControlGearThermalDerating threshold shall fulfil the following conditions:
    The value of the ControlGearThermalDerating threshold is such that lifetime and/or performance of the control gear
    could be affected if the ControlGearTemperature is higher than the threshold.
    If ControlGearThermalDerating = 1 the output current of the control gear may be reduced."""

    locations = (MemoryLocation(bank=205, address=0x17, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearThermalDeratingCounter(NumericValue):
    """Control Gear Thermal Derating Counter"""

    locations = (MemoryLocation(bank=205, address=0x18, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearThermalShutdown(BinaryValue):
    """Control Gear Thermal Shutdown
    Failure condition flag indication as follows:
    ControlGearThermalShutdown = 1 if
    ControlGearTemperature > ControlGearThermalShutdown threshold.
    Otherwise: ControlGearThermalShutdown = 0.
    ControlGearThermalShutdown threshold shall fulfil the following conditions:
    The value of the ControlGearThermalShutdown threshold is such that lifetime and/or performance of the control gear
    could be affected if the ControlGearTemperature is higher than the threshold.
    ControlGearThermalShutdown threshold shall be higher than ControlGearThermalDerating threshold.
    If ControlGearThermalShutdown = 1 the output current of the control gear shall be reduced to zero."""

    locations = (MemoryLocation(bank=205, address=0x19, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearThermalShutdownCounter(NumericValue):
    """Control Gear Thermal Shutdown Counter"""

    locations = (MemoryLocation(bank=205, address=0x1a, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class ControlGearTemperature(TemperatureValue):
    """Control Gear Temperature in °C
    Indicates the internal temperature of the control gear.
    NOTE The temperature indicated by ControlGearTemperature is an internal temperature and may be different from the
    Tc temperature."""

    locations = (MemoryLocation(bank=205, address=0x1b, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class ControlGearOutputCurrentPercent(NumericValue):
    """Control Gear Output Current Percent
    Control gear output current in % related to the nominal output current setting of the control gear.
    ControlGearOutputCurrentPercent shall include all control gear internal reductions of output current except
    reduction by constant lumen functionality.
    NOTE Example:
    ControlGearOutputCurrentPercent includes the following reductions of output current:
    - Reduction due to external supply over/under voltage
    - Reduction due to power limitation
    - Reduction due to thermal overload of control gear
    - Reduction due to thermal overload of light source

    ControlGearOutputCurrentPercent excludes the following changes of nominal output current:
    - Changes due to constant lumen functionality"""

    unit = '%'

    locations = (MemoryLocation(bank=205, address=0x1c, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceStartCounterResettable(NumericValue, LockableValueMixin):
    """Light Source Start Counter Resettable
    Counts the starts of the light source.
    Counts one step up for every 0 to 1 transition of the lampOn bit."""

    locations = (
        MemoryLocation(bank=206, address=0x04, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x05, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x06, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

class LightSourceStartCounter(NumericValue):
    """Light Source Start Counter
    Counts the starts of the light source.
Counts one step up for every 0 to 1 transition of the lampOn bit."""

    locations = (
        MemoryLocation(bank=206, address=0x07, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=206, address=0x08, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=206, address=0x09, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

class LightSourceOnTimeResettable(NumericValue, LockableValueMixin):
    """Light Source On Time Resettable in s
    Counts the light source operating time in seconds.
    Counts up during the time where lampOn bit = 1."""

    unit = 's'

    locations = (
        MemoryLocation(bank=206, address=0x0a, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x0b, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x0c, default=0x00, reset=None, type_=MemoryType.NVM_RW),
        MemoryLocation(bank=206, address=0x0d, default=0x00, reset=None, type_=MemoryType.NVM_RW)
    )

class LightSourceOnTime(NumericValue):
    """Light Source On Time in s
    Counts the light source operating time in seconds.
Counts up during the time where lampOn bit = 1."""

    unit = 's'

    locations = (
        MemoryLocation(bank=206, address=0x0e, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=206, address=0x0f, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=206, address=0x10, default=0x00, reset=None, type_=MemoryType.NVM_RO),
        MemoryLocation(bank=206, address=0x11, default=0x00, reset=None, type_=MemoryType.NVM_RO)
    )

class LightSourceVoltage(FixedScaleNumericValue):
    """Light Source Voltage in V
    Indicates the actual control gear output voltage"""

    unit = 'V'

    scaling_factor = 0.1

    locations = (
        MemoryLocation(bank=206, address=0x12, default=0x0c, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=206, address=0x13, default=0x0c, reset=None, type_=MemoryType.RAM_RO)
    )

class LightSourceCurrent(FixedScaleNumericValue):
    """Light Source Current in A
    Indicates the actual control gear output current"""

    unit = 'A'

    scaling_factor = 0.001

    locations = (
        MemoryLocation(bank=206, address=0x14, default=0x0c, reset=None, type_=MemoryType.RAM_RO),
        MemoryLocation(bank=206, address=0x15, default=0x0c, reset=None, type_=MemoryType.RAM_RO)
    )

class LightSourceOverallFailureCondition(BinaryValue):
    """Light Source Overall Failure Condition
    Failure condition flag indication as follows:
    LightSourceOverallFailureCondition reflects the status of “lampFailure”."""

    locations = (MemoryLocation(bank=206, address=0x16, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceOverallFailureConditionCounter(NumericValue):
    """Light Source Overall Failure Condition Counter"""

    locations = (MemoryLocation(bank=206, address=0x17, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class LightSourceShortCircuit(BinaryValue):
    """Light Source Short Circuit
    Failure condition flag indication as follows:
    LightSourceShortCircuit = 1 if the light source has a lamp failure with short circuit according to
    QUERY LAMP FAILURE defined in IEC62386-102:2014.
    Otherwise: LightSourceShortCircuit = 0"""

    locations = (MemoryLocation(bank=206, address=0x18, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceShortCircuitCounter(NumericValue):
    """Light Source Short Circuit Counter"""

    locations = (MemoryLocation(bank=206, address=0x19, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class LightSourceOpenCircuit(BinaryValue):
    """Light Source Open Circuit
    Failure condition flag indication as follows:
    LightSourceOpenCircuit = 1 if the light source has a lamp failure with open circuit according to
    QUERY LAMP FAILURE defined in IEC62386-102:2014.
    Otherwise: LightSourceOpenCircuit = 0"""

    locations = (MemoryLocation(bank=206, address=0x1a, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceOpenCircuitCounter(NumericValue):
    """Light Source Open CircuitCounter"""

    locations = (MemoryLocation(bank=206, address=0x1b, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class LightSourceThermalDerating(BinaryValue):
    """Light Source Thermal Derating
    Failure condition flag indication as follows:
    LightSourceThermalDerating = 1 if
    LightSourceTemperature > LightSourceThermalDerating threshold.
    Otherwise:
    LightSourceThermalDerating = 0.
    LightSourceThermalDerating threshold shall fulfil the following conditions:
    The value of the LightSourceThermalDerating threshold is such that lifetime and/or performance of the light source
    could be affected if the LightSourceTemperature is higher than the threshold.
    If LightSourceThermalDerating = 1 the output current of the control gear may be reduced."""

    locations = (MemoryLocation(bank=206, address=0x1c, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceThermalDeratingCounter(NumericValue):
    """Light Source Thermal Derating Counter"""

    locations = (MemoryLocation(bank=206, address=0x1d, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class LightSourceThermalShutdown(BinaryValue):
    """Light Source Thermal Shutdown
    Failure condition flag indication as follows:
    LightSourceThermalShutdown = 1 if
    control gear temperature > LightSourceThermalShutdown threshold.
    Otherwise:
    LightSourceThermalShutdown = 0.
    LightSourceThermalShutdown threshold shall fulfil the following conditions:
    The value of the LightSourceThermalShutdown threshold is such that lifetime and/or performance of the light source
    could be affected if the LightSourceTemperature is higher than the threshold.
    LightSourceThermalShutdown threshold shall be higher than LightSourceThermalDerating threshold.
    If LightSourceThermalShutdown = 1 the output current of the control gear shall be reduced to zero."""

    locations = (MemoryLocation(bank=206, address=0x1e, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

class LightSourceThermalShutdownCounter(NumericValue):
    """Light Source Thermal Shutdown Counter"""

    locations = (MemoryLocation(bank=206, address=0x1f, default=0x00, reset=0x0e, type_=MemoryType.NVM_RO))

class LightSourceTemperature(TemperatureValue):
    """Light Source Temperature in °C
    Indicates the temperature of the light source.
    NOTE The temperature should be measured by an external sensor that is thermaly coupled to the light source.
    NOTE The interface between sensor and controlgear is manufacturer specific and is configured in a manufacturer
    specific way."""

    locations = (MemoryLocation(bank=206, address=0x20, default=0x0c, reset=None, type_=MemoryType.RAM_RO))

