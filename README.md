## Overview

This FastAPI application is designed to provide weather data services. It allows authenticated users to fetch, store, and retrieve weather data for specific locations. The API integrates with Firebase for user authentication and uses Redis for data storage. It fetches weather data from the OpenWeather API.

### Key Components

1. **Authentication**: Uses Firebase tokens to authenticate users.
2. **Weather Data Fetching**: Retrieves current and forecast weather data from the OpenWeather API.
3. **Data Storage**: Stores weather data in Redis, allowing retrieval of historical data and forecast data.

### Endpoints

#### 1. **Update Weather Data**
- **Endpoint**: `/update_weather/`
- **Method**: `POST`
- **Parameters**:
  - `lat` (float): Latitude of the location.
  - `lon` (float): Longitude of the location.
  - `token` (str): Firebase token for authentication.
- **Description**: Fetches the current and forecast weather data for the specified location and stores it in Redis. The data is stored with an expiry of 30 days.
- **Returns**: A message indicating that the weather data has been updated.

#### 2. **Get All Historical Weather Data**
- **Endpoint**: `/weather_data/{lat}/{lon}`
- **Method**: `GET`
- **Parameters**:
  - `lat` (float): Latitude of the location.
  - `lon` (float): Longitude of the location.
  - `token` (str): Firebase token for authentication.
- **Description**: Retrieves all historical weather data for the specified location from Redis.
- **Returns**: A list of all historical weather data for the specified location.

#### 3. **Get Forecast Weather Data**
- **Endpoint**: `/forecast_data/{lat}/{lon}`
- **Method**: `GET`
- **Parameters**:
  - `lat` (float): Latitude of the location.
  - `lon` (float): Longitude of the location.
  - `token` (str): Firebase token for authentication.
- **Description**: Retrieves the forecast weather data for the specified location from Redis.
- **Returns**: The forecast weather data or an error message if data is not found.

### How It Works

1. **Authentication**: 
   - The API uses Firebase for user authentication. Users must provide a valid Firebase token to access the endpoints. The `verify_token` function checks the token's validity and extracts the user ID.

2. **Fetching Weather Data**:
   - The `fetch_weather_data` function makes asynchronous requests to the OpenWeather API to get the current and forecast weather data for the given latitude and longitude.

3. **Saving Weather Data**:
   - The `save_weather_data` function stores the fetched weather data in Redis. Current weather data is saved with a timestamp and set to expire after 30 days. Forecast weather data is also saved.

4. **Updating Weather Data**:
   - The `/update_weather/` endpoint allows users to update the weather data for a specific location. It verifies the user's token, fetches the weather data, and saves it to Redis.

5. **Retrieving Historical Weather Data**:
   - The `/weather_data/{lat}/{lon}` endpoint allows users to retrieve all historical weather data for a specific location. It verifies the user's token and fetches the data from Redis.

6. **Retrieving Forecast Data**:
   - The `/forecast_data/{lat}/{lon}` endpoint allows users to retrieve the forecast weather data for a specific location. It verifies the user's token and fetches the data from Redis.

### Example Use Case

A user wants to keep track of the weather at a specific location over time. They can use the `/update_weather/` endpoint to periodically fetch and store the weather data. Later, they can use the `/weather_data/{lat}/{lon}` endpoint to retrieve all historical weather data or the `/forecast_data/{lat}/{lon}` endpoint to get the latest forecast.

This API is useful for applications that need to provide weather information to authenticated users, such as weather tracking apps, travel planning tools, or personalized weather notifications.

# Automated Setup
For the automated setup and cleanup process see `README_AUTOMATION.md` on how to use the `deploy.sh` and `order66.sh` scripts.