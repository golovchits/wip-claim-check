FROM python:3.12-slim

WORKDIR /code

# Install dependencies first so Docker can cache this layer between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema.sql .
COPY app ./app
COPY tests ./tests

# Render sets PORT; locally it falls back to 8000.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
