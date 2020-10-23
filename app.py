from asyncio.streams import StreamReader, StreamWriter
from dotenv import load_dotenv
import asyncio
import os
import json
import re
from datetime import datetime
import paho.mqtt.client as mqtt
import logging
from typing import Awaitable, Callable, Union


load_dotenv()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    level=logging.DEBUG if os.getenv("LOG_LEVEL") == "DEBUG" else logging.INFO,
)


P1_ADDRESS: str = os.getenv("P1_ADDRESS", "")
obis: list = json.load(open(os.path.join(os.path.dirname(__file__), "obis.json")))[
    "obis_fields"
]
mqtt_client = mqtt.Client()
mqtt_client.connect(os.getenv("MQTT_BROKER"), 1883, 60)
mqtt_client.loop_start()


def calc_crc(telegram: list[bytes]) -> str:
    telegram_str = b"".join(telegram)
    telegram_cut = telegram_str[0 : telegram_str.find(b"!") + 1]
    x = 0
    y = 0
    crc = 0
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


def parse_hex(str) -> str:
    try:
        result = bytes.fromhex(str).decode()
    except ValueError:
        result = str
    return result


async def send_telegram(telegram: list[bytes]) -> None:
    def format_value(value: str, type: str) -> Union[str, float]:
        # Timestamp has message of format "YYMMDDhhmmssX"
        format_functions: dict = {
            "float": lambda str: float(str),
            "int": lambda str: int(str),
            "timestamp": lambda str: int(
                datetime.strptime(str[:-1], "%y%m%d%H%M%S").timestamp()
            ),
            "string": lambda str: parse_hex(str),
            "unknown": lambda str: str,
        }
        return_value = format_functions[type](value.split("*")[0])
        return return_value

    telegram_formatted: dict = {}
    line: str
    for line in [line.decode() for line in telegram]:
        matches: list[[]] = re.findall("(^.*?(?=\\())|((?<=\\().*?(?=\\)))", line)
        if len(matches) > 0:
            obis_key: str = matches[0][0]
            obis_item: Union[dict, None] = next(
                (item for item in obis if item.get("key", "") == obis_key), None
            )
            if obis_item is not None:
                item_type: str = obis_item.get("type", "")
                item_value_position: Union[int, None] = obis_item.get("valuePosition")
                telegram_formatted[obis_item.get("name")] = (
                    format_value(matches[1][1], item_type)
                    if len(matches) == 2
                    else (
                        "|".join(
                            [
                                str(
                                    format_value(
                                        match[1],
                                        item_type[index]
                                        if type(item_type) == list
                                        else item_type,
                                    )
                                )
                                for index, match in enumerate(matches[1:])
                            ]
                        )
                        if item_value_position is None
                        else format_value(
                            matches[2][1],
                            item_type[item_value_position],
                        )
                    )
                )
    try:
        result = mqtt_client.publish(
            os.getenv("MQTT_TOPIC"), payload=json.dumps(telegram_formatted), retain=True
        )
        if result.rc == 0:
            logging.info("Telegram published on MQTT")
        else:
            logging.error(f"Telegram not published (return code {result.rc})")
    except Exception as err:
        logging.error(f"Unable to publish telegram on MQTT: {err}")


async def read_telegram():
    reader: StreamReader
    writer: StreamWriter
    reader, writer = await asyncio.open_connection(P1_ADDRESS, 23)
    telegram: Union[list, None] = None
    iteration_limit: int = 100
    i: int = 0
    while True:
        if i > iteration_limit:
            raise Exception(f"Exceeded iteration limit ({iteration_limit})")
        i = i + 1
        data: bytes = await reader.readline()
        logging.debug(data)
        if data.startswith(b"/"):
            telegram = []
            logging.debug("New telegram")
        if telegram is not None:
            telegram.append(data)
            if data.startswith(b"!"):
                crc: str = hex(int(data[1:], 16))
                calculated_crc: str = calc_crc(telegram)
                if crc == calculated_crc:
                    logging.info(f"CRC verified ({crc})")
                    await send_telegram(telegram)
                else:
                    logging.debug("CRC check failed")
                writer.close()
                await writer.wait_closed()
                break


async def read_p1():
    async def timeout(awaitable: Callable, timeout: int) -> Union[Awaitable, None]:
        try:
            return await asyncio.wait_for(awaitable(), timeout=timeout)
        except Exception as err:
            logging.error(f"Unable to read data from {P1_ADDRESS}: {err}")

    while True:
        await asyncio.gather(
            asyncio.sleep(int(os.getenv("INTERVAL", 5))),
            timeout(read_telegram, timeout=5),
        )


asyncio.run(read_p1())
