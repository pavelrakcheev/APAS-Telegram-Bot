FROM python:3.12-slim

WORKDIR /app

# Известная проблема v0.1: битая последняя строка requirements.txt — фильтруем
COPY requirements.txt .
RUN grep -v '^google-cloud-aiplatform' requirements.txt > /tmp/requirements-clean.txt \
    && pip install --no-cache-dir -r /tmp/requirements-clean.txt \
    && rm /tmp/requirements-clean.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Данные монтируются из ./data и ./Chats (см. docker-compose.yml)
CMD ["python", "main.py"]
