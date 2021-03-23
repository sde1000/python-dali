import unittest

from dali.tests import fakes
from dali.memory import diagnostics, energy, maintenance, oem
from dali.memory.location import MemoryBank, MemoryRange, MemoryValue, NumericValue, ScaledNumericValue, \
                                 FixedScaleNumericValue, StringValue, BinaryValue, TemperatureValue, \
                                 ManufacturerSpecificValue, LockableValueMixin, MemoryLocation, MemoryType
from dali.command import Command, Response
from dali.frame import BackwardFrame
from dali.gear.general import DTR0, DTR1, ReadMemoryLocation

# the following MemoryBank will be used for checks on missing memory locations
DUMMY_BANK0 = MemoryBank(0)

class DummyMemoryValue(MemoryValue):

    locations = MemoryRange(DUMMY_BANK0, 3, 7).locations

class DummyNumericValue(NumericValue):

    locations = MemoryRange(DUMMY_BANK0, 8, 12).locations

class DummyScaledNumericValue(ScaledNumericValue):

    locations = MemoryRange(DUMMY_BANK0, 13, 17).locations

class DummyFixedScaleNumericValue(FixedScaleNumericValue):

    locations = MemoryRange(DUMMY_BANK0, 18, 22).locations

class DummyStringValue(StringValue):

    locations = MemoryRange(DUMMY_BANK0, 23, 27).locations

class DummyBinaryValue(BinaryValue):

    locations = MemoryRange(DUMMY_BANK0, 28, 32).locations

class DummyTemperatureValue(TemperatureValue):

    locations = MemoryRange(DUMMY_BANK0, 33, 37).locations

class DummyManufacturerSpecificValue(ManufacturerSpecificValue):

    locations = MemoryRange(DUMMY_BANK0, 38, 42).locations

# the following MemoryBank will be used to check
# - the response for an unlocked MemoryValue,
# - the response for an addressable MemoryValue
DUMMY_BANK1 = MemoryBank(1)

class DummyLateLastMemoryLocation(MemoryValue):

    locations = (MemoryLocation(DUMMY_BANK1, 0, default=20), )

class DummyLockByteWritable(MemoryValue):

    locations = (MemoryLocation(DUMMY_BANK1, 2, default=0x55), )

class DummyUnlockedMemoryValue(MemoryValue, LockableValueMixin):

    locations = MemoryRange(DUMMY_BANK1, 3, 7, type_=MemoryType.NVM_RW_P).locations

class DummyAddressableValue(MemoryValue):

    locations = MemoryRange(DUMMY_BANK1, 11, 15).locations

# the following MemoryBank will be used to check
# - the response for a locked MemoryValue,
# - the response for an unaddressable MemoryValue
DUMMY_BANK2 = MemoryBank(2)

class DummyEarlyLastMemoryLocation(MemoryValue):

    locations = (MemoryLocation(DUMMY_BANK2, 0, default=10), )

class DummyLockByteReadOnly(MemoryValue):

    locations = (MemoryLocation(DUMMY_BANK2, 2, default=0x00), )

class DummyLockedMemoryValue(MemoryValue, LockableValueMixin):

    locations = MemoryRange(DUMMY_BANK2, 3, 7, type_=MemoryType.NVM_RW_P).locations

class DummyUnaddressableValue(MemoryValue):

    locations = MemoryRange(DUMMY_BANK2, 11, 15).locations

