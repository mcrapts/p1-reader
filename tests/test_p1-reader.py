from unittest import mock

import aiomqtt
import pytest

from app import calc_crc, convert_telegram_to_dict, process_lines, publish_telegram


def test_calc_crc():
    with open("./tests/telegram.txt", "rb") as f:
        telegram = f.readlines()
    crc = calc_crc(telegram)
    assert crc == "0x1058"


class Reader:
    def __init__(self, lines):
        self.lines = iter(lines)

    async def readline(self):
        return next(self.lines)


@pytest.fixture
def mock_open_connection(request):
    filename = request.param
    with open(filename, "rb") as f:
        lines = f.readlines()
    reader = Reader(lines)
    writer = mock.Mock()
    writer.close = mock.Mock()
    writer.wait_closed = mock.AsyncMock()

    async def open_connection(host, port):
        return (reader, writer)

    return (open_connection, reader, writer)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_open_connection", ["./tests/lines_corrupt.txt"], indirect=True
)
async def test_readlines_corrupt_p1(monkeypatch, mock_open_connection):
    open_connection, reader, writer = mock_open_connection
    monkeypatch.setattr("asyncio.open_connection", open_connection)
    with pytest.raises(Exception, match="CRC check failed"):
        await process_lines()

    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_open_connection", ["./tests/lines_ok.txt"], indirect=True
)
async def test_readlines_ok_p1(monkeypatch, mock_open_connection):
    open_connection, reader, writer = mock_open_connection

    monkeypatch.setattr("asyncio.open_connection", open_connection)
    telegram_bytes = await process_lines()
    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited()

    expected_telegram_bytes = telegram_bytes = [
        b"/XMX5LGF0010453336756\r\n",
        b"\r\n",
        b"1-3:0.2.8(50)\r\n",
        b"0-0:1.0.0(210110165213W)\r\n",
        b"0-0:96.1.1(4530303132333435363738363735363139)\r\n",
        b"1-0:1.8.1(001390.529*kWh)\r\n",
        b"1-0:1.8.2(001083.563*kWh)\r\n",
        b"1-0:2.8.1(000502.043*kWh)\r\n",
        b"1-0:2.8.2(001072.631*kWh)\r\n",
        b"0-0:96.14.0(0001)\r\n",
        b"1-0:1.7.0(00.375*kW)\r\n",
        b"1-0:2.7.0(00.000*kW)\r\n",
        b"0-0:96.7.21(00015)\r\n",
        b"0-0:96.7.9(00007)\r\n",
        b"1-0:99.97.0(4)(0-0:96.7.19)(000101010000W)(0000000426*s)(000101010000W)(0000098573*s)(000101010000W)(0000000559*s)(200127202136W)(0000000328*s)\r\n",
        b"1-0:32.32.0(00017)\r\n",
        b"1-0:52.32.0(00016)\r\n",
        b"1-0:72.32.0(00024)\r\n",
        b"1-0:32.36.0(00000)\r\n",
        b"1-0:52.36.0(00000)\r\n",
        b"1-0:72.36.0(00000)\r\n",
        b"0-0:96.13.0()\r\n",
        b"1-0:32.7.0(230.3*V)\r\n",
        b"1-0:52.7.0(228.0*V)\r\n",
        b"1-0:72.7.0(229.7*V)\r\n",
        b"1-0:31.7.0(000*A)\r\n",
        b"1-0:51.7.0(000*A)\r\n",
        b"1-0:71.7.0(001*A)\r\n",
        b"1-0:21.7.0(00.100*kW)\r\n",
        b"1-0:41.7.0(00.125*kW)\r\n",
        b"1-0:61.7.0(00.149*kW)\r\n",
        b"1-0:22.7.0(00.000*kW)\r\n",
        b"1-0:42.7.0(00.000*kW)\r\n",
        b"1-0:62.7.0(00.000*kW)\r\n",
        b"0-1:24.1.0(003)\r\n",
        b"0-1:96.1.0(4730303132333435363738313736323139)\r\n",
        b"0-1:24.2.1(210110165007W)(01319.046*m3)\r\n",
        b"!2E85\r\n",
    ]
    assert telegram_bytes == expected_telegram_bytes


