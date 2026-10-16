import pytest

from dali.frame import BackwardFrame
from dali.gear.general import (
    DAPC,
    Off,
    QueryExtendedFadeTimeResponse,
    QueryGroupsZeroToSevenResponse,
    QueryGroupsEightToFifteenResponse,
)


def test_deprecated_int_address() -> None:
    # Using an int as an address must raise a DeprecationWarning

    with pytest.deprecated_call():
        DAPC(0, 128)  # type: ignore[arg-type]

    with pytest.deprecated_call():
        Off(0)  # type: ignore[arg-type]


def test_query_extended_fade_time_response() -> None:
    rsp = QueryExtendedFadeTimeResponse(BackwardFrame(0b01010101))
    assert rsp.extendedFadeTimeMultiplier == 0b101
    assert rsp.extendedFadeTimeBase == 0b0101


def test_query_groups_zero_to_seven_response() -> None:
    rsp = QueryGroupsZeroToSevenResponse(BackwardFrame(0))
    assert hasattr(rsp, "group0")
    assert hasattr(rsp, "group7")


def test_query_groups_eight_to_fifteen_response() -> None:
    rsp = QueryGroupsEightToFifteenResponse(BackwardFrame(0))
    assert hasattr(rsp, "group8")
    assert hasattr(rsp, "group15")
