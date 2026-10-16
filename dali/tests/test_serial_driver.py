import asyncio
from functools import reduce
import logging
from operator import xor
from unittest.mock import AsyncMock, MagicMock

import pytest

from dali.address import DeviceShort, GearShort, InstanceNumber
from dali.command import NumericResponse
from dali.device.general import QueryInstanceType
from dali.driver.serial import _DALI_FRAMING_ERROR, DriverLubaRs232
from dali.gear.general import QueryActualLevel


@pytest.mark.asyncio
async def test_timed_out_query_reports_missing_value():
    """A query that times out must return the command's own response type.

    A bare Response(None) passes check_bad_rsp while its value is None, which
    leaked into control-device autodiscovery and crashed on int(None).
    """
    driver = DriverLubaRs232("luba232:/dev/ttyACM0")
    driver._connected.set()
    protocol = MagicMock()
    protocol.reset_dali_response = MagicMock()
    protocol.send_dali_command = AsyncMock()
    protocol.wait_dali_raw_response = AsyncMock(side_effect=asyncio.TimeoutError)
    driver._protocol = protocol

    response = await driver.send(
        QueryInstanceType(device=DeviceShort(0), instance=InstanceNumber(0))
    )

    assert isinstance(response, NumericResponse)
    assert response.value == "(missing)"


@pytest.mark.asyncio
async def test_reset_dali_response_drains_all_without_critical(caplog):
    """Stale buffered responses must all be cleared and not logged as CRITICAL.

    A late backward frame that missed its query is routine on a busy bus; the
    old code discarded only one item and logged it at CRITICAL, spamming logs.
    """
    protocol = DriverLubaRs232.LubaProtocol()
    protocol._queue_rx_raw_dali.put_nowait(6)
    protocol._queue_rx_raw_dali.put_nowait(7)
    protocol._queue_rx_raw_dali.put_nowait(8)

    with caplog.at_level(logging.DEBUG, logger="dali.driver"):
        protocol.reset_dali_response()

    assert protocol._queue_rx_raw_dali.empty()
    assert not [r for r in caplog.records if r.levelno >= logging.CRITICAL]
    assert any("discarded 3 stale" in r.getMessage() for r in caplog.records)


def _connecting_driver(monkeypatch, info_side_effect):
    """Return a driver whose transport is faked and handshake is scripted."""
    driver = DriverLubaRs232("luba232:/dev/ttyACM0")
    protocol = MagicMock()
    connected = asyncio.Event()
    connected.set()
    protocol.connected = connected
    protocol.send_device_info_query = AsyncMock(side_effect=info_side_effect)
    protocol.send_device_settings = AsyncMock()
    protocol.reset_luba_response = MagicMock()
    monkeypatch.setattr(
        "dali.driver.serial.serialx.create_serial_connection",
        AsyncMock(return_value=(MagicMock(), protocol)),
    )
    return driver, protocol


@pytest.mark.asyncio
async def test_connect_retries_handshake_on_timeout(monkeypatch):
    """A busy bus can time out the first handshake frames; connect must retry.

    The interface is slow to acknowledge the info/settings exchange while a
    device streams events, so a single timeout should not fail the connect.
    """
    driver, protocol = _connecting_driver(
        monkeypatch, [asyncio.TimeoutError, asyncio.TimeoutError, None]
    )

    await driver.connect()

    assert driver.is_connected
    assert protocol.send_device_info_query.await_count == 3
    assert protocol.send_device_settings.await_count == 1
    assert protocol.reset_luba_response.call_count == 2


@pytest.mark.asyncio
async def test_connect_without_applying_settings_leaves_hardware_untouched(
    monkeypatch,
):
    """connect(apply_settings=False) must not write the device settings.

    A read-only probe of a discovered interface must not overwrite the
    hardware configuration, otherwise it could depower a bus the integrated
    supply is already driving.
    """
    driver, protocol = _connecting_driver(monkeypatch, [None])

    await driver.connect(apply_settings=False)

    assert driver.is_connected
    assert protocol.send_device_info_query.await_count == 1
    assert protocol.send_device_settings.await_count == 0


@pytest.mark.asyncio
async def test_connect_raises_after_exhausting_handshake_attempts(monkeypatch):
    """When every handshake attempt times out, connect must give up and raise."""
    driver, protocol = _connecting_driver(monkeypatch, asyncio.TimeoutError)

    with pytest.raises(asyncio.TimeoutError):
        await driver.connect()

    assert not driver.is_connected
    attempts = DriverLubaRs232.handshake_attempts
    assert protocol.send_device_info_query.await_count == attempts
    assert protocol.reset_luba_response.call_count == attempts - 1


