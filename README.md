# TL;DR
Dit project is een Python-script die een P1-reader aangesloten op het netwerk uitleest middels TCP, de berichten interpreteert, omzet naar JSON en publiceert op MQTT. Door deze applicatie te draaien heb je de berichten van je slimme meter binnen een handomdraai in leesbaar en bruikbaar JSON-formaat beschikbaar op MQTT.

# Gebruik
Het script kan zowel via Python als Docker uitgevoerd worden:
## Script starten middels Python
1. Installeer `poetry`: https://python-poetry.org/docs/#installation
2. Voer het commando `poetry install` uit in de root van dit project
3. Voer `poetry install` uit om alle dependencies te installeren
4. Start het script middels `poetry run python app.py`

## Script starten midels Docker
1. Zorg dat je Docker geinstalleerd hebt: https://docs.docker.com/get-docker/
2. Build de container met `docker build -t p1-reader .`
3. Start de container met `docker run --env-file ./.env --name -d p1-reader p1-reader`