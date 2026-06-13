FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip to ensure pre-built wheels are found
RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Uses shell form so Railway can dynamically inject its assigned port number
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
