FROM python:3.12-slim

WORKDIR /app

RUN apt update \
    && apt install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .

ENV PATH="/root/.local/bin:${PATH}"

RUN pip install --requirements requirements.txt

ENV PYTHONPATH=/app:/share

CMD ["python", "main.py"]
