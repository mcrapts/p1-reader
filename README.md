# English
## TL;DR
This project contains a Python script to read a network connected P1 reader using TCP. The messages are interpreted, transformed to JSON and published on MQTT. This application makes it straightforward to have messages from your meter available in a readable JSON format on MQTT. 

## Usage
The script can be executed using Python and Docker.

> Before you start, rename `.env.example` to `.env` and make sure to fill in the variables.

### Start script using Python
1. Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
3. Start the script using `uv run python -m app`
4. Optional: run tests using `uv run pytest`

### Start script using Docker
1. Ensure you have Docker installed: https://docs.docker.com/get-docker/
2. Build container using  `docker build -t p1-reader .`
3. Start container using  `docker run --env-file ./.env --name p1-reader -d p1-reader`
---
# Nederlands
## TL;DR
Dit project is een Python-script die een P1-reader aangesloten op het netwerk uitleest middels TCP, de berichten interpreteert, omzet naar JSON en publiceert op MQTT. Door deze applicatie te draaien heb je de berichten van je slimme meter binnen een handomdraai in leesbaar en bruikbaar JSON-formaat beschikbaar op MQTT.

## Gebruik
Het script kan zowel via Python als Docker uitgevoerd worden.

> Hernoem `.env.example` to `.env` en zorg dat alle variables ingevuld zijn.

### Script starten middels Python
1. Installeer `uv`: https://docs.astral.sh/uv/getting-started/installation/
3. Start het script middels `uv run python -m app`
4. Optioneel: voer tests uit met `uv run pytest`

### Script starten midels Docker
1. Zorg dat je Docker geinstalleerd hebt: https://docs.docker.com/get-docker/
2. Build de container met `docker build -t p1-reader .`
3. Start de container met `docker run --env-file ./.env --name p1-reader -d p1-reader`
