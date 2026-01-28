from datetime import datetime
from dotenv import load_dotenv

import requests

from api.geocode import geocodeCity
from api.climatology import get_climatology_data
from api.forecast import get_forecast_data
from utils.date_parser import extract_date_range, refine_date_range, format_dates_for_api

# load our env vars
load_dotenv()

def get_climatology(city: str, country: str, start_date: str, end_date: str):
    """
    Get climatology (historical weather patterns) for a city and date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        return get_climatology_data(city, country, start_date, end_date)
    except ValueError as e:
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch climatology: {str(e)}"}


def get_forecast(city: str, country: str, start_date: str, end_date: str):
    """
    Get climatology (historical weather patterns) for a city and date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        return get_forecast_data(city, country, start_date, end_date)
    except ValueError as e:
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch forecast: {str(e)}"}


def get_weather(location_name: str, country: str, start_date: datetime, end_date: datetime) -> dict:
    
    forecast = None
    climatology = None

    # is it a forecast, climatology or hybrid report
    refined_dates = refine_date_range(start_date, end_date)
    report_type = refined_dates[0]

    if report_type == "climatology":
        climatology_start_date, climatology_end_date = refined_dates[2]
        climatology = get_climatology(location_name, country, climatology_start_date, climatology_end_date)

    elif report_type == "hybrid":
        forecast_start_date, forecast_end_date = refined_dates[1]
        climatology_start_date, climatology_end_date = refined_dates[2]

        forecast = get_forecast(location_name, country, forecast_start_date, forecast_end_date)
        climatology = get_climatology(location_name, country, climatology_start_date, climatology_end_date)
    else:
        return {
            "report_type": report_type
        }

    start_date, end_date = format_dates_for_api((start_date, end_date))

    return {
        "location": location_name,
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
        # keep these for convenience / compatibility
        "start_date": start_date,
        "end_date": end_date,
        "forecast": forecast,
        "climatology": climatology,
        "report_type": report_type
    }


def parse_and_get_weather(query: str, country: str) -> dict:
    """
    Main function to get weather information for a city based on a natural language query.
    
    Args:
        query: Natural language query like "Costa rica 7/1-7/14" or "New York next week"
    
    Returns:
        Dictionary with weather information
    """
    # parse location and date range from query
    location, start_date, end_date = extract_date_range(query)
    print(f"Location: {location}, Start Date: {start_date}, End Date: {end_date}")
    
    # Prepare the structured weather data
    if start_date and end_date:

        forecast = None
        climatology = None

        # is it a forecast, climatology or hybrid report
        refined_dates = refine_date_range(start_date, end_date)
        report_type = refined_dates[0]

        if report_type == "climatology":
            climatology_start_date, climatology_end_date = refined_dates[2]
            climatology = get_climatology(location, climatology_start_date, climatology_end_date)

        elif report_type == "hybrid":
            forecast_start_date, forecast_end_date = refined_dates[1]
            climatology_start_date, climatology_end_date = refined_dates[2]

            forecast = get_forecast(location, forecast_start_date, forecast_end_date)
            climatology = get_climatology(location, climatology_start_date, climatology_end_date)
        else:
            return {
                "report_type": report_type
            }

        start_date, end_date = format_dates_for_api((start_date, end_date))

        return {
            "location": location,
            "date_range": {
                "start": start_date,
                "end": end_date,
            },
            # keep these for convenience / compatibility
            "start_date": start_date,
            "end_date": end_date,
            "forecast": forecast,
            "climatology": climatology,
            "report_type": report_type
        }
    else:
        return {"error": "No date range found in query"}
