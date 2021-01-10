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
    await process_lines(reader)


@pytest.mark.asyncio
async def test_readlines_corrupt_p1():
    with pytest.raises(Exception, match="CRC check failed"):
        await read_lines("./tests/lines_corrupt.txt")


@pytest.mark.asyncio
async def test_readlines_ok_p1():
    await read_lines("./tests/lines_ok.txt")
