import threading
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.models import SecuritySchemeType
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, HTTPBasic
from fastapi.middleware.cors import CORSMiddleware
import markdown
import os
import firebase_admin
from firebase_admin import credentials, auth
import redis
import json
import uvicorn
import time
import sqlite3
import httpx
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
HOUDINI = os.getenv("HOUDINI") == "true"

# Check for required environment variables and files
if not API_KEY:
    raise SystemExit("Missing OPENWEATHERMAP_API_KEY in .env file.")

firebase_cert_path = "horizon-weather-firebase-admin.json"
if not os.path.exists(firebase_cert_path):
    raise SystemExit(f"Missing Firebase credentials file: {firebase_cert_path}")

app = FastAPI(
    title="Horizon Weather API",
    description="API for managing weather data with Firebase authentication.",
    version="1.0.0",
    contact={
        "name": "Marco van Staden",
        "email": "mvs2403@gmail.com",
    },
)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_cert_path)
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
    '''CREATE TABLE IF NOT EXISTS weather_data (user_id TEXT, lat REAL, lon REAL, timestamp TEXT, data TEXT)''')
sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS forecast_data (user_id TEXT, lat REAL, lon REAL, data TEXT)''')

# OAuth2 scheme for Firebase token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add CORS middleware
origins = [
    # "http://localhost",
    # "http://localhost:8000",
    "https://horizon-weather.web.app"
    ""
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    if HOUDINI:
        return "houdini"
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/", response_class=HTMLResponse, summary="Read Root", description="Serve the README.md file as styled HTML.")
async def read_root():
    """
    Serve the README.md file as styled HTML.

    Returns:
        HTMLResponse: Rendered HTML content of README.md.
    """

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
        <title>Horizon Weather</title>
        {css_styles}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    return HTMLResponse(content=full_html_content)


class WeatherUpdateResponse(BaseModel):
    detail: str
    timestamp: str


class Coord(BaseModel):
    lon: float
    lat: float


class Weather(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class Main(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: Optional[int]
    grnd_level: Optional[int]


class Wind(BaseModel):
    speed: float
    deg: int
    gust: Optional[float]


class Clouds(BaseModel):
    all: int


class Sys(BaseModel):
    type: Optional[int]
    id: Optional[int]
    country: Optional[str]
    sunrise: Optional[str]
    sunset: Optional[str]


class WeatherDataResponse(BaseModel):
    coord: Coord
    weather: List[Weather]
    base: Optional[str]
    main: Main
    visibility: Optional[int]
    wind: Wind
    clouds: Clouds
    dt: str
    sys: Sys
    timezone: Optional[int]
    id: Optional[int]
    name: Optional[str]
    cod: Optional[int]


class ForecastMain(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    sea_level: int
    grnd_level: int
    humidity: int
    temp_kf: float


class ForecastWeather(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class ForecastClouds(BaseModel):
    all: int


class ForecastWind(BaseModel):
    speed: float
    deg: int
    gust: float


class ForecastSys(BaseModel):
    pod: str


class ForecastListItem(BaseModel):
    dt: int
    main: ForecastMain
    weather: List[ForecastWeather]
    clouds: ForecastClouds
    wind: ForecastWind
    visibility: int
    pop: float
    sys: ForecastSys
    dt_txt: str


class City(BaseModel):
    id: int
    name: str
    coord: Coord
    country: str
    population: int
    timezone: int
    sunrise: int
    sunset: int


class ForecastDataResponse(BaseModel):
    cod: str
    message: int
    cnt: int
    list: List[ForecastListItem]
    city: City


@app.post(
    "/update_weather/",
    summary="Update Weather Data",
    description="Update the weather data for a specific location.",
    response_model=WeatherUpdateResponse,
    responses={
        200: {
            "description": "Weather data updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Weather data updated",
                        "timestamp": "2024-07-11 14:23:00"
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired token"
                    }
                }
            }
        }
    }
)
async def update_weather(lat: float, lon: float, token: str = Depends(oauth2_scheme)):
    """
    Update the weather data for a specific location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        token (str): Firebase token.

    Returns:
        dict: Detail message indicating the weather data update status with a human-readable timestamp.
    """
    user_id = verify_token(token)
    await save_weather_data(user_id, lat, lon)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {"detail": "Weather data updated", "timestamp": timestamp}


@app.get(
    "/weather_data/{lat}/{lon}",
    summary="Current Weather and Historical Weather",
    description="Get up to the last 30 days and the current weather for a specific location.",
    response_model=list[WeatherDataResponse],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "coord": {
                                "lon": 27.9769,
                                "lat": -26.1404
                            },
                            "weather": [
                                {
                                    "id": 800,
                                    "main": "Clear",
                                    "description": "clear sky",
                                    "icon": "01d"
                                }
                            ],
                            "base": "stations",
                            "main": {
                                "temp": 21.96,
                                "feels_like": 20.68,
                                "temp_min": 20.9,
                                "temp_max": 22.28,
                                "pressure": 1018,
                                "humidity": 18,
                                "sea_level": 1018,
                                "grnd_level": 840
                            },
                            "visibility": 10000,
                            "wind": {
                                "speed": 0.89,
                                "deg": 307,
                                "gust": 4.47
                            },
                            "clouds": {
                                "all": 0
                            },
                            "dt": "2024-07-11 14:44:12",
                            "sys": {
                                "type": 2,
                                "id": 2008899,
                                "country": "ZA",
                                "sunrise": "2024-07-11 06:55:14",
                                "sunset": "2024-07-11 17:31:36"
                            },
                            "timezone": 7200,
                            "id": 7870410,
                            "name": "Albertskroon",
                            "cod": 200
                        },
                        {
                            "coord": {
                                "lon": 27.9769,
                                "lat": -26.1404
                            },
                            "weather": [
                                {
                                    "id": 800,
                                    "main": "Clear",
                                    "description": "clear sky",
                                    "icon": "01d"
                                }
                            ],
                            "base": "stations",
                            "main": {
                                "temp": 21.96,
                                "feels_like": 20.68,
                                "temp_min": 20.9,
                                "temp_max": 22.28,
                                "pressure": 1018,
                                "humidity": 18,
                                "sea_level": 1018,
                                "grnd_level": 840
                            },
                            "visibility": 10000,
                            "wind": {
                                "speed": 0.89,
                                "deg": 307,
                                "gust": 4.47
                            },
                            "clouds": {
                                "all": 0
                            },
                            "dt": "2024-07-11 14:44:14",
                            "sys": {
                                "type": 2,
                                "id": 2008899,
                                "country": "ZA",
                                "sunrise": "2024-07-11 06:55:14",
                                "sunset": "2024-07-11 17:31:36"
                            },
                            "timezone": 7200,
                            "id": 7870410,
                            "name": "Albertskroon",
                            "cod": 200
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired token"
                    }
                }
            }
        }
    }
)
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


@app.get(
    "/forecast_data/{lat}/{lon}",
    summary="Forecast Weather Data",
    description="Get forecast weather data for a specific location.",
    response_model=list[ForecastDataResponse],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "cod": "200",
                            "message": 0,
                            "cnt": 40,
                            "list": [
                                {
                                    "dt": 1720710000,
                                    "main": {
                                        "temp": 20.4,
                                        "feels_like": 18.86,
                                        "temp_min": 17.27,
                                        "temp_max": 20.4,
                                        "pressure": 1017,
                                        "sea_level": 1017,
                                        "grnd_level": 840,
                                        "humidity": 14,
                                        "temp_kf": 3.13
                                    },
                                    "weather": [
                                        {
                                            "id": 800,
                                            "main": "Clear",
                                            "description": "clear sky",
                                            "icon": "01d"
                                        }
                                    ],
                                    "clouds": {
                                        "all": 0
                                    },
                                    "wind": {
                                        "speed": 3.63,
                                        "deg": 322,
                                        "gust": 6.39
                                    },
                                    "visibility": 10000,
                                    "pop": 0,
                                    "sys": {
                                        "pod": "d"
                                    },
                                    "dt_txt": "2024-07-11 15:00:00"
                                },
                                {
                                    "dt": 1720720800,
                                    "main": {
                                        "temp": 16.15,
                                        "feels_like": 14.13,
                                        "temp_min": 13.25,
                                        "temp_max": 16.15,
                                        "pressure": 1020,
                                        "sea_level": 1020,
                                        "grnd_level": 839,
                                        "humidity": 12,
                                        "temp_kf": 2.9
                                    },
                                    "weather": [
                                        {
                                            "id": 800,
                                            "main": "Clear",
                                            "description": "clear sky",
                                            "icon": "01n"
                                        }
                                    ],
                                    "clouds": {
                                        "all": 0
                                    },
                                    "wind": {
                                        "speed": 1.58,
                                        "deg": 307,
                                        "gust": 1.9
                                    },
                                    "visibility": 10000,
                                    "pop": 0,
                                    "sys": {
                                        "pod": "n"
                                    },
                                    "dt_txt": "2024-07-11 18:00:00"
                                }
                            ],
                            "city": {
                                "id": 7870410,
                                "name": "Albertskroon",
                                "coord": {
                                    "lat": -26.1404,
                                    "lon": 27.9769
                                },
                                "country": "ZA",
                                "population": 0,
                                "timezone": 7200,
                                "sunrise": 1720673714,
                                "sunset": 1720711896
                            }
                        }
                    ]
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired token"
                    }
                }
            }
        }
    }
)
async def get_forecast_data(lat: float, lon: float, token: str = Depends(oauth2_scheme)):
    """
    Get forecast weather data for a specific location.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        token (str): Firebase token.

    Returns:
        list: Forecast weather data for the specified location.
    """
    user_id = verify_token(token)
    if use_redis:
        data = r.get(f"{user_id}:forecast_data:{lat}:{lon}")
        if data:
            return json.loads(data)
    else:
        sqlite_cursor.execute("SELECT data FROM forecast_data WHERE user_id=? AND lat=? AND lon=?", (user_id, lat, lon))
        rows = sqlite_cursor.fetchall()
        data = [json.loads(row[0]) for row in rows]
    return data


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
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}")
        forecast_weather_response = await client.get(
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}")

        current_weather_data = current_weather_response.json()
        forecast_weather_data = forecast_weather_response.json()
        return current_weather_data, forecast_weather_data


def unix_to_datetime(unix_time, tz_offset):
    """
    Convert Unix timestamp to human-readable datetime string with timezone adjustment.

    Args:
        unix_time (int): Unix timestamp.
        tz_offset (int): Timezone offset in seconds.

    Returns:
        str: Human-readable datetime string.
    """
    tz = timezone(timedelta(seconds=tz_offset))
    return datetime.fromtimestamp(unix_time, tz).strftime('%Y-%m-%d %H:%M:%S')


async def save_weather_data(user_id: str, lat: float, lon: float):
    """
    Save current and forecast weather data to Redis or SQLite.

    Args:
        user_id (str): User ID.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    """
    current_weather_data, forecast_weather_data = await fetch_weather_data(lat, lon)

    # Convert Unix timestamps to human-readable datetime with timezone adjustment
    tz_offset = current_weather_data["timezone"]
    current_weather_data["dt"] = unix_to_datetime(current_weather_data["dt"], tz_offset)
    current_weather_data["sys"]["sunrise"] = unix_to_datetime(current_weather_data["sys"]["sunrise"], tz_offset)
    current_weather_data["sys"]["sunset"] = unix_to_datetime(current_weather_data["sys"]["sunset"], tz_offset)

    timestamp = int(time.time())
    if use_redis:
        await r.set(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", json.dumps(current_weather_data))
        await r.expireat(f"{user_id}:weather_data:{lat}:{lon}:{timestamp}", timestamp + 30 * 24 * 3600)
        await r.set(f"{user_id}:forecast_data:{lat}:{lon}", json.dumps(forecast_weather_data))
    else:
        sqlite_cursor.execute("INSERT INTO weather_data (user_id, lat, lon, timestamp, data) VALUES (?, ?, ?, ?, ?)",
                              (user_id, lat, lon, timestamp, json.dumps(current_weather_data)))
        sqlite_cursor.execute("INSERT INTO forecast_data (user_id, lat, lon, data) VALUES (?, ?, ?, ?)",
                              (user_id, lat, lon, json.dumps(forecast_weather_data)))
        sqlite_conn.commit()


def janitor_bot():
    """
    JanitorBot: Cleans up old weather data from the SQLite database.

    Deletes weather data older than 30 days to manage the database size.
    """
    while True:
        sqlite_cleanup_conn = sqlite3.connect(':memory:')
        sqlite_cleanup_cursor = sqlite_cleanup_conn.cursor()

        cutoff_timestamp = int(time.time()) - 30 * 24 * 3600
        sqlite_cleanup_cursor.execute("DELETE FROM weather_data WHERE timestamp < ?", (cutoff_timestamp,))
        sqlite_cleanup_conn.commit()

        sqlite_cleanup_conn.close()
        time.sleep(24 * 3600)  # Run the cleanup process once a day


# Start the JanitorBot cleanup thread
# cleanup_thread = threading.Thread(target=janitor_bot, daemon=True)
# cleanup_thread.start()
# TODO: Does not Work (Not thread safe)

# Define OpenAPI schema with Bearer authentication
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = app._original_openapi()
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",  # Use string directly instead of SecuritySchemeType.http
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    routes_with_auth = ["/update_weather/", "/weather_data/{lat}/{lon}", "/forecast_data/{lat}/{lon}"]
    for route in routes_with_auth:
        if route in openapi_schema["paths"]:
            for method in openapi_schema["paths"][route]:
                openapi_schema["paths"][route][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Store the original app.openapi method
app._original_openapi = app.openapi

# Override the app.openapi method with the custom one
app.openapi = custom_openapi

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
