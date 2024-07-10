import asyncio
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
import redis
import httpx
import json
import time
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth

import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

app = FastAPI()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("horizon-weather-firebase-admin.json")
firebase_admin.initialize_app(cred)

# Configure Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# OAuth2 scheme for Firebase token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Global houdini authentication
HOUDINI = os.getenv("HOUDINI") == "true"


def verify_token(token: str):
    """
    Verify the Firebase token to authenticate the user.

    Args:
        token (str): Firebase token.

    Returns:
        str: User ID if token is valid.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    if HOUDINI:
        return "houdini"
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def fetch_weather_data(lat: float, lon: float):
    """
    Fetch current and forecast weather data from OpenWeather API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        tuple: Current weather data and forecast weather data.
    """
    async with httpx.AsyncClient() as client:
        current_weather_response = await client.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}")
        forecast_weather_response = await client.get(
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}")

        current_weather_data = current_weather_response.json()
        forecast_weather_data = forecast_weather_response.json()
        return current_weather_data, forecast_weather_data


async def save_weather_data(user_id: str, lat: float, lon: float):
    """
    Save current and forecast weather data to Redis.

    Args:
        user_id (str): User ID.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    """
    current_weather_data, forecast_weather_data = await fetch_weather_data(lat, lon)
    timestamp = int(time.time())

    # Save current weather data to history
    await r.set(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", json.dumps(current_weather_data))
    # Set expiry to 30 days
    await r.expireat(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", timestamp + 30 * 24 * 3600)
    # Save forecast weather data
    await r.set(f"{user_id}:forecast_data:{lat}:{lon}", json.dumps(forecast_weather_data))


@app.post("/update_weather/")
async def update_weather(lat: float, lon: float, token: str = Depends(oauth2_scheme)):
    """
    Update the weather data for a specific location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        token (str): Firebase token.

    Returns:
        dict: Detail message indicating the weather data update status.
    """
    user_id = verify_token(token)
    await save_weather_data(user_id, lat, lon)
    return {"detail": "Weather data updated"}


@app.get("/weather_data/{lat}/{lon}")
async def get_all_weather_data(lat: float, lon: float, token: str = Depends(oauth2_scheme)):
    """
    Get all historical weather data for a specific location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        token (str): Firebase token.

    Returns:
        list: List of all historical weather data for the specified location.
    """
    user_id = verify_token(token)
    keys = r.keys(f"{user_id}:weather_data:{lat}:{lon}:*")
    data = [json.loads(r.get(key)) for key in keys]
    return data


@app.get("/forecast_data/{lat}/{lon}")
async def get_forecast_data(lat: float, lon: float, token: str = Depends(oauth2_scheme)):
    """
    Get forecast weather data for a specific location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        token (str): Firebase token.

    Returns:
        dict: Forecast weather data or error message if data is not found.
    """
    user_id = verify_token(token)
    data = r.get(f"{user_id}:forecast_data:{lat}:{lon}")
    if data:
        return json.loads(data)
    return {"error": "Data not found"}