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
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_hours",
        ]),
        "timezone": "auto",
    }

    # Request to Open Meteo
    res = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    res.raise_for_status()
    data = res.json()

    daily = data["daily"]
    days = []

    for i, date in enumerate(daily["time"]):
        days.append({
            "date": date,
            "weather_code": daily["weather_code"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "precip_mm": daily["precipitation_sum"][i],
            "precip_hours": daily["precipitation_hours"][i],
        })

    # ---- Summary stats for the requested forecast window (computed in Python) ----
    temps_max = [v for v in daily.get("temperature_2m_max", []) if v is not None]
    temps_min = [v for v in daily.get("temperature_2m_min", []) if v is not None]
    precips = [v for v in daily.get("precipitation_sum", []) if v is not None]

    avg_max_temperature_c = (sum(temps_max) / len(temps_max)) if temps_max else None
    avg_min_temperature_c = (sum(temps_min) / len(temps_min)) if temps_min else None

    total_precipitation_mm = sum(precips) if precips else None
    days_with_precip_mm_gt_0 = sum(1 for v in precips if v > 0) if precips else None

    if precips:
        max_precipitation_mm_in_a_day = max(precips)
        max_idx = daily["precipitation_sum"].index(max_precipitation_mm_in_a_day)
        date_of_max_precipitation = daily["time"][max_idx]
    else:
        max_precipitation_mm_in_a_day = None
        date_of_max_precipitation = None


    return {
        "daily" : days,
        "summary" : {
            "avg_max_temperature_c": round(avg_max_temperature_c, 1) if avg_max_temperature_c is not None else None,
            "avg_min_temperature_c": round(avg_min_temperature_c, 1) if avg_min_temperature_c is not None else None,
            "total_precipitation_mm": round(total_precipitation_mm, 2) if total_precipitation_mm is not None else None,
            "days_with_precip_mm_gt_0": days_with_precip_mm_gt_0,
            "max_precipitation_mm_in_a_day": round(max_precipitation_mm_in_a_day, 2) if max_precipitation_mm_in_a_day is not None else None,
            "date_of_max_precipitation": date_of_max_precipitation
        }
    }

  
  
