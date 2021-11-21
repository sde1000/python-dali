import unittest

from dali.tests import fakes
from dali.memory import info, diagnostics, energy, maintenance, oem
from dali.memory.location import MemoryBank, NumericValue, FlagValue
from dali.command import Command, Response
from dali.exceptions import ResponseError, MemoryLocationNotImplemented, \
    MemoryValueNotWriteable, MemoryLocationNotWriteable, MemoryWriteFailure
from dali.frame import BackwardFrame
from dali.gear.general import DTR0, DTR1, ReadMemoryLocation
from decimal import Decimal

# Test data: valid initial contents of memory banks

# Bank 0 is used unchanged from fakes.py


# OEM data
class FakeBank1(fakes.FakeMemoryBank):
    bank = oem.BANK_1
    initial_contents = [
        0x77, None, 0xff,  # Initially locked
        0x06, 0xf6, 0x29, 0x19, 0x22, 0x87,  # GTIN 7654321234567
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,  # Serial number 2
        0x00, 0x03,  # Content format ID 0x0003 -> DiiA spec part 251
        21,  # Year of manufacture 2021
        43,  # Week of manufacture 43
        0x05, 0xdc,  # Nominal input power 1500W
        0x00, 0x64,  # Power at minimum dim level 100W
        0x00, 0xdc,  # Nominal minimum AC mains voltage 220V
        0x00, 0xfa,  # Nominal maximum AC mains voltage 250V
        0x00, 0x3a, 0x98,  # Nominal light output 15000Lm
        0x64,  # CRI 100
        0x00, 0x01,  # CCT 1K
        0x05,  # Light distribution type "Type V"
        0x4f, 0x63, 0x74, 0x61, 0x72, 0x69, 0x6e, 0x65,  # Colour "Octarine"
        0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0x57, 0x69, 0x7a, 0x61, 0x72, 0x64, 0x27, 0x73,  # ID "Wizard's Staff"
        0x20, 0x53, 0x74, 0x61, 0x66, 0x66, 0x00, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  #
        0xff, 0xff, 0xff, 0xff,  # (end of ID string)
    ]


# Energy: bank 202 is "active", bank 203 is "apparent", bank 204 is "loadside"
class FakeBank202(fakes.FakeMemoryBank):
    bank = energy.BANK_202
    initial_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0x03,  # Scale to 10^3 ('kWh')
        0x00, 0x00, 0x00, 0x00, 0x00, 0x0a,  # 10kWh (10,000Wh)
        0x00,  # Scale to 10^0 ('W')
        0x00, 0x00, 0x03, 0xe8,  # 1000W
    ]


class FakeBank203(fakes.FakeMemoryBank):
    bank = energy.BANK_203
    initial_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0xff,  # Scale to 10^-1 (0.1)
        0x00, 0x00, 0x00, 0x00, 0x03, 0xe8,  # 100Wh
        0xfe,  # Scale to 10^-2 (0.01)
        0x00, 0x00, 0x03, 0xe8,  # 10W
    ]


class FakeBank204(fakes.FakeMemoryBank):
    bank = energy.BANK_204
    initial_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0xfa,  # Scale to 10^-6
        0x00, 0x00, 0x00, 0x01, 0x86, 0xa0,  # 0.1
        0x01,  # Scale to 10^1
        0x00, 0x00, 0x03, 0xe8,  # 10000
    ]


# Control gear diagnostics and maintenance
class FakeBank205(fakes.FakeMemoryBank):
    bank = diagnostics.BANK_205
    initial_contents = [
        0x1c, None, 0xff,
        0x01,  # Version 1
        0x00, 0x00, 0x0e, 0x10,  # Operating time 3600s
        0x00, 0x00, 0x0a,  # Start counter 10
        0x08, 0xfc,  # Supply voltage 230V
        50,  # Supply frequency 50Hz
        90,  # Power factor 0.90
        1,  # Overall failure condition True
        1,  # Overall failure condition counter 1
        1,  # External supply undervoltage True
        10,  # External supply undervoltage counter 10
        0,  # External supply overvoltage False
        11,  # External supply overvoltage counter 11
        0,  # Output power limitation False
        2,  # Output power limitation counter 2
        0,  # Control gear thermal derating False
        6,  # Control gear thermal derating counter 6
        0,  # Control gear thermal shutdown
        2,  # Control gear thermal shutdown counter 2
        90,  # Control gear temperature 30°C
        85,  # Control gear output current percent 85%
    ]


# Light source diagnostics and maintenance
class FakeBank206(fakes.FakeMemoryBank):
    bank = diagnostics.BANK_206
    initial_contents = [
        0x20, None, 0xff,
        0x01,  # Version 1
        0x00, 0x01, 0x2c,  # Light source start counter resettable 300
        0x00, 0x01, 0xf4,  # Light source start counter 500
        0x00, 0x00, 0x03, 0xe8,  # Light source on time resettable 1000
        0x00, 0x00, 0x0b, 0xb8,  # Light source on time 3000
        0x02, 0x58,  # Light source voltage 60.0V
        0x02, 0xbc,  # Light source current 700mA
        0,  # Light source overall failure condition False
        12,  # Light source overall failure condition counter 12
        0,  # Light source short circuit False
        15,  # Light source short circuit counter 15
        0,  # Light source open circuit False
        23,  # Light source open circuit counter 23
        1,  # Light source thermal derating True
        45,  # Light source thermal derating counter 45
        0,  # Light source thermal shutdown False
        67,  # Light source thermal shutdown counter 67
        160,  # Light source temperature 100°C
    ]


# Luminaire maintenance data
class FakeBank207(fakes.FakeMemoryBank):
    bank = maintenance.BANK_207
    initial_contents = [
        0x07, None, 0xff,
        0x01,  # Version 1
        50,  # Rated median useful life of luminaire, 50000 hours
        90,  # Internal control gear reference temperature, 30°C
        0x13, 0x88,  # Rated median useful light source starts, 500000
    ]


# Invalid / special memory bank contents
class InvalidBank1(fakes.FakeMemoryBank):
    """Strange version of bank 1

    This version of bank 1 has invalid contents, uses a non-standard
    lock byte value so cannot be written to successfully, and is
    missing half the luminaire colour and all the ID string.
    """
    bank = oem.BANK_1
    unlock_value = 0x54
    initial_contents = [
        40, None, 0xff,  # Only 40 bytes long, initially locked
        0x06, 0xf6, 0x29, 0x19, 0x22, 0x87,  # GTIN 7654321234567
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,  # Serial number 2
        0x00, 0x03,  # Content format ID 0x0003 -> DiiA spec part 251
        105,  # Year of manufacture invalid
        60,  # Week of manufacture invalid
        0xff, 0xff,  # Nominal input power MASK
        0xff, 0xff,  # Power at minimum dim level MASK
        0xff, 0xff,  # Nominal minimum AC mains voltage MASK
        0xff, 0xff,  # Nominal maximum AC mains voltage MASK
        0xff, 0xff, 0xff,  # Nominal light output MASK
        105,  # CRI invalid
        0xff, 0xfe,  # CCT "Part 209 implemented"
        0xff,  # Light distribution type MASK
    ]


class InvalidBank202(fakes.FakeMemoryBank):
    bank = energy.BANK_202
    initial_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0xaa,  # Scale is invalid
        0x00, 0x00, 0x00, 0x00, 0x00, 0x0a,  # Value is irrelevant
        0x00,  # Scale to 10^0 ('W')
        0xff, 0xff, 0xff, 0xfe,  # TMASK
    ]


class LatchTestBank203(fakes.FakeMemoryBank):
    """This version of Bank 203 returns different values when latched
    """
    bank = energy.BANK_203
    initial_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0xff,  # Scale to 10^-1 (0.1)
        0x00, 0x00, 0x00, 0x00, 0x03, 0xe8,  # 100Wh
        0xfe,  # Scale to 10^-2 (0.01)
        0x00, 0x00, 0x03, 0xe8,  # 10W
    ]
    latched_contents = [
        0x0f, None, 0xff,
        0x01,  # Version 1
        0xff,  # Scale to 10^-1 (0.1)
        0x00, 0x00, 0x00, 0x00, 0x05, 0xdc,  # 150Wh
        0xfe,  # Scale to 10^-2 (0.01)
        0x00, 0x00, 0x05, 0xdc,  # 15W
    ]

    def read(self, address):
        if self.contents[2] != 0xaa:
            return super().read(address)
        if address > self.contents[0]:
            return
        return self.latched_contents[address]


