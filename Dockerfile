FROM python:3.12-slim

WORKDIR /app

RUN apt update \
    && apt install --yes --no-install-recommends \
        curl \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --requirement requirements.txt

# Copy application code
COPY . .

ENV PYTHONPATH=/app:/share

# Expose Streamlit port
EXPOSE 8501

# Start Streamlit app
CMD ["streamlit", "run", "biblioteq/ui/web/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
