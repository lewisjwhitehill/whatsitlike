import requests
from datetime import datetime, date
from api.geocode import geocodeCity

def get_climatology_data(city: str, country: str, start_date: str, end_date: str, years_back: int = 10) -> dict:
    """
    start_date/end_date must be 'YYYY-MM-DD'
    Computes averages for that month/day window across the last `years_back` years.
    """
    location = geocodeCity(city, country)
    lat = location.latitude
    lon = location.longitude
    # convert back to date time as we rely on datetime object fields for computation
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    current_year = date.today().year
    years = list(range(current_year - years_back, current_year))  # exclude current year by default

    temps_max_all: list[float] = []
    temps_min_all: list[float] = []
    precip_all: list[float] = []

    for y in years:
        # Same month/day window in year y
        window_start = date(y, start_dt.month, start_dt.day)
        window_end = date(y, end_dt.month, end_dt.day)

        # If the range crosses year boundary (e.g. Dec 28 - Jan 3)
        if window_end < window_start:
            window_end = date(y + 1, end_dt.month, end_dt.day)

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": window_start.strftime("%Y-%m-%d"),
            "end_date": window_end.strftime("%Y-%m-%d"),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
            ]),
            "timezone": "auto",
        }

        res = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=20)
        res.raise_for_status()
        data = res.json()
        daily = data.get("daily") or {}

        temps_max_all.extend(daily.get("temperature_2m_max") or [])
        temps_min_all.extend(daily.get("temperature_2m_min") or [])
        precip_all.extend(daily.get("precipitation_sum") or [])

    avg_max = (sum(temps_max_all) / len(temps_max_all)) if temps_max_all else None
    avg_min = (sum(temps_min_all) / len(temps_min_all)) if temps_min_all else None
    avg_precip = (sum(precip_all) / len(precip_all)) if precip_all else None

    return {
        "location": {"name": location.name, "country": location.country},
        "date_range": {"start": start_date, "end": end_date},
        "climatology": {
            "average_max_temperature_c": round(avg_max, 1) if avg_max is not None else None,
            "average_min_temperature_c": round(avg_min, 1) if avg_min is not None else None,
            "average_precipitation_mm": round(avg_precip, 2) if avg_precip is not None else None,
            "years_analyzed": years_back,
        },
    }