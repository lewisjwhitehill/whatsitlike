import requests
from api.geocode import geocodeCity

def get_forecast_data(city: str, start_date: str, end_date: str):
    """
    Get weather forecast for a city within a date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    location = geocodeCity(city)
    lat = location.latitude
    lon = location.longitude

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "current_weather": "false",
        "daily": ",".join([
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_hours",
        ]),
        "timezone": "auto",
    }
    

    res = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    return data