@pytest.mark.asyncio
async def test_lost_transport_is_reported_as_disconnected(monkeypatch):
    """An interface that goes away must stop claiming to be connected.

    The driver's own event only records that the handshake once succeeded, so
    an unplugged USB interface still looked connected and every frame ran into
    its transmit timeout instead of failing fast.
    """
    driver, protocol = _connecting_driver(monkeypatch, [None])
    await driver.connect()
    assert driver.is_connected

    # What LubaProtocol.connection_lost() does when the port disappears
    protocol.connected.clear()

    assert not driver.is_connected


@pytest.mark.asyncio
async def test_connect_reopens_the_port_after_a_lost_transport(monkeypatch):
    """Once the interface is back, connect() must open the port again."""
    driver, protocol = _connecting_driver(monkeypatch, [None])
    await driver.connect()
    protocol.connected.clear()

    replacement = MagicMock()
    connected = asyncio.Event()
    connected.set()
    replacement.connected = connected
    replacement.send_device_info_query = AsyncMock()
    replacement.send_device_settings = AsyncMock()
    monkeypatch.setattr(
        "dali.driver.serial.serialx.create_serial_connection",
        AsyncMock(return_value=(MagicMock(), replacement)),
    )

    await driver.connect()

    assert driver.is_connected
    assert driver._protocol is replacement


@pytest.mark.asyncio
async def test_send_dali_command_resyncs_after_stale_confirmation(caplog):
    """A stale confirmation must not desync every following transmission.

    A weak bus can let a send's confirmation arrive after it timed out; the
    next send then finds that stale confirmation queued ahead of its own. It
    must be discarded and the matching one awaited, so the stream recovers
    instead of every later frame inheriting the one-off mismatch.
    """
    protocol = DriverLubaRs232.LubaProtocol()
    protocol.transport = MagicMock()
    protocol.rx_idle.set()

    command = QueryActualLevel(GearShort(0))
    stale = QueryActualLevel(GearShort(1))
    protocol._queue_tx_conf.put_nowait(
        protocol.LubaMsgTxConf(tx_id=1, message=stale)
    )
    protocol._queue_tx_conf.put_nowait(
        protocol.LubaMsgTxConf(tx_id=2, message=command)
    )

    with caplog.at_level(logging.WARNING, logger="dali.driver"):
        await protocol.send_dali_command(command)

    assert protocol._queue_tx_conf.empty()
    assert any("stale LUBA confirmation" in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_reset_luba_response_drains_all(caplog):
    """Stale LUBA command replies must be cleared before a handshake retry."""
    protocol = DriverLubaRs232.LubaProtocol()
    protocol._queue_rx_luba_cmd.put_nowait("stale-1")
    protocol._queue_rx_luba_cmd.put_nowait("stale-2")

    protocol.reset_luba_response()

    assert protocol._queue_rx_luba_cmd.empty()


def _luba_framing_error_event():
    """Build a LUBA 'DALI frame received' event reporting a framing error."""
    payload = [
        0x00, 0x01,          # Time tick
        0x00,                # DALI line
        (2 << 6) | 63,       # Event type 2, event info 63 (framing error)
    ]
    body = [
        DriverLubaRs232.LubaCmd.EVENT_MESSAGE.value,
        len(payload),
        *payload,
    ]
    return bytes([0x59, *body, reduce(xor, body)])


@pytest.mark.asyncio
async def test_framing_error_event_is_queued():
    """A framing-error event must be surfaced on the raw response queue."""
    protocol = DriverLubaRs232.LubaProtocol()

    protocol.data_received(_luba_framing_error_event())

    raw = await asyncio.wait_for(protocol._queue_rx_raw_dali.get(), timeout=1)
    assert raw is _DALI_FRAMING_ERROR


@pytest.mark.asyncio
async def test_framing_error_query_returns_error_response():
    """A query that hits a framing error must report it, not time out silently.

    Several gear answering at once (a short-address collision) garble the
    backward frame; the response must carry the error so callers can tell it
    apart from an address that did not answer.
    """
    driver = DriverLubaRs232("luba232:/dev/ttyACM0")
    driver._connected.set()
    protocol = MagicMock()
    protocol.reset_dali_response = MagicMock()
    protocol.send_dali_command = AsyncMock()
    protocol.wait_dali_raw_response = AsyncMock(return_value=_DALI_FRAMING_ERROR)
    driver._protocol = protocol

    response = await driver.send(
        QueryInstanceType(device=DeviceShort(0), instance=InstanceNumber(0))
    )

    assert response.raw_value is not None
    assert response.raw_value.error is True
