FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and files
COPY app/ ./app/
COPY README.md .
COPY run.sh .

# Prepare data storage directory
RUN mkdir -p /app/data/uploads/inbox

ENV PORT=9035
EXPOSE 9035

VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9035/ || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9035"]
