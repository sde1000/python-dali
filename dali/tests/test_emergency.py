from dataclasses import astuple

from dali.frame import BackwardFrame
from dali.gear.emergency import (
    QueryEmergencyFailureStatusResponse,
    QueryEmergencyModeResponse,
    QueryEmergencyStatusResponse,
)
from dali.gear.sequences import (
    EmergencyFeatures,
    EmergencyMode,
    EmergencyStatus,
    QueryEmergencyInformation,
)
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
    assert info.emergency_mode == EmergencyMode(
        rest_mode=False,
        normal_mode=True,
        emergency_mode=False,
        extended_emergency_mode=False,
        function_test=False,
        duration_test=False,
        hardwired_inhibit_active=False,
        hardwired_switch_on=False,
    )
    assert info.emergency_features == EmergencyFeatures(
        integral_emergency_control_gear=True,
        maintained_control_gear=True,
        switched_maintained_control_gear=False,
        auto_test_capability=False,
        adjustable_emergency_level=False,
        hardwired_inhibit_supported=False,
        physical_selection_supported=False,
        relight_in_rest_mode_supported=False,
    )
    assert not any(astuple(info.emergency_failure_status))
    assert info.emergency_status == EmergencyStatus(
        inhibit_mode=False,
        function_test_done_and_result_valid=False,
        duration_test_done_and_result_valid=False,
        battery_fully_charged=True,
        function_test_pending=False,
        duration_test_pending=False,
        identification_active=False,
        physically_selected=False,
    )
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
