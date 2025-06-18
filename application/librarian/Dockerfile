FROM python:3.12-slim

WORKDIR /app

RUN apt update \
    && apt install --yes --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONPATH=/app:/share

CMD ["python", "main.py"]
