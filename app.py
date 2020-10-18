from dotenv import load_dotenv
import asyncio
import os
import json
import re
from datetime import datetime
from influxdb import InfluxDBClient


load_dotenv()


P1_ADDRESS = os.getenv("P1_ADDRESS")
obis: list = json.load(open(os.path.join(os.path.dirname(__file__), "obis.json")))[
    "obis_fields"
]
influxdb_client = InfluxDBClient(
    host=os.getenv("INFLUXDB_HOST"),
    port=443,
    ssl=os.getenv("INFLUXDB_SSL") == "1",
    verify_ssl=False,
)


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


def parse_hex(str):
    try:
        result = bytes.fromhex(str).decode()
    except ValueError:
        result = str
    return result


def send_telegram(telegram: list[bytes]):
    def format_value(value, type):
        # Timestamp has message of format "YYMMDDhhmmssX"
        format_functions = {
            "float": lambda str: float(str),
            "int": lambda str: int(str),
            "timestamp": lambda str: int(
                datetime.strptime(str[:-1], "%y%m%d%H%M%S").timestamp()
            ),
            "string": lambda str: parse_hex(str),
        }
        value = format_functions[type](value.split("*")[0])
        return value

    telegram_formatted = {}
    for line in [line.decode() for line in telegram]:
        matches = re.findall("(^.*?(?=\\())|((?<=\\().*?(?=\\)))", line)
        if len(matches) > 0:
            obis_key = matches[0][0]
            obis_item = next((item for item in obis if item["key"] == obis_key), None)
            if obis_item is not None:
                telegram_formatted[obis_item["name"]] = (
                    format_value(matches[1][1], obis_item["type"])
                    if len(matches) == 2
                    else "|".join(
                        [
                            str(
                                format_value(
                                    match[1],
                                    obis_item["type"][index]
                                    if type(obis_item["type"]) == list
                                    else obis_item["type"],
                                )
                            )
                            for index, match in enumerate(matches[1:])
                        ]
                    )
                )
    influxdb_body = [
        {
            "measurement": "p1",
            "fields": telegram_formatted,
            "time": int(datetime.now().timestamp()),
        }
    ]
    try:
        influxdb_client.write_points(
            points=influxdb_body,
            database=os.getenv("INFLUXDB_DATABASE"),
            time_precision="s",
            protocol="json"
        )
    except Exception as err:
        print(f"Unable to send data to InfluxDB: {err}")


async def read_p1_tcp():
    reader, _ = await asyncio.open_connection(P1_ADDRESS, 23)
    telegram = []
    while True:
        try:
            data = await reader.readline()
            line = data.decode("utf-8")
            if line.startswith("/"):
                telegram = []
            telegram.append(data)
            if line.startswith("!"):
                crc = hex(int(line[1:], 16))
                calculated_crc = calc_crc(telegram)
                if crc == calculated_crc:
                    # print("crc valid!!! do something")
                    send_telegram(telegram)
                    # import sys
                    # sys.exit()
        except Exception:
            print(f"Unable to read data from {P1_ADDRESS}")
            await asyncio.sleep(5)


asyncio.run(read_p1_tcp())
