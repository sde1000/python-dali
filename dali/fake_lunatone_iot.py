import asyncio
import dali.frame
import dali.gear
import dali.device
from dali.device.helpers import DeviceInstanceTypeMapper
from dali.driver.hid import tridonic
from enum import Enum
import json
import logging
from websockets.server import serve
import websockets.exceptions

"""
Emulate the bare minimum of Lunatone's DALI-2 IoT Gateway over Websocket

Sometimes it's useful to fire up Lunatone's DALI Cockpit, the proprietary
Windows GUI application for addressing, configuring, managing, etc. a DALI
installation. This code implements the bare minimum of their Websocket
protocol, effectively emulating the "Lunatone DALI-2 IoT Gateway". If you
run this code (or integrate the relevant two lines into your existing
building automation system which uses python-dali internally), you can let
the DALI Cockpit access the DALI bus without having to mess with, say,
usb-ip and restarting services.

In the DALI Cockpit, select DALI Bus -> Bus Interface, pick the "Network"
option and in there the "DALI-2 Display/DALI-2 IoT/DALI-2 WLAN", and enter
your device's IP address and port, e.g., 192.0.2.3:8080.
"""

class LunatoneIotProtocolError(RuntimeError):
    pass

class SendingResult(Enum):
    SENT = 0
    ERROR_BUS_VOLTAGE = 1
    ERROR_INITIALIZE = 2
    ERROR_QUIESCENT = 3
    BUFFER_FULL = 4
    NO_SUCH_LINE = 5
    SYNTAX_ERROR = 6
    MACRO_IS_ACTIVE = 7
    COLLISION = 61
    BUS_ERROR = 62
    TIMEOUT = 63
    NO_ANSWER = 100

class AnswerResult(Enum):
    NO_ANSWER = 0
    VALUE_8BIT = 8
    FRAMING_ERROR = 63

def _msg_dali_monitor(line, bits, data, framing_error):
    return {
        "type": "daliMonitor",
        "data": {
            "bits": bits,
            "data": data,
            "line": line,
            "framingError": framing_error,
        },
    }

# The docs mention a ton of other fields, but I'm still getting this thing displayed as a 'DALI-2 Display 7"',
# despite using the IoT-getway's GTIN. I can live with that :).
_INITIAL_GREET = {
    "type": "info",
    "data": {
        "name": "faux-lunatone-iot",
        "errors": {},
        "descriptor": {
            "lines": 1,
            "protocolVersion": "1.0",
        },
        "device": {
            "gtin": 9010342013607, # "Lunatone DALI-2 IoT"
        },
    },
}

_log = logging.getLogger(f'fake-lunatone-iot')

def _unbreak_jsonish(blob: str):
    # Lunatone's DALI-Cockpit sends malformed JSON, with `True` and `False` instead of JSON's own `true` and `false`.
    # This is a huge hack which will corrupt unrelated data, but hey, I *hope* I won't be getting any strings here.
    return blob.replace('True', 'true').replace('False', 'false')

async def frame_result(websocket, line, result: SendingResult):
    _log.debug(f'>> daliFrame {result=}')
    await websocket.send(json.dumps({"type": "daliFrame", "data": {"line": line, "result": result.value}}))

async def dali_answer(websocket, line, result, dali_data):
    if dali_data is None:
        _log.debug(f'WS >> daliAnswer {result=} {dali_data=}')
    else:
        _log.debug(f'WS >> daliAnswer {result=} {dali_data=:02x}')
    await websocket.send(json.dumps({"type": "daliAnswer", "data": {"line": line, "result": result.value, "daliData": dali_data}}))

async def _cleanup_bus_traffic(driver, handle):
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        handle.unregister()

