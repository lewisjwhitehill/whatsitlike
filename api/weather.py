from datetime import datetime
from dotenv import load_dotenv

import requests

from api.geocode import geocodeCity
from api.climatology import get_climatology_data
from api.forecast import get_forecast_data
from utils.date_parser import extract_date_range, refine_date_range, format_date_for_api

# load our env vars
load_dotenv()

def get_climatology(city: str, start_date: str, end_date: str):
    """
    Get climatology (historical weather patterns) for a city and date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        return get_climatology_data(city, start_dt, end_dt)
    except ValueError as e:
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch climatology: {str(e)}"}


def get_forecast(city: str, start_date: str, end_date: str):
    """
    Get climatology (historical weather patterns) for a city and date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        return get_forecast_data(city, start_date, end_date)
    except ValueError as e:
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch forecast: {str(e)}"}


def get_city_weather(query: str) -> dict:
    """
    Main function to get weather information for a city based on a natural language query.
    
    Args:
        query: Natural language query like "Costa rica 7/1-7/14" or "New York next week"
    
    Returns:
        Dictionary with weather information
    """
    # Extract location and date range from query
    location, start_date, end_date = extract_date_range(query)
    print(f"Location: {location}, Start Date: {start_date}, End Date: {end_date}")
    
    # Prepare the structured weather data
    if start_date and end_date:

        forecast = None
        climatology = None

        # is it a forecast, climatology or hybrid report
        refined_dates = refine_date_range(start_date, end_date)
        report_type = refined_dates[0]
        
        if report_type == "forecast":
            forecast_start_date, forecast_end_date = refined_dates[1]
            forecast_start_date_str, forecast_end_date_str = format_date_for_api(forecast_start_date, forecast_end_date)
            forecast = get_forecast(location, forecast_start_date_str, forecast_end_date_str)

        elif report_type == "climatology":
            climatology_start_date, climatology_end_date = refined_dates[2]
            climatology_start_date_str, climatology_end_date_str = format_date_for_api(climatology_start_date, climatology_end_date)
            climatology = get_climatology(location, climatology_start_date_str, climatology_end_date_str)

        elif report_type == "hybrid":
            forecast_start_date, forecast_end_date = refined_dates[1]
            forecast_start_date_str, forecast_end_date_str = format_date_for_api(forecast_start_date, forecast_end_date)
            forecast = get_forecast(location, forecast_start_date_str, forecast_end_date_str)

            climatology_start_date, climatology_end_date = refined_dates[2]
            climatology_start_date_str, climatology_end_date_str = format_date_for_api(climatology_start_date, climatology_end_date)
            climatology = get_climatology(location, climatology_start_date_str, climatology_end_date_str)
        else:
            return {
                "report_type": report_type
            }

        return {
            "location": location,
            "date_range": {
                "start": start_date_str,
                "end": end_date_str,
            },
            # keep these for convenience / compatibility
            "start_date": start_date_str,
            "end_date": end_date_str,
            "forecast": forecast,
            "climatology": climatology,
            "report_type": report_type
        }
    else:
        return {"error": "No date range found in query"}
