import pytest
from app import calc_crc, process_lines


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


async def read_lines(filename):
    with open(filename, "rb") as f:
        lines = f.readlines()
    reader = Reader(lines)
    return await process_lines(reader)


@pytest.mark.asyncio
async def test_readlines_corrupt_p1():
    with pytest.raises(Exception, match="CRC check failed"):
        await read_lines("./tests/lines_corrupt.txt")


@pytest.mark.asyncio
async def test_readlines_ok_p1():
    result = await read_lines("./tests/lines_ok.txt")
    expected_result = {
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
    assert result == expected_result
