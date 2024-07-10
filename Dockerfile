FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY main.py /app/main.py
COPY .env /app/.env
COPY horizon-weather-firebase-admin.json /app/horizon-weather-firebase-admin.json
COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt