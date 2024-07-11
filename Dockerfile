FROM python:3.9-slim

COPY main.py /app/main.py
COPY .env /app/.env
COPY horizon-weather-firebase-admin.json /app/horizon-weather-firebase-admin.json
COPY requirements.txt /app/requirements.txt
COPY README.md /app/README.md

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV PORT 8000
ENV HOST 0.0.0.0

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} 