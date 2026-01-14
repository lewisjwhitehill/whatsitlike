"""
Climatology API wrapper for historical weather data.
Uses Open-Meteo Historical Weather API.
"""
import requests
from datetime import datetime
from typing import Optional
from api.geocode import geocodeCity


def get_climatology_data(
    city: str,
    start_date: datetime,
    end_date: datetime,
    years_back: int = 10
) -> dict:
    """
    Get historical weather data (climatology) for a location and date range.
    
    Args:
        city: City name
        start_date: Start date of the range
        end_date: End date of the range
        years_back: Number of years of historical data to include (default: 10)
    
    Returns:
        Dictionary containing climatology data
    """
    location = geocodeCity(city)
    lat = location.latitude
    lon = location.longitude
    
    # Calculate date range for historical data
    # Get data for the same date range across multiple years
    current_year = datetime.now().year
    start_year = current_year - years_back
    
    # Format dates for API (just month and day, API will use across years)
    start_month_day = start_date.strftime("%m-%d")
    end_month_day = end_date.strftime("%m-%d")
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-{start_month_day}",
        "end_date": f"{current_year}-{end_month_day}",
        "daily": ",".join([
            "weathercode",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_hours",
        ]),
        "timezone": "auto",
    }
    
    try:
        res = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # Calculate averages across all years
        daily_data = data.get("daily", {})
        if daily_data:
            # Calculate statistics
            temps_max = daily_data.get("temperature_2m_max", [])
            temps_min = daily_data.get("temperature_2m_min", [])
            precip = daily_data.get("precipitation_sum", [])
            
            avg_max_temp = sum(temps_max) / len(temps_max) if temps_max else None
            avg_min_temp = sum(temps_min) / len(temps_min) if temps_min else None
            avg_precip = sum(precip) / len(precip) if precip else None
            
            return {
                "location": {
                    "name": location.name,
                    "country": location.country,
                },
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                "climatology": {
                    "average_max_temperature_c": round(avg_max_temp, 1) if avg_max_temp else None,
                    "average_min_temperature_c": round(avg_min_temp, 1) if avg_min_temp else None,
                    "average_precipitation_mm": round(avg_precip, 2) if avg_precip else None,
                    "years_analyzed": years_back,
                },
                "raw_data": daily_data,
            }
        else:
            return {
                "location": {"name": location.name, "country": location.country},
                "error": "No climatology data available",
            }
    except requests.RequestException as e:
        return {
            "location": {"name": location.name, "country": location.country},
            "error": f"Failed to fetch climatology data: {str(e)}",
        }
