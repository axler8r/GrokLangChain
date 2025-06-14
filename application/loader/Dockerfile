FROM python:3.11-slim

WORKDIR /app

RUN apt update \
    && apt install --yes --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fLsS https://astral.sh/uv/install.sh | sh

COPY . .

ENV PATH="/root/.local/bin:${PATH}"

RUN uv sync

ENV PYTHONPATH=/app:/share

CMD ["python", "main.py"]
