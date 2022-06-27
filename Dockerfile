FROM python:3.10

RUN pip install poetry==1.1.13
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false --local && \
    poetry install

COPY *.py *.json ./
CMD ["python", "-u", "app.py"]
