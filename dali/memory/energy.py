from .location import MemoryBank, MemoryLocation, MemoryRange, \
    MemoryType, NumericValue, FlagValue
from decimal import Decimal

# Memory bank definitions from DiiA Specification, DALI Part 252 -
# Energy Reporting, Version 1.1, October 2019
BANK_202 = MemoryBank(202, 0x0F, has_latch=True)
BANK_203 = MemoryBank(203, 0x0F, has_latch=True)
BANK_204 = MemoryBank(204, 0x0F, has_latch=True)


class ScaledNumericValue(NumericValue):
    """A numeric value with scaling factor provided by the bus unit

    Scale is valid from 10^-6 to 10^6 and is read from the first
    memory location of the value. The remaining locations hold the
    value MSB first.

    Values are returned as Decimals to preserve precision.
    """
    # We remove a byte before checking for MASK or TMASK
    mask_length_adjust = -1

    @classmethod
    def raw_to_value(cls, raw):
        scaling_factor = pow(Decimal(10), int.from_bytes(
            raw[:1], 'big', signed=True))
        return int.from_bytes(raw[1:], 'big') * scaling_factor

    @classmethod
    def check_raw(cls, raw):
        # Check the scale factor here rather than in is_valid(); the
        # raw value passed to is_valid() by check_raw() will be
        # missing the scale factor
        if raw[0] > 6 and raw[0] < 0xfa:
            return FlagValue.Invalid
        # Ignore the first location when checking for MASK or TMASK
        return super().check_raw(raw[1:])


class ActiveBankVersion(NumericValue):
    """Version of the active energy and power memory bank
    """
    bank = BANK_202
    locations = MemoryLocation(address=0x03, default=0x01,
                               type_=MemoryType.ROM)


class ActiveEnergy(ScaledNumericValue):
    """Active Energy in Wh

    The integral of the instantaneous power over a time interval
    """
    bank = BANK_202
    unit = 'Wh'
    locations = (
        MemoryLocation(address=0x04, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x05, end=0x0a, default=0x00,
                    type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffffffffd


class ActivePower(ScaledNumericValue):
    """Active Power in W

    Under periodic conditions, meand value, taken over one period, of
    the instantaneous power
    """
    bank = BANK_202
    unit = 'W'
    locations = (
        MemoryLocation(address=0x0b, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x0c, end=0x0f, type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfffffffd


class ApparentBankVersion(NumericValue):
    """Version of the apparent energy and power memory bank
    """
    bank = BANK_203
    locations = MemoryLocation(address=0x03, default=0x01,
                               type_=MemoryType.ROM)


class ApparentEnergy(ScaledNumericValue):
    """Apparent Energy in VAh

    The integral of Apparent Power over a time interval
    """
    bank = BANK_203
    unit = 'VAh'
    locations = (
        MemoryLocation(address=0x04, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x05, end=0x0a, default=0x00,
                    type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffffffffd


class ApparentPower(ScaledNumericValue):
    """Apparent Power in VA

    The product of the rms voltage between the terminals of a
    two-terminal element or two-terminal circuit and the rms electric
    current in the element or circuit
    """
    bank = BANK_203
    unit = 'VA'
    locations = (
        MemoryLocation(address=0x0b, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x0c, end=0x0f, type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfffffffd


class LoadsideBankVersion(NumericValue):
    """Version of the loadside energy and power memory bank
    """
    bank = BANK_204
    locations = MemoryLocation(address=0x03, default=0x01,
                               type_=MemoryType.ROM)


class ActiveEnergyLoadside(ScaledNumericValue):
    """Loadside Active Energy in Wh

    The integral of Load side Power over a time interval
    """
    bank = BANK_204
    unit = 'Wh'
    locations = (
        MemoryLocation(address=0x04, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x05, end=0x0a, default=0x00,
                    type_=MemoryType.NVM_RO)
    tmask_supported = True
    max_value = 0xfffffffffffd


class ActivePowerLoadside(ScaledNumericValue):
    """Loadside Active Power in W

    The input power minus the sum of power used for the DALI bus power
    supply (if present) and the power used for the AUX power supply
    (if present).

    Note: the losses for both power supplies (if present) may be
    neglected in the measurement
    """
    bank = BANK_204
    unit = 'W'
    locations = (
        MemoryLocation(address=0x0b, type_=MemoryType.ROM),
    ) + MemoryRange(start=0x0c, end=0x0f, type_=MemoryType.RAM_RO)
    tmask_supported = True
    max_value = 0xfffffffd
