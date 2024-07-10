from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
import markdown
import os
import firebase_admin
from firebase_admin import credentials, auth
import redis
import json
import time
import sqlite3
import httpx

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BYPASS_AUTH = os.getenv("BYPASS_AUTH") == "true"

app = FastAPI()

# Initialize Firebase Admin SDK
cred = credentials.Certificate("horizon-weather-firebase-admin.json")
firebase_admin.initialize_app(cred)

# Attempt to configure Redis connection
use_redis = True
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
except redis.ConnectionError:
    use_redis = False

# Configure SQLite as fallback
sqlite_conn = sqlite3.connect(':memory:')
sqlite_cursor = sqlite_conn.cursor()

# Create tables for SQLite
sqlite_cursor.execute(
    '''CREATE TABLE IF NOT EXISTS weather_data (user_id TEXT, lat REAL, lon REAL, timestamp INTEGER, data TEXT)''')
sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS forecast_data (user_id TEXT, lat REAL, lon REAL, data TEXT)''')

# OAuth2 scheme for Firebase token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_token(token: str = None):
    """
    Verify the Firebase token to authenticate the user.

    Args:
        token (str): Firebase token.

    Returns:
        str: User ID if token is valid, or dummy user ID if bypassing auth.

    Raises:
        HTTPException: If token is invalid or expired and not bypassing auth.
    """
    if BYPASS_AUTH:
        return "development_user"
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/", response_class=HTMLResponse)
async def read_root(token: str = Depends(oauth2_scheme)):
    """
    Serve the README.md file as styled HTML.

    Args:
        token (str): Firebase token.

    Returns:
        HTMLResponse: Rendered HTML content of README.md.
    """
    user_id = verify_token(token)

    # Define the path to the README.md file
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")

    # Read the contents of the README.md file
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Convert the Markdown content to HTML
    html_content = markdown.markdown(readme_content)

    # Define your CSS styles
    css_styles = """
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1, h2, h3 {
            color: #333;
        }
        p {
            color: #666;
        }
        code {
            background-color: #eee;
            padding: 2px 4px;
            border-radius: 4px;
        }
        pre {
            background-color: #eee;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        a {
            color: #1e90ff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
    """

    # Inject the CSS styles into the HTML content
    full_html_content = f"""
    <html>
    <head>
        <title>README</title>
        {css_styles}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    return HTMLResponse(content=full_html_content)


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
    if use_redis:
        keys = r.keys(f"{user_id}:weather_data:{lat}:{lon}:*")
        data = [json.loads(r.get(key)) for key in keys]
    else:
        sqlite_cursor.execute("SELECT data FROM weather_data WHERE user_id=? AND lat=? AND lon=?", (user_id, lat, lon))
        rows = sqlite_cursor.fetchall()
        data = [json.loads(row[0]) for row in rows]
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
    if use_redis:
        data = r.get(f"{user_id}:forecast_data:{lat}:{lon}")
        if data:
            return json.loads(data)
    else:
        sqlite_cursor.execute("SELECT data FROM forecast_data WHERE user_id=? AND lat=? AND lon=?", (user_id, lat, lon))
        row = sqlite_cursor.fetchone()
        if row:
            return json.loads(row[0])
    return {"error": "Data not found"}


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
    Save current and forecast weather data to Redis or SQLite.

    Args:
        user_id (str): User ID.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    """
    current_weather_data, forecast_weather_data = await fetch_weather_data(lat, lon)
    timestamp = int(time.time())
    if use_redis:
        await r.set(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", json.dumps(current_weather_data))
        await r.expireat(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", timestamp + 30 * 24 * 3600)
        await r.set(f"{user_id}:forecast_data:{lat}:{lon}", json.dumps(forecast_weather_data))
    else:
        sqlite_cursor.execute("INSERT INTO weather_data (user_id, lat, lon, timestamp, data) VALUES (?, ?, ?, ?, ?)",
                              (user_id, lat, lon, timestamp, json.dumps(current_weather_data)))
        sqlite_cursor.execute("INSERT INTO forecast_data (user_id, lat, lon, data) VALUES (?, ?, ?)",
                              (user_id, lat, lon, json.dumps(forecast_weather_data)))
        sqlite_conn.commit()