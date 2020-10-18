import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


P1_ADDRESS = os.getenv("P1_ADDRESS")


def calc_crc(telegram: list[bytes]):
    telegram_str = b"".join(telegram)
    telegram_cut = telegram_str[0 : telegram_str.find(b"!") + 1]
    x = 0
    y = 0
    crc = 0
    # print "Lengte telegram",len(telegram)
    while x < len(telegram_cut):
        crc = crc ^ telegram_cut[x]
        x = x + 1
        y = 0
        while y < 8:
            if (crc & 1) != 0:
                crc = crc >> 1
                crc = crc ^ (int("0xA001", 16))
            else:
                crc = crc >> 1
            y = y + 1
    return hex(crc)


async def read_p1_tcp():
    reader, _ = await asyncio.open_connection(P1_ADDRESS, 23)
    telegram = []
    while True:
        data = await reader.readline()
        line = data.decode("utf-8")
        if line.startswith("/"):
            telegram = []
        telegram.append(data)
        if line.startswith("!"):
            crc = hex(int(line[1:], 16))
            calculated_crc = calc_crc(telegram)
            if(crc == calculated_crc):
                print('crc valid!!! do something')


asyncio.run(read_p1_tcp())
