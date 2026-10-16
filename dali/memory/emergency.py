"""Memory bank 208 from IEC 62386-202 (self-contained emergency lighting).

Section 9.15.6, Table 18: information about the control gear, lamp and
battery of a device-type-1 (emergency) control gear.
"""
from .location import (
    FixedScaleNumericValue,
    MemoryBank,
    MemoryLocation,
    MemoryRange,
    MemoryType,
    NumericValue,
    TemperatureValue,
)

# Table 18 lists 0x32 as the default last addressable location but also
# defines a value at 0x33 ("Performed on this battery"); declare the bank
# up to 0x33 so that value is treated as addressable when a device reports
# it. read_all() always honours the device's own reported last address.
BANK_208 = MemoryBank(208, 0x33, has_lock=True, has_latch=True)


class MemoryBankVersion(NumericValue):
    """Version of memory bank 208."""
    bank = BANK_208
    locations = MemoryLocation(address=0x03, default=0x01, type_=MemoryType.ROM)


class ControlGearMaxReferenceTemperature(TemperatureValue):
    """Control gear maximum reference temperature, typically at the Tc point."""
    bank = BANK_208
    locations = MemoryLocation(address=0x04, type_=MemoryType.ROM)
    mask_supported = True
    min_value = 0
    max_value = 0xFD


class ControlGearTemperature(TemperatureValue):
    """Internal temperature of the control gear."""
    bank = BANK_208
    locations = MemoryLocation(address=0x05, type_=MemoryType.RAM_RO)
    mask_supported = True
    tmask_supported = True
    min_value = 0
    max_value = 0xFD


class MinControlGearTemperatureTotal(TemperatureValue):
    """Minimum measured gear temperature (total)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x06, type_=MemoryType.NVM_RO)
    mask_supported = True
    tmask_supported = True
    min_value = 0
    max_value = 0xFD


class MaxControlGearTemperatureTotal(TemperatureValue):
    """Maximum measured gear temperature (total)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x07, type_=MemoryType.NVM_RO)
    mask_supported = True
    tmask_supported = True
    min_value = 0
    max_value = 0xFD


class MinControlGearTemperatureCurrentBattery(TemperatureValue):
    """Minimum measured gear temperature (current battery)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x08, type_=MemoryType.NVM_RO)
    mask_supported = True
    tmask_supported = True
    min_value = 0
    max_value = 0xFD


class MaxControlGearTemperatureCurrentBattery(TemperatureValue):
    """Maximum measured gear temperature (current battery)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x09, type_=MemoryType.NVM_RO)
    mask_supported = True
    tmask_supported = True
    min_value = 0
    max_value = 0xFD