@pytest.mark.asyncio
async def test_telegram_bytes_to_dict():
    telegram_bytes = [
        b"/XMX5LGF0010453336756\r\n",
        b"\r\n",
        b"1-3:0.2.8(50)\r\n",
        b"0-0:1.0.0(210110165213W)\r\n",
        b"0-0:96.1.1(4530303132333435363738363735363139)\r\n",
        b"1-0:1.8.1(001390.529*kWh)\r\n",
        b"1-0:1.8.2(001083.563*kWh)\r\n",
        b"1-0:2.8.1(000502.043*kWh)\r\n",
        b"1-0:2.8.2(001072.631*kWh)\r\n",
        b"0-0:96.14.0(0001)\r\n",
        b"1-0:1.7.0(00.375*kW)\r\n",
        b"1-0:2.7.0(00.000*kW)\r\n",
        b"0-0:96.7.21(00015)\r\n",
        b"0-0:96.7.9(00007)\r\n",
        b"1-0:99.97.0(4)(0-0:96.7.19)(000101010000W)(0000000426*s)(000101010000W)(0000098573*s)(000101010000W)(0000000559*s)(200127202136W)(0000000328*s)\r\n",
        b"1-0:32.32.0(00017)\r\n",
        b"1-0:52.32.0(00016)\r\n",
        b"1-0:72.32.0(00024)\r\n",
        b"1-0:32.36.0(00000)\r\n",
        b"1-0:52.36.0(00000)\r\n",
        b"1-0:72.36.0(00000)\r\n",
        b"0-0:96.13.0()\r\n",
        b"1-0:32.7.0(230.3*V)\r\n",
        b"1-0:52.7.0(228.0*V)\r\n",
        b"1-0:72.7.0(229.7*V)\r\n",
        b"1-0:31.7.0(000*A)\r\n",
        b"1-0:51.7.0(000*A)\r\n",
        b"1-0:71.7.0(001*A)\r\n",
        b"1-0:21.7.0(00.100*kW)\r\n",
        b"1-0:41.7.0(00.125*kW)\r\n",
        b"1-0:61.7.0(00.149*kW)\r\n",
        b"1-0:22.7.0(00.000*kW)\r\n",
        b"1-0:42.7.0(00.000*kW)\r\n",
        b"1-0:62.7.0(00.000*kW)\r\n",
        b"0-1:24.1.0(003)\r\n",
        b"0-1:96.1.0(4730303132333435363738313736323139)\r\n",
        b"0-1:24.2.1(210110165007W)(01319.046*m3)\r\n",
        b"!2E85\r\n",
    ]
    telegram_dict = convert_telegram_to_dict(telegram_bytes)
    expected_telegram_dict = {
        "versionInformation": 50,
        "timestamp": 1610293933,
        "equipmentIdentifier": "E0012345678675619",
        "electricityDeliveredT1": 1390.529,
        "electricityDeliveredT2": 1083.563,
        "electricitySuppliedT1": 502.043,
        "electricitySuppliedT2": 1072.631,
        "tariffIndicator": 1,
        "electricityDeliveredActual": 0.375,
        "electricitySuppliedActual": 0.0,
        "powerFailures": 15,
        "powerFailuresLong": 7,
        "powerFailureEventLog": "4|0-0:96.7.19|000101010000W|0000000426|000101010000W|0000098573|000101010000W|0000000559|200127202136W|0000000328",
        "voltageSagsL1": 17.0,
        "voltageSagsL2": 16.0,
        "voltageSagsL3": 24.0,
        "voltageSwellsL1": 0.0,
        "voltageSwellsL2": 0.0,
        "voltageSwellsL3": 0.0,
        "textMessage": "",
        "instantaneousVoltageL1": 230.3,
        "instantaneousVoltageL2": 228.0,
        "instantaneousVoltageL3": 229.7,
        "instantaneousCurrentL1": 0.0,
        "instantaneousCurrentL2": 0.0,
        "instantaneousCurrentL3": 1.0,
        "instantaneousActivePowerL1Plus": 0.1,
        "instantaneousActivePowerL2Plus": 0.125,
        "instantaneousActivePowerL3Plus": 0.149,
        "instantaneousActivePowerL1Min": 0.0,
        "instantaneousActivePowerL2Min": 0.0,
        "instantaneousActivePowerL3Min": 0.0,
        "deviceType1": "003",
        "equipmentIdentifier1": "G0012345678176219",
        "deviceValue1": 1319.046,
    }
    assert telegram_dict == expected_telegram_dict


@pytest.mark.asyncio
@pytest.mark.parametrize("raise_exception", [True, False])
async def test_publish_telegram(raise_exception):
    MockMqttClient = mock.create_autospec(aiomqtt.Client, spec_set=True)
    mock_mqtt_client = MockMqttClient("test_broker.home")
    mock_mqtt_client.publish = mock.AsyncMock(
        side_effect=Exception if raise_exception else None
    )

    mock_telegram_dict = {
        "versionInformation": 50,
        "timestamp": 1610293933,
        "equipmentIdentifier": "E0012345678675619",
    }

    await publish_telegram(mock_telegram_dict, mock_mqtt_client)
    mock_mqtt_client.publish.assert_called_once()
