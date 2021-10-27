from .location import MemoryBank, MemoryLocation, MemoryRange, MemoryType, \
    NumericValue, FixedScaleNumericValue, TemperatureValue

# Memory bank definitions from DiiA Specification, DALI Part 253 -
# Diagnostics & Maintenance, Version 1.1, October 2019
BANK_207 = MemoryBank(207, 0x07, has_lock=True)

# In this module, MASK indicates 'unknown'


class LuminaireMaintenanceBankVersion(NumericValue):
    """Version of the luminaire maintenance memory bank
    """
    bank = BANK_207
    locations = (MemoryLocation(address=0x03, default=0x01,
                                type_=MemoryType.ROM),)


class RatedMedianUsefulLifeOfLuminaire(FixedScaleNumericValue):
    """Rated Median Useful Life Of Luminaire in h

    The parameter represents the rated median useful life time of the
    luminaire (including light source and other components) as defined in
    IEC62722-2-1:2014.

    It is based on the L80/B50 criteria @ tq = 25°C

    tq: rated ambient temperature of the luminaire as defined in
    IEC62722-2-1:2014.

    NOTE RatedMedianUsefulLifeOfLuminaire represents the rated median
    useful life time of the luminaire including light source, control gear
    and other components.

    TMASK and MASK are supported
    """
    bank = BANK_207
    unit = 'h'
    scaling_factor = 1000
    locations = (MemoryLocation(address=0x04, default=0xff,
                                type_=MemoryType.NVM_RW_L),)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class InternalControlGearReferenceTemperature(TemperatureValue):
    """Internal Control Gear Reference Temperature in °C

    The parameter represents the internal control gear reference temperature.

    The value is derived by the luminaire manufacturer by measuring the
    value ControlGearTemperature at tq = 25°C, at rated luminaire power
    (at 100% dimming level).

    tq: rated ambient temperature of the luminaire as defined in
    IEC62722-2-1:2014.

    TMASK and MASK are supported
    """
    bank = BANK_207
    locations = (MemoryLocation(address=0x05, default=0xff,
                                type_=MemoryType.NVM_RW_L),)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfd


class RatedMedianUsefulLightSourceStarts(FixedScaleNumericValue):
    """Rated Median Useful Light Source Starts

    The parameter represents the rated median useful light source starts
    of the luminaire.

    A start is defined by 0 to 1 transition of the lampOn bit.

    TMASK and MASK are supported
    """
    "RatedMedianUsefulLightSourceStarts",
    bank = BANK_207
    scaling_factor = 100
    locations = MemoryRange(start=0x06, end=0x07, default=0xff,
                            type_=MemoryType.NVM_RW_L)
    tmask_supported = True
    mask_supported = True
    max_value = 0xfffd
