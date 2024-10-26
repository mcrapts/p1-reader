FROM python:3.13.0-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY *.py *.json ./
CMD ["uv", "run", "python", "-m", "app"]
