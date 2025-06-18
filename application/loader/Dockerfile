FROM python:3.12-slim

WORKDIR /app

RUN apt update \
    && apt install --yes --no-install-recommends \
        curl \
        cron \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fLsS https://astral.sh/uv/install.sh | sh

COPY . .

ENV PATH="/root/.local/bin:${PATH}"

RUN uv sync

ENV PYTHONPATH=/app:/share

# Create a cron job to run the loader weekly (every Sunday at 2 AM)
RUN echo "0 2 * * 0 cd /app && /app/.venv/bin/python source/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/loader-cron \
    && chmod 0644 /etc/cron.d/loader-cron \
    && crontab /etc/cron.d/loader-cron \
    && touch /var/log/cron.log

# Start cron and keep the container running
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]
