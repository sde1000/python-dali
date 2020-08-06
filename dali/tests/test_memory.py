import unittest

from dali.tests import fakes
from dali.memory import diagnostics, energy, maintenance, oem

class TestMemory(unittest.TestCase):

    def setUp(self):
        self.addr = 1
        self.bus = fakes.Bus([fakes.Gear(self.addr)])

    def _test_MemoryValue(self, memory_value, default):
        r = self.bus.run_sequence(memory_value.retrieve(self.addr))
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