class InvalidBank207(fakes.FakeMemoryBank):
    bank = maintenance.BANK_207
    initial_contents = [
        0x07, None, 0xff,
        0x01,  # Version 1
        0xfe,  # Rated median useful life of luminaire TMASK
        0xff,  # Internal control gear reference temperature MASK
        0xff, 0xfe,  # Rated median useful light source starts TMASK
    ]


class BrokenBank1(fakes.FakeMemoryBank):
    """This version of Bank 1 has a weird problem with writing

    The WriteMemoryLocation command always returns 0xaa instead of the
    value written.
    """
    bank = oem.BANK_1

    def write(self, address, value):
        super().write(address, value)
        return 0xaa


class BrokenBank206(fakes.FakeMemoryBank):
    """This version of Bank 206 has a weird problem with updating DTR0

    DTR0 is not incremented on read or write.
    """
    bank = diagnostics.BANK_206
    nobble_dtr0_update = True
    initial_contents = [
        0x20, None, 0xff,
        0x01,  # Version 1
        0x00, 0x01, 0x2c,  # Light source start counter resettable 300
        0x00, 0x01, 0xf4,  # Light source start counter 500
        0x00, 0x00, 0x03, 0xe8,  # Light source on time resettable 1000
        0x00, 0x00, 0x0b, 0xb8,  # Light source on time 3000
        0x02, 0x58,  # Light source voltage 60.0V
        0x02, 0xbc,  # Light source current 700mA
        0,  # Light source overall failure condition False
        12,  # Light source overall failure condition counter 12
        0,  # Light source short circuit False
        15,  # Light source short circuit counter 15
        0,  # Light source open circuit False
        23,  # Light source open circuit counter 23
        1,  # Light source thermal derating True
        45,  # Light source thermal derating counter 45
        0,  # Light source thermal shutdown False
        67,  # Light source thermal shutdown counter 67
        160,  # Light source temperature 100°C
    ]


class TestMemoryBank(unittest.TestCase):
    def test_repr_memorybank(self):
        self.assertEqual(
            repr(MemoryBank(3, 45)),
            "MemoryBank(address=3, has_lock=False, has_latch=False)")

    def test_has_lock(self):
        self.assertEqual(MemoryBank(3, 45).has_lock, False)
        self.assertEqual(MemoryBank(3, 45, has_latch=True).has_lock, False)
        self.assertEqual(MemoryBank(3, 45, has_lock=True).has_lock, True)

    def test_has_latch(self):
        self.assertEqual(MemoryBank(3, 45).has_latch, False)
        self.assertEqual(MemoryBank(3, 45, has_lock=True).has_latch, False)
        self.assertEqual(MemoryBank(3, 45, has_latch=True).has_latch, True)


class TestLocations(unittest.TestCase):
    def test_str_memoryvalue(self):
        # str() on a concrete memory value class should return the class name
        # so that it is usable as a label.
        self.assertEqual(str(info.GTIN), 'GTIN')
        self.assertEqual(str(NumericValue),
                         "<class 'dali.memory.location.NumericValue'>")