async def emulate(tg, websocket, driver):
    handle = driver.bus_traffic.register(publish_traffic(tg, websocket))
    unregister = tg.create_task(_cleanup_bus_traffic(driver, handle), name='unregister-dali-bus-watcher-to-websocket')
    _log.debug(f'WS >> info')
    try:
        await websocket.send(json.dumps(_INITIAL_GREET))
        async for raw_message in websocket:
            try:
                try:
                    message = json.loads(_unbreak_jsonish(raw_message))
                except json.JSONDecodeError as e:
                    raise LunatoneIotProtocolError(f'Cannot parse JSON: {e}: {raw_message=}')
                if 'type' not in message:
                    raise LunatoneIotProtocolError(f'No "type" field in this JSON packet: {message}')
                if message['type'] == 'filtering':
                    _log.debug(f'WS << NOOP filtering: {message}')
                    # FIXME: do we need to implement this?
                    pass
                elif message['type'] == 'daliFrame':
                    try:
                        bits = message['data']['numberOfBits']
                        payload = message['data']['daliData']
                        line = message['data']['line']
                        sendTwice = message['data']['mode']['sendTwice']
                        priority = message['data']['mode']['priority']
                        waitForAnswer = message['data']['mode']['waitForAnswer']
                    except KeyError as e:
                        raise MissingData(f'{e} for DALI frame: {message}')
                    _log.debug(f'WS << daliFrame ({bits=} {line=} {sendTwice=} {waitForAnswer=}) {" ".join(f"{b:02x}" for b in payload)}')
                    if line != 0:
                        await frame_result(websocket, line, SendingResult.NO_SUCH_LINE)
                        continue

                    if bits not in (8, 16, 24):
                        _log.error(f'{bits=} not supported yet, faking a no-reply')
                        await frame_result(websocket, line, SendingResult.SENT)
                        if waitForAnswer:
                            await dali_answer(websocket, line, AnswerResult.NO_ANSWER, None)
                        continue

                    frame = dali.frame.ForwardFrame(bits, payload)
                    command = dali.command.from_frame(frame)
                    resp = await driver.send(command)
                    # FIXME: error handling
                    await frame_result(websocket, line, SendingResult.SENT)
                    if sendTwice:
                        # As per docs, just send the confirmation twice.
                        # I am lazy, and therefore I ignore the `sendTwice` because the frame parser within python-dali
                        # already does that for me. This might be a bug from the DALI Cockpit's point of view.
                        await frame_result(websocket, line, SendingResult.SENT)
                    if waitForAnswer:
                        if resp is None or resp.raw_value is None:
                            await dali_answer(websocket, line, AnswerResult.NO_ANSWER, None)
                        elif isinstance(resp.raw_value, dali.frame.BackwardFrameError):
                            await dali_answer(websocket, line, AnswerResult.FRAMING_ERROR, None)
                        else:
                            await dali_answer(websocket, line, AnswerResult.VALUE_8BIT, resp.raw_value.as_integer)
                else:
                    raise LunatoneIotProtocolError(f'Unknown "type" field in this JSON packet: {message}')
            except LunatoneIotProtocolError as e:
                _log.error(f'Error: {e}')
                await frame_result(websocket, line, SendingResult.SYNTAX_ERROR)
    except websockets.exceptions.ConnectionClosed as e:
        _log.info(f'WS closed: {e}')
    unregister.cancel()

def publish_traffic(tg, websocket):
    def _traffic_filter(dev, command, response, config_command_error):
        tasks = []
        if config_command_error:
            # FIXME: how to handle this one?
            _log.debug(f'WS >> daliMonitor: FRAMING_ERROR bits={len(command.frame)} {" ".join(f"{b:02x}" for b in command.frame.as_byte_sequence)}')
            tasks.append(websocket.send(json.dumps(
                _msg_dali_monitor(0, len(command.frame), command.frame.as_byte_sequence, framing_error=True))))
        elif command:
            _log.debug(f'WS >> daliMonitor: bits={len(command.frame)} {" ".join(f"{b:02x}" for b in command.frame.as_byte_sequence)}')
            tasks.append(websocket.send(json.dumps(
                _msg_dali_monitor(0, len(command.frame), command.frame.as_byte_sequence, framing_error=False))))
            if response and response.raw_value is not None:
                _log.debug(f'WS >> daliMonitor: bits={len(response.raw_value)} {" ".join(f"{b:02x}" for b in response.raw_value.as_byte_sequence)}')
                tasks.append(websocket.send(json.dumps(
                    _msg_dali_monitor(0, len(response.raw_value), response.raw_value.as_byte_sequence, framing_error=response.raw_value.error))))
        for t in tasks:
            tg.create_task(t, name='publish_traffic')
    return _traffic_filter

def process_request(path, request_headers):
    _log.info(f'WS: {path}')
    if path != '/':
        return (404, [], 'Not found')

async def run_websocket(dev, tg, host, port):
    async with serve(lambda websocket: emulate(tg, websocket, dev), host, port, process_request=process_request):
        await asyncio.Future()

async def main():
    dev_inst_map = DeviceInstanceTypeMapper()
    dev = tridonic("/dev/dali/daliusb-*", glob=True, dev_inst_map=dev_inst_map)
    dev.exceptions_on_send = False
    dev.connect()
    await dev.connected.wait()
    _log.info(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")
    # uncomment the line below to see properly decoded packets from your DALI devices
    # await dev.run_sequence(dev_inst_map.autodiscover())
    _log.info("Listening on websocket...")
    tg = asyncio.TaskGroup()
    async with tg:
        await run_websocket(dev, tg, "0.0.0.0", 8080)
    dev.disconnect()

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
