FROM python:3.11.0-slim

RUN pip install poetry==1.2.2
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false --local && \
    poetry install

COPY *.py *.json ./
CMD ["python", "-u", "app.py"]
