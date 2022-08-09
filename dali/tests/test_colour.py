import pytest  # noqa

from dali.frame import BackwardFrame
from dali.gear.colour import (
    AssignedColour,
    QueryAssignedColourResponse,
    QueryColourTypeFeaturesResponse,
    QueryRBGWAFControlResponse,
)


def test_colour_type_features_properties_decoding():
    rsp = QueryColourTypeFeaturesResponse(BackwardFrame(0b10101010))

    # These properties are common for any BitmapResponse
    assert rsp.xy_capable == 0
    assert rsp.Tc_capable == 1
    assert rsp.primary_N_bit_0 == 0
    assert rsp.primary_N_bit_1 == 1
    assert rsp.primary_N_bit_2 == 0
    assert rsp.RGBWAF_channels_bit_0 == 1
    assert rsp.RGBWAF_channels_bit_1 == 0
    assert rsp.RGBWAF_channels_bit_2 == 1

    # These properties are special for QueryColourTypeFeaturesResponse
    assert rsp.primary_n == 2
    assert rsp.RGBWAF_channels == 5


def test_query_assigned_colour_decoding():
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000000))
    assert rsp.value == AssignedColour.not_assigned
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000001))
    assert rsp.value == AssignedColour.red
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000010))
    assert rsp.value == AssignedColour.green
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000011))
    assert rsp.value == AssignedColour.blue
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000100))
    assert rsp.value == AssignedColour.white
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000101))
    assert rsp.value == AssignedColour.amber
    rsp = QueryAssignedColourResponse(BackwardFrame(0b00000110))
    assert rsp.value == AssignedColour.freecolour
    rsp = QueryAssignedColourResponse(BackwardFrame(7))
    assert rsp.value == "(error)"
    rsp = QueryAssignedColourResponse(BackwardFrame(254))
    assert rsp.value == "(error)"
    rsp = QueryAssignedColourResponse(BackwardFrame(255))
    assert rsp.value == "MASK"


def test_query_rgbwaf_control_decoding():
    rsp = QueryRBGWAFControlResponse(BackwardFrame(0b00000000))
    assert not rsp.channel_0_red
    assert rsp.control_type == "channel control"

    rsp = QueryRBGWAFControlResponse(BackwardFrame(0b10000001))
    assert rsp.channel_0_red
    assert rsp.control_type == "normalised colour control"

    rsp = QueryRBGWAFControlResponse(BackwardFrame(0b01000101))
    assert rsp.channel_0_red
    assert not rsp.channel_1_green
    assert rsp.channel_2_blue
    assert rsp.control_type == "colour control"

    rsp = QueryRBGWAFControlResponse(BackwardFrame(0b11000000))
    assert rsp.control_type == "(error)"
