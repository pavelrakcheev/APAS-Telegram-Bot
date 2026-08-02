FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Данные пользователей монтируются в /data (см. docker-compose.yml,
# app.py ищет ../data/users_data.json)
EXPOSE 5000

CMD ["gunicorn", "app:app"]