class AveragePowerDuringCharging(FixedScaleNumericValue):
    """Average power during battery charging; 0xFD means 25.3 W or greater."""
    bank = BANK_208
    unit = 'W'
    scaling_factor = 0.1
    locations = MemoryLocation(address=0x0A, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class AveragePowerDuringMaintenance(FixedScaleNumericValue):
    """Average power during battery charge maintenance; 0xFD means 25.3 W or
    greater."""
    bank = BANK_208
    unit = 'W'
    scaling_factor = 0.1
    locations = MemoryLocation(address=0x0B, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class RatedDuration(FixedScaleNumericValue):
    """Rated duration time in minutes (stored in units of 2 min)."""
    bank = BANK_208
    unit = 'min'
    scaling_factor = 2
    locations = MemoryLocation(address=0x0C, type_=MemoryType.NVM_RO)


class FunctionTestTime(NumericValue):
    """Nominal function test time in seconds; 0xFD means 253 s or greater."""
    bank = BANK_208
    unit = 's'
    locations = MemoryLocation(address=0x0D, type_=MemoryType.NVM_RO)
    min_value = 5
    max_value = 0xFD


class BatteryRechargeTime(FixedScaleNumericValue):
    """Nominal battery recharge time in minutes (stored in units of 10 min);
    0xFD means 2530 min or greater."""
    bank = BANK_208
    unit = 'min'
    scaling_factor = 10
    locations = MemoryLocation(address=0x0E, type_=MemoryType.NVM_RO)
    min_value = 1
    max_value = 0xFD


class BatteryFailureCounter(NumericValue):
    """Battery failure counter."""
    bank = BANK_208
    locations = MemoryLocation(address=0x0F, type_=MemoryType.NVM_RO)
    mask_supported = True
    max_value = 0xFD


class BatteryCutOffCounter(NumericValue):
    """Count of transitions from below to above battery cut-off voltage;
    0xFD means 253 or greater."""
    bank = BANK_208
    locations = MemoryLocation(address=0x10, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class LampCutOffCounterTotal(NumericValue):
    """Count of transitions from above to below lamp cut-off voltage (total)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x11, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class LampCutOffCounterCurrentBattery(NumericValue):
    """Count of transitions from above to below lamp cut-off voltage
    (current battery)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x12, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class LampEmergencyTimeTotal(NumericValue):
    """Lamp emergency time (total) in minutes; 0xFFFFFD means 16777213 min or
    greater."""
    bank = BANK_208
    unit = 'min'
    locations = MemoryRange(start=0x13, end=0x15, type_=MemoryType.NVM_RO)
    max_value = 0xFFFFFD


class LampEmergencyTimeCurrentBattery(NumericValue):
    """Lamp emergency time (current battery) in minutes; 0xFFFFFD means
    16777213 min or greater."""
    bank = BANK_208
    unit = 'min'
    locations = MemoryRange(start=0x16, end=0x18, type_=MemoryType.NVM_RO)
    max_value = 0xFFFFFD


class BatteryConnectedTimeTotal(NumericValue):
    """Battery connected time (total) in days; 0xFFFD means 65533 days or
    greater."""
    bank = BANK_208
    unit = 'd'
    locations = MemoryRange(start=0x19, end=0x1A, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class BatteryConnectedTimeCurrentBattery(NumericValue):
    """Battery connected time (current battery) in days; 0xFFFD means 65533
    days or greater."""
    bank = BANK_208
    unit = 'd'
    locations = MemoryRange(start=0x1B, end=0x1C, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class CircuitFailureCounter(NumericValue):
    """Counts transitions of failure status bit 0 (circuit failure)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x1D, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class BatteryDurationFailureCounter(NumericValue):
    """Counts transitions of failure status bit 1 (battery duration failure)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x1E, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class BatteryFailureStatusCounter(NumericValue):
    """Counts transitions of failure status bit 2 (battery failure)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x1F, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class EmergencyLampFailureCounter(NumericValue):
    """Counts transitions of failure status bit 3 (emergency lamp failure)."""
    bank = BANK_208
    locations = MemoryLocation(address=0x20, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class FunctionTestMaxDelayExceededCounter(NumericValue):
    """Counts transitions of failure status bit 4."""
    bank = BANK_208
    locations = MemoryLocation(address=0x21, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class DurationTestMaxDelayExceededCounter(NumericValue):
    """Counts transitions of failure status bit 5."""
    bank = BANK_208
    locations = MemoryLocation(address=0x22, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class FunctionTestFailedCounterTotal(NumericValue):
    """Counts transitions of failure status bit 6 (total); 0xFFFD means 65533
    or greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x23, end=0x24, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class DurationTestFailedCounterTotal(NumericValue):
    """Counts transitions of failure status bit 7 (total); 0xFD means 253 or
    greater."""
    bank = BANK_208
    locations = MemoryLocation(address=0x25, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class FunctionTestFailedCounterCurrentBattery(NumericValue):
    """Counts transitions of failure status bit 6 (current battery); 0xFFFD
    means 65533 or greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x26, end=0x27, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class DurationTestFailedCounterCurrentBattery(NumericValue):
    """Counts transitions of failure status bit 7 (current battery); 0xFD means
    253 or greater."""
    bank = BANK_208
    locations = MemoryLocation(address=0x28, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class StartFunctionTestCounter(NumericValue):
    """Counts transitions into function test mode; 0xFFFD means 65533 or
    greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x29, end=0x2A, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class StartDurationTestCounterTotal(NumericValue):
    """Counts transitions into duration test mode (total); 0xFD means 253 or
    greater."""
    bank = BANK_208
    locations = MemoryLocation(address=0x2B, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class StartDurationTestCounterCurrentBattery(NumericValue):
    """Counts transitions into duration test mode (current battery); 0xFD means
    253 or greater."""
    bank = BANK_208
    locations = MemoryLocation(address=0x2C, type_=MemoryType.NVM_RO)
    max_value = 0xFD


class RestModeCounter(NumericValue):
    """Counts transitions into rest mode; 0xFFFD means 65533 or greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x2D, end=0x2E, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class EmergencyModeCounterTotal(NumericValue):
    """Counts transitions into emergency mode (total); 0xFFFD means 65533 or
    greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x2F, end=0x30, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class EmergencyModeCounterCurrentBattery(NumericValue):
    """Counts transitions into emergency mode (current battery); 0xFFFD means
    65533 or greater."""
    bank = BANK_208
    locations = MemoryRange(start=0x31, end=0x32, type_=MemoryType.NVM_RO)
    max_value = 0xFFFD


class PerformedOnThisBattery(NumericValue):
    """Bitmap of modes/tests that occurred on the current battery.

    Bit 0: rest mode was active at least once
    Bit 1: battery is successfully charging or maintained at full charge
    Bit 2: emergency mode was active at least once
    Bit 3: extended emergency mode was active at least once
    Bit 4: function test was active at least once
    Bit 5: duration test was active at least once
    """
    bank = BANK_208
    locations = MemoryLocation(address=0x33, type_=MemoryType.RAM_RO)
