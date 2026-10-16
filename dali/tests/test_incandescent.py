from dali.frame import BackwardFrame
from dali.gear.incandescent import (
    DimmerTemperatureResponse,
    VoltageResponse,
    FrequencyResponse,
    LoadCurrentPctResponse,
    LoadCurrentRatingResponse,
)
from dali.gear.sequences import QueryIncandescentRealLoadPower
from dali.address import GearShort
from dali.tests import fakes


def test_dimmer_temperature_response() -> None:
    rsp = DimmerTemperatureResponse(BackwardFrame(40))
    assert rsp.value == 0
    rsp = DimmerTemperatureResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_voltage_response() -> None:
    rsp = VoltageResponse(BackwardFrame(100))
    assert rsp.value == 200
    rsp = VoltageResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_frequency_response() -> None:
    rsp = FrequencyResponse(BackwardFrame(101))
    assert rsp.value == 50.5
    rsp = FrequencyResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_load_current_pct_response() -> None:
    rsp = LoadCurrentPctResponse(BackwardFrame(101))
    assert rsp.value == 50.5
    rsp = LoadCurrentPctResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_load_current_rating_response() -> None:
    rsp = LoadCurrentRatingResponse(BackwardFrame(254))
    assert rsp.value == 38.1
    rsp = LoadCurrentRatingResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_real_load_power_sequence() -> None:
    gear = fakes.Gear(shortaddr=0)
    bus = fakes.Bus([gear])
    assert bus.run_sequence(QueryIncandescentRealLoadPower(
        GearShort(0))) is None
    gear = fakes.Gear(shortaddr=0, devicetypes=[4])
    gear.real_load_power = 200.0
    bus = fakes.Bus([gear])
    assert bus.run_sequence(QueryIncandescentRealLoadPower(
        GearShort(0))) == gear.real_load_power
    gear.real_load_power = None
    assert bus.run_sequence(QueryIncandescentRealLoadPower(
        GearShort(0))) == "MASK"
