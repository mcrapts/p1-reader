import asyncio
import json
import logging
import os
import re
from asyncio.streams import StreamReader, StreamWriter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable

import aiomqtt
from dotenv import load_dotenv

load_dotenv()


class Config:
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "")
    P1_ADDRESS = os.getenv("P1_ADDRESS", "")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "")
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "")
    INTERVAL: int = int(os.getenv("INTERVAL", 5))


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    level=logging.DEBUG if Config.LOG_LEVEL == "DEBUG" else logging.INFO,
)


@dataclass
class ObisField:
    key: str
    name: str
    type: list | str
    value_position: Any

    def __post_init__(self):
        self.type = [self.type] if isinstance(self.type, str) else self.type


obis_fields: list[ObisField] = [
    ObisField(
        key=field.get("key", ""),
        name=field.get("name", ""),
        type=field.get("type", ""),
        value_position=field.get("valuePosition"),
    )
    for field in json.load(open(os.path.join(os.path.dirname(__file__), "obis.json")))[
        "obis_fields"
    ]
]


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


def convert_telegram_to_dict(telegram: list[bytes] | None):
    def format_value(value: str, field_type: str) -> str | float:
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
        result = format_functions[field_type](value.split("*")[0])
        return result

    telegram_formatted: dict = {}
    line: str

    telegram = telegram if telegram else []
    for line in [line.decode() for line in telegram]:
        matches: list[list] = re.findall("(^.*?(?=\\())|((?<=\\().*?(?=\\)))", line)
        if len(matches) > 0:
            obis_key: str = matches[0][0]
            obis_field: ObisField | None = next(
                (field for field in obis_fields if field.key == obis_key), None
            )
            if obis_field is not None:
                telegram_formatted[obis_field.name] = (
                    [
                        format_value(
                            match[1],
                            (
                                obis_field.type[index]
                                if len(obis_field.type) > 1
                                else obis_field.type[0]
                            ),
                        )
                        for index, match in enumerate(matches[1:])
                    ]
                    if obis_field.value_position is None
                    else [
                        format_value(
                            matches[2][1],
                            obis_field.type[obis_field.value_position],
                        )
                    ]
                )
    telegram_formatted = {
        key: "|".join(value) if isinstance(value, list) and len(value) > 1 else value[0]
        for (key, value) in telegram_formatted.items()
    }
    return telegram_formatted


async def publish_telegram(
    telegram_formatted: dict, mqtt_client: aiomqtt.Client
) -> dict | None:
    try:
        await mqtt_client.publish(
            Config.MQTT_TOPIC,
            payload=json.dumps(telegram_formatted),
            retain=True,
        )
        logging.info("Telegram published on MQTT")
    except Exception as err:
        logging.error(f"Unable to publish telegram on MQTT: {err}")


async def process_lines(reader) -> list[bytes] | None:
    telegram: list[bytes] | None = None
    iteration_limit: int = 10
    i: int = 0

    while True:
        if i > iteration_limit:
            raise Exception(f"Exceeded iteration limit: {iteration_limit} iteration(s)")
        data: bytes = await reader.readline()
        logging.debug(data)

        if data.startswith(b"/"):
            telegram = []
            i = i + 1
            logging.debug("New telegram")
        if telegram is not None and data is not None:
            telegram.append(data)
            if data.startswith(b"!"):
                crc: str = hex(int(data[1:], 16))
                calculated_crc: str = calc_crc(telegram)
                if crc == calculated_crc:
                    logging.info(f"CRC verified ({crc}) after {i} iteration(s)")
                    return telegram
                else:
                    raise Exception("CRC check failed")


async def read_p1_and_publish_telegram():
    reader: StreamReader
    writer: StreamWriter
    reader, writer = await asyncio.open_connection(Config.P1_ADDRESS, 23)

    try:
        telegram_bytes = await process_lines(reader)
        telegram_dict = convert_telegram_to_dict(telegram_bytes)
        async with aiomqtt.Client(Config.MQTT_BROKER, 1883) as mqtt_client:
            await publish_telegram(telegram_dict, mqtt_client)
    except Exception as err:
        logging.debug(err)
    finally:
        writer.close()


async def read_p1():
    async def timeout(awaitable: Callable, timeout: float) -> Awaitable | None:
        try:
            return await asyncio.wait_for(awaitable(), timeout=timeout)
        except Exception as err:
            logging.error(
                f"Unable to read data from {Config.P1_ADDRESS}: {str(err) or err.__class__.__name__}"
            )

    while True:
        logging.info("Read P1 reader")
        await asyncio.gather(
            asyncio.sleep(Config.INTERVAL),
            timeout(read_p1_and_publish_telegram, timeout=10),
        )


if __name__ == "__main__":
    asyncio.run(read_p1())