class TestMemory(unittest.TestCase):

    def setUp(self):
        self.addr = (1, 2)
        self.bus = fakes.Bus([
            fakes.Gear(self.addr[0]),
            fakes.Gear(self.addr[1], memory_banks=[DUMMY_BANK1, DUMMY_BANK2])
        ])

    def _test_MemoryValue(self, memory_value, default):
        r = self.bus.run_sequence(memory_value.retrieve(self.addr[0]))
        self.assertEqual(r, default)

    def _test_NumericValue(self, memory_value, default=0):
        self._test_MemoryValue(memory_value, default)

    def _test_TemperatureValue(self, memory_value, default=-60):
        self._test_NumericValue(memory_value, default)

    def _test_BinaryValue(self, memory_value, default=False):
        self._test_MemoryValue(memory_value, default)

    def _test_StringValue(self, memory_value, default=''):
        self._test_MemoryValue(memory_value, default)

    def _test_ManufacturerSpecificValue(self, memory_value, default=0):
        self._test_MemoryValue(memory_value, default)

    def test_missingMemoryLocation(self):
        self.assertIsNone(self.bus.run_sequence(DummyMemoryValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyNumericValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyScaledNumericValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyFixedScaleNumericValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyStringValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyBinaryValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyTemperatureValue.retrieve(self.addr[1])))
        self.assertIsNone(self.bus.run_sequence(DummyManufacturerSpecificValue.retrieve(self.addr[1])))

    def test_lockByte(self):
        self.assertFalse(self.bus.run_sequence(DummyUnlockedMemoryValue.is_locked(self.addr[1])))
        self.assertTrue(self.bus.run_sequence(DummyLockedMemoryValue.is_locked(self.addr[1])))

    def test_isAddressable(self):
        self.assertTrue(self.bus.run_sequence(DummyAddressableValue.is_addressable(self.addr[1])))
        self.assertFalse(self.bus.run_sequence(DummyUnaddressableValue.is_addressable(self.addr[1])))

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

        commands = dummy_run_sequence(DummyMemoryValue.retrieve(0))
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

    def test_diagnostics(self):
        self._test_NumericValue(diagnostics.ControlGearOperatingTime)
        self._test_NumericValue(diagnostics.ControlGearStartCounter)
        self._test_NumericValue(diagnostics.ControlGearExternalSupplyVoltage)
        self._test_NumericValue(diagnostics.ControlGearExternalSupplyVoltageFrequency)
        self._test_NumericValue(diagnostics.ControlGearPowerFactor)
        self._test_BinaryValue(diagnostics.ControlGearOverallFailureCondition)
        self._test_NumericValue(diagnostics.ControlGearOverallFailureConditionCounter)
        self._test_BinaryValue(diagnostics.ControlGearExternalSupplyUndervoltage)
        self._test_NumericValue(diagnostics.ControlGearExternalSupplyUndervoltageCounter)
        self._test_BinaryValue(diagnostics.ControlGearExternalSupplyOvervoltage)
        self._test_NumericValue(diagnostics.ControlGearExternalSupplyUndervoltageCounter)
        self._test_BinaryValue(diagnostics.ControlGearExternalSupplyOvervoltage)
        self._test_NumericValue(diagnostics.ControlGearExternalSupplyOvervoltageCounter)
        self._test_BinaryValue(diagnostics.ControlGearOutputPowerLimitation)
        self._test_NumericValue(diagnostics.ControlGearOutputPowerLimitationCounter)
        self._test_BinaryValue(diagnostics.ControlGearThermalDerating)
        self._test_NumericValue(diagnostics.ControlGearThermalDeratingCounter)
        self._test_BinaryValue(diagnostics.ControlGearThermalShutdown)
        self._test_NumericValue(diagnostics.ControlGearThermalShutdownCounter)
        self._test_TemperatureValue(diagnostics.ControlGearTemperature)
        self._test_NumericValue(diagnostics.ControlGearOutputCurrentPercent)
        self._test_NumericValue(diagnostics.LightSourceStartCounterResettable)
        self._test_NumericValue(diagnostics.LightSourceStartCounter)
        self._test_NumericValue(diagnostics.LightSourceOnTimeResettable)
        self._test_NumericValue(diagnostics.LightSourceOnTime)
        self._test_NumericValue(diagnostics.LightSourceVoltage)
        self._test_NumericValue(diagnostics.LightSourceCurrent)
        self._test_BinaryValue(diagnostics.LightSourceOverallFailureCondition)
        self._test_NumericValue(diagnostics.LightSourceOverallFailureConditionCounter)
        self._test_BinaryValue(diagnostics.LightSourceShortCircuit)
        self._test_NumericValue(diagnostics.LightSourceShortCircuitCounter)
        self._test_BinaryValue(diagnostics.LightSourceOpenCircuit)
        self._test_NumericValue(diagnostics.LightSourceOpenCircuitCounter)
        self._test_BinaryValue(diagnostics.LightSourceThermalDerating)
        self._test_NumericValue(diagnostics.LightSourceThermalDeratingCounter)
        self._test_BinaryValue(diagnostics.LightSourceThermalShutdown)
        self._test_NumericValue(diagnostics.LightSourceThermalShutdownCounter)
        self._test_TemperatureValue(diagnostics.LightSourceTemperature)

    def test_energy(self):
        self._test_NumericValue(energy.ActiveEnergy)
        self._test_NumericValue(energy.ActivePower)
        self._test_NumericValue(energy.ApparentEnergy)
        self._test_NumericValue(energy.ApparentPower)
        self._test_NumericValue(energy.ActiveEnergyLoadside)
        self._test_NumericValue(energy.ActivePowerLoadside)

    def test_maintenance(self):
        self._test_NumericValue(maintenance.RatedMedianUsefulLifeOfLuminaire, default=0xff*1000)
        self._test_TemperatureValue(maintenance.InternalControlGearReferenceTemperature, default=0xff-60)
        self._test_NumericValue(maintenance.RatedMedianUsefulLightSourceStarts, default=0xffff*100)
    
    def test_oem(self):
        self._test_MemoryValue(oem.ManufacturerGTIN, default=bytes([0xff,]*6))
        self._test_MemoryValue(oem.LuminaireID, default=bytes([0xff,]*8))
        self._test_NumericValue(oem.ContentFormatID, default=0x03)
        self._test_NumericValue(oem.YearOfManufacture, default=0xff)
        self._test_NumericValue(oem.WeekOfManufacture, default=0xff)
        self._test_NumericValue(oem.InputPowerNominal, default=0xffff)
        self._test_NumericValue(oem.InputPowerMinimumDim, default=0xffff)
        self._test_NumericValue(oem.MainsVoltageMinimum, default=0xffff)
        self._test_NumericValue(oem.MainsVoltageMaximum, default=0xffff)
        self._test_NumericValue(oem.LightOutputNominal, default=0xffffff)
        self._test_NumericValue(oem.CRI, default=0xff)
        self._test_NumericValue(oem.CCT, default=0xffff)
        self._test_MemoryValue(oem.LightDistributionType, default='reserved')
        self._test_StringValue(oem.LuminaireColor)
        self._test_StringValue(oem.LuminaireIdentification)
        self._test_ManufacturerSpecificValue(oem.ManufacturerSpecific, default=bytes([0x00,]*135))

if __name__ == '__main__':
    unittest.main()