class TestMemory(unittest.TestCase):
    def setUp(self):
        # The unit at address 0 behaves normally, the units at address
        # 1 and 2 have some oddities which we use to test special
        # value handling and write errors
        self.bus = fakes.Bus([
            fakes.Gear(0, memory_banks=(
                fakes.FakeBank0, FakeBank1, FakeBank202, FakeBank203,
                FakeBank204, FakeBank205, FakeBank206, FakeBank207)),
            fakes.Gear(1, memory_banks=(
                fakes.FakeBank0, InvalidBank1, InvalidBank202,
                LatchTestBank203, InvalidBank207)),
            fakes.Gear(2, memory_banks=(
                fakes.FakeBank0, BrokenBank1, BrokenBank206)),
        ])

    def _test_value(self, memory_value, expected, addr=0):
        r = self.bus.run_sequence(memory_value.read(addr))
        self.assertEqual(r, expected)

    def test_missingMemoryLocation(self):
        self.assertRaises(MemoryLocationNotImplemented, self.bus.run_sequence,
                          oem.LuminaireColor.read(1))
        self.assertRaises(MemoryLocationNotImplemented, self.bus.run_sequence,
                          oem.LuminaireIdentification.read(1))

    def test_lockByte(self):
        # Toggle the lock byte in bank 1 and check that values become
        # locked and unlocked as appropriate
        self.bus.run_sequence(oem.BANK_1.LockByte.write(0, 0xff))
        self.assertTrue(self.bus.run_sequence(
            oem.ManufacturerGTIN.is_locked(0)))
        self.bus.run_sequence(oem.BANK_1.LockByte.write(0, 0x55))
        self.assertFalse(self.bus.run_sequence(
            oem.ManufacturerGTIN.is_locked(0)))

    def test_isAddressable(self):
        self.assertTrue(self.bus.run_sequence(
            oem.LuminaireIdentification.is_addressable(0)))
        self.assertFalse(self.bus.run_sequence(
            oem.LuminaireIdentification.is_addressable(1)))

    def test_dtrHandling(self):
        # Instead of messing with run_sequence in fakes this dummy
        # is implemented. It returns commands in the sequence as
        # a list in place of its result.
        def dummy_run_sequence(seq):
            commands = []
            response = None
            while True:
                try:
                    cmd = seq.send(response)
                except StopIteration:
                    return commands
                response = Response(BackwardFrame(0))
                if isinstance(cmd, Command):
                    commands.append(cmd)

        commands = dummy_run_sequence(info.GTIN.read(0))
        dtr0_counter = 0
        dtr1_counter = 0
        for i, cmd in enumerate(commands):
            if i < 2:
                if isinstance(cmd, DTR0):
                    dtr0_counter += 1
                elif isinstance(cmd, DTR1):
                    dtr1_counter += 1
                else:
                    self.fail('DTR0 and DTR1 must be set before a memory location is read.')
            else:
                self.assertTrue(isinstance(cmd, ReadMemoryLocation))
        self.assertEqual(dtr0_counter, 1)
        self.assertEqual(dtr1_counter, 1)

    def test_memorybank_read_all(self):
        values = self.bus.run_sequence(info.BANK_0.read_all(0))
        # We can't rely on LastMemoryBank being unchanged, so remove it
        # from the results
        del values[info.LastMemoryBank]
        expected = {
            info.GTIN: 1234567654321,
            info.FirmwareVersion: "1.0",
            info.IdentificationNumber: 1,
            info.HardwareVersion: "2.1",
            info.Part101Version: "2.0",
            info.Part102Version: "2.0",
            info.Part103Version: "not implemented",
            info.DeviceUnitCount: 0,
            info.GearUnitCount: 1,
            info.UnitIndex: 0,
        }
        self.assertEqual(values, expected)

    def test_memorybank_read_all_latch(self):
        values = self.bus.run_sequence(energy.BANK_203.read_all(
            1, use_latch=False))
        expected = {
            energy.ApparentBankVersion: 1,
            energy.ApparentEnergy: Decimal("100"),
            energy.ApparentPower: Decimal("10"),
        }
        self.assertEqual(values, expected)
        values = self.bus.run_sequence(energy.BANK_203.read_all(1))
        expected = {
            energy.ApparentBankVersion: 1,
            energy.ApparentEnergy: Decimal("150"),
            energy.ApparentPower: Decimal("15"),
        }
        self.assertEqual(values, expected)

    def test_diagnostics(self):
        self._test_value(diagnostics.ControlGearDiagnosticBankVersion, 1)
        self._test_value(diagnostics.ControlGearOperatingTime, 3600)
        self._test_value(diagnostics.ControlGearStartCounter, 10)
        self._test_value(diagnostics.ControlGearExternalSupplyVoltage, 230)
        self._test_value(diagnostics.ControlGearExternalSupplyVoltageFrequency, 50)
        self._test_value(diagnostics.ControlGearPowerFactor, Decimal("0.9"))
        self._test_value(diagnostics.ControlGearOverallFailureCondition, True)
        self._test_value(diagnostics.ControlGearOverallFailureConditionCounter, 1)
        self._test_value(diagnostics.ControlGearExternalSupplyUndervoltage, True)
        self._test_value(diagnostics.ControlGearExternalSupplyUndervoltageCounter, 10)
        self._test_value(diagnostics.ControlGearExternalSupplyOvervoltage, False)
        self._test_value(diagnostics.ControlGearExternalSupplyUndervoltageCounter, 10)
        self._test_value(diagnostics.ControlGearExternalSupplyOvervoltage, False)
        self._test_value(diagnostics.ControlGearExternalSupplyOvervoltageCounter, 11)
        self._test_value(diagnostics.ControlGearOutputPowerLimitation, False)
        self._test_value(diagnostics.ControlGearOutputPowerLimitationCounter, 2)
        self._test_value(diagnostics.ControlGearThermalDerating, False)
        self._test_value(diagnostics.ControlGearThermalDeratingCounter, 6)
        self._test_value(diagnostics.ControlGearThermalShutdown, False)
        self._test_value(diagnostics.ControlGearThermalShutdownCounter, 2)
        self._test_value(diagnostics.ControlGearTemperature, 30)
        self._test_value(diagnostics.ControlGearOutputCurrentPercent, 85)
        self._test_value(diagnostics.LightSourceDiagnosticBankVersion, 1)
        self._test_value(diagnostics.LightSourceStartCounterResettable, 300)
        self._test_value(diagnostics.LightSourceStartCounter, 500)
        self._test_value(diagnostics.LightSourceOnTimeResettable, 1000)
        self._test_value(diagnostics.LightSourceOnTime, 3000)
        self._test_value(diagnostics.LightSourceVoltage, Decimal("60.0"))
        self._test_value(diagnostics.LightSourceCurrent, Decimal("0.7"))
        self._test_value(diagnostics.LightSourceOverallFailureCondition, False)
        self._test_value(diagnostics.LightSourceOverallFailureConditionCounter, 12)
        self._test_value(diagnostics.LightSourceShortCircuit, False)
        self._test_value(diagnostics.LightSourceShortCircuitCounter, 15)
        self._test_value(diagnostics.LightSourceOpenCircuit, False)
        self._test_value(diagnostics.LightSourceOpenCircuitCounter, 23)
        self._test_value(diagnostics.LightSourceThermalDerating, True)
        self._test_value(diagnostics.LightSourceThermalDeratingCounter, 45)
        self._test_value(diagnostics.LightSourceThermalShutdown, False)
        self._test_value(diagnostics.LightSourceThermalShutdownCounter, 67)
        self._test_value(diagnostics.LightSourceTemperature, 100)

    def test_energy(self):
        self._test_value(energy.ActiveBankVersion, 1)
        self._test_value(energy.ActiveEnergy, Decimal("10000"))
        self._test_value(energy.ActiveEnergy, FlagValue.Invalid, addr=1)
        self._test_value(energy.ActivePower, Decimal("1000"))
        self._test_value(energy.ActivePower, FlagValue.TMASK, addr=1)
        self._test_value(energy.ApparentBankVersion, 1)
        self._test_value(energy.ApparentEnergy, Decimal("100"))
        self._test_value(energy.ApparentPower, Decimal("10"))
        self._test_value(energy.LoadsideBankVersion, 1)
        self._test_value(energy.ActiveEnergyLoadside, Decimal("0.1"))
        self._test_value(energy.ActivePowerLoadside, Decimal("10000"))

    def test_maintenance(self):
        self._test_value(
            maintenance.LuminaireMaintenanceBankVersion, 1)
        self._test_value(
            maintenance.RatedMedianUsefulLifeOfLuminaire, 50000)
        self._test_value(
            maintenance.RatedMedianUsefulLifeOfLuminaire,
            FlagValue.TMASK, addr=1)
        self._test_value(
            maintenance.InternalControlGearReferenceTemperature, 30)
        self._test_value(
            maintenance.InternalControlGearReferenceTemperature,
            FlagValue.MASK, addr=1)
        self._test_value(
            maintenance.RatedMedianUsefulLightSourceStarts, 500000)
        self._test_value(
            maintenance.RatedMedianUsefulLightSourceStarts,
            FlagValue.TMASK, addr=1)

    def test_oem(self):
        self._test_value(oem.ManufacturerGTIN, 7654321234567)
        self._test_value(oem.LuminaireID, 2)
        self._test_value(oem.ContentFormatID, 3)
        self._test_value(oem.YearOfManufacture, 21)
        self._test_value(oem.YearOfManufacture, FlagValue.Invalid, addr=1)
        self._test_value(oem.WeekOfManufacture, 43)
        self._test_value(oem.WeekOfManufacture, FlagValue.Invalid, addr=1)
        self._test_value(oem.InputPowerNominal, 1500)
        self._test_value(oem.InputPowerNominal, FlagValue.MASK, addr=1)
        self._test_value(oem.InputPowerMinimumDim, 100)
        self._test_value(oem.InputPowerMinimumDim, FlagValue.MASK, addr=1)
        self._test_value(oem.MainsVoltageMinimum, 220)
        self._test_value(oem.MainsVoltageMaximum, 250)
        self._test_value(oem.LightOutputNominal, 15000)
        self._test_value(oem.CRI, 100)
        self._test_value(oem.CRI, FlagValue.Invalid, addr=1)
        self._test_value(oem.CCT, 1)
        self._test_value(oem.CCT, "Part 209 implemented", addr=1)
        self._test_value(oem.LightDistributionType, "Type V")
        self._test_value(oem.LightDistributionType, FlagValue.MASK, addr=1)
        self._test_value(oem.LuminaireColor, "Octarine")
        self._test_value(oem.LuminaireIdentification, "Wizard's Staff")

    def test_invalid_oem_strings(self):
        # Write an invalid ASCII string to the luminaire colour
        self.bus.run_sequence(
            oem.LuminaireIdentification.write_raw(
                0, [0x88, 0x3f, 0x00], allow_short_write=True))
        self.assertEqual(self.bus.run_sequence(
            oem.LuminaireIdentification.read(0)), FlagValue.Invalid)

    def test_info(self):
        # Default bank 0 contents from fakes.py
        self._test_value(info.GTIN, 1234567654321)
        self._test_value(info.FirmwareVersion, "1.0")
        self._test_value(info.IdentificationNumber, 1)
        self._test_value(info.HardwareVersion, "2.1")
        self._test_value(info.Part101Version, "2.0")
        self._test_value(info.Part102Version, "2.0")
        self._test_value(info.Part103Version, "not implemented")
        self._test_value(info.DeviceUnitCount, 0)
        self._test_value(info.GearUnitCount, 1)
        self._test_value(info.UnitIndex, 0)

    def test_write(self):
        # Write a new OEM GTIN and see if we can read it back
        self.bus.run_sequence(
            oem.ManufacturerGTIN.write(0, 123123123))
        self._test_value(oem.ManufacturerGTIN, 123123123)
        # Try to write a new gear GTIN and ensure we fail
        self.assertRaises(
            MemoryValueNotWriteable, self.bus.run_sequence,
            info.GTIN.write(0, 123123123))
        # Write a new luminaire identification and read it back
        test_string = "A wizard's staff has a knob on the end"
        self.bus.run_sequence(
            oem.LuminaireIdentification.write(0, test_string))
        self._test_value(oem.LuminaireIdentification, test_string)
        # Write MASK to nominal output and check it reads back correctly
        self.bus.run_sequence(
            oem.LightOutputNominal.write(0, "MASK"))
        self._test_value(oem.LightOutputNominal, FlagValue.MASK)
        # Try to write MASK to a value that does not support it;
        self.assertRaises(
            ValueError, self.bus.run_sequence,
            info.GTIN.write(0, "MASK"))

    def test_write_fail(self):
        # The unit at address 1 uses non-standard lock byte value
        # 0x54 to unlock, so attempts to write to lockable values
        # using the normal 0x55 should fail
        self.assertRaises(
            MemoryLocationNotWriteable, self.bus.run_sequence,
            oem.ManufacturerGTIN.write(1, 123123123))

        # The unit at address 2 always returns 0xaa when writing to
        # memory bank 1 instead of the value written
        self.assertIsNone(self.bus.run_sequence(
            oem.ManufacturerGTIN.write(2, 123123123,
                                       ignore_feedback=True)))
        self.assertRaises(
            ResponseError, self.bus.run_sequence,
            oem.ManufacturerGTIN.write(2, 123123123))

        # The unit at address 2 fails to update DTR0 when writing to
        # memory bank 206
        self.assertRaises(
            MemoryWriteFailure, self.bus.run_sequence,
            diagnostics.LightSourceStartCounterResettable.write(2, 300))


if __name__ == '__main__':
    unittest.main()
