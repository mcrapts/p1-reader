FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY *.py *.json ./
CMD ["uv", "run", "python", "-m", "app"]
