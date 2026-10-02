from dali.frame import BackwardFrame
from dali.gear.emergency import (
    QueryEmergencyFailureStatusResponse,
    QueryEmergencyModeResponse,
    QueryEmergencyStatusResponse,
)
from dali.gear.sequences import QueryEmergencyInformation
from dali.tests import fakes


def test_emergency_status_decoding():
    rsp = QueryEmergencyStatusResponse(BackwardFrame(0b00001010))
    assert rsp.inhibit_mode == 0
    assert rsp.function_test_done_and_result_valid == 1
    assert rsp.duration_test_done_and_result_valid == 0
    assert rsp.battery_fully_charged == 1
    assert set(rsp.status) == {
        "function test done and result valid",
        "battery fully charged",
    }


def test_emergency_failure_decoding():
    rsp = QueryEmergencyFailureStatusResponse(BackwardFrame(0b00000101))
    assert rsp.circuit_failure == 1
    assert rsp.battery_duration_failure == 0
    assert rsp.battery_failure == 1


def test_emergency_mode_property():
    # Only the "emergency mode" bit set
    rsp = QueryEmergencyModeResponse(BackwardFrame(0b00000100))
    assert rsp.mode == "emergency mode"


def test_query_emergency_information():
    bus = fakes.Bus([fakes.Gear(shortaddr=0, devicetypes=[1])])
    info = bus.run_sequence(QueryEmergencyInformation(0))
    assert info.emergency_mode == 0b00000010
    assert info.emergency_features == 0b00000011
    assert info.emergency_failure_status == 0
    assert info.emergency_status == 0b00001000
    assert info.battery_charge == 254
    assert info.emergency_level == 254
    assert info.duration_test_result == 60
    assert info.lamp_emergency_time == 5
    assert info.lamp_total_operation_time == 100
    assert info.rated_duration == 90


def test_query_emergency_information_mask():
    gear = fakes.Gear(shortaddr=0, devicetypes=[1])
    gear.battery_charge = 255  # MASK
    bus = fakes.Bus([gear])
    info = bus.run_sequence(QueryEmergencyInformation(0))
    assert info.battery_charge is None
