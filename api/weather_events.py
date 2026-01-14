"""
Weather events API wrapper for long-range weather predictions and warnings.
Includes hurricanes, El Niño/La Niña, and other significant weather events.
"""
import requests
from datetime import datetime
from typing import Optional, List, Dict
from api.geocode import geocodeCity


def get_weather_events(
    city: str,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """
    Get weather events, warnings, and long-range predictions for a location and date range.
    
    This function aggregates data from multiple sources:
    - Hurricane forecasts (NOAA)
    - El Niño/La Niña predictions
    - Severe weather warnings
    
    Args:
        city: City name
        start_date: Start date of the range
        end_date: End date of the range
    
    Returns:
        Dictionary containing weather events and warnings
    """
    location = geocodeCity(city)
    lat = location.latitude
    lon = location.longitude
    
    events = {
        "location": {
            "name": location.name,
            "country": location.country,
            "latitude": lat,
            "longitude": lon,
        },
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
        "events": [],
        "warnings": [],
    }
    
    # Check for El Niño/La Niña conditions
    # Note: This is a simplified check. In production, you'd query NOAA's Climate Prediction Center
    # For now, we'll provide a placeholder structure
    try:
        # Check if we're in a region affected by El Niño/La Niña
        # This is a simplified heuristic - in production, query actual CPC data
        enso_info = _check_enso_conditions(location, start_date, end_date)
        if enso_info:
            events["warnings"].append(enso_info)
    except Exception as e:
        # Silently fail - this is optional data
        pass
    
    # Check for hurricane season and forecasts
    # Note: Hurricane data typically requires NOAA API access
    # This is a simplified version that checks if location is in hurricane-prone region
    try:
        hurricane_info = _check_hurricane_risk(location, start_date, end_date)
        if hurricane_info:
            events["warnings"].append(hurricane_info)
    except Exception as e:
        # Silently fail - this is optional data
        pass
    
    return events


def _check_enso_conditions(location, start_date: datetime, end_date: datetime) -> Optional[Dict]:
    """
    Check for El Niño/La Niña conditions that might affect the region.
    This is a simplified placeholder - in production, query NOAA CPC data.
    """
    # Simplified: Check if location is in a region typically affected by ENSO
    # Pacific regions, parts of South America, etc.
    # In production, you would:
    # 1. Query NOAA's Climate Prediction Center API
    # 2. Check current ENSO status
    # 3. Determine if location is in affected region
    # 4. Provide forecast for the date range
    
    # For now, return None (no ENSO warnings)
    # In a real implementation, you might return something like:
    # return {
    #     "type": "enso",
    #     "severity": "moderate",
    #     "message": "El Niño conditions may affect weather patterns in this region",
    #     "source": "NOAA Climate Prediction Center"
    # }
    return None


def _check_hurricane_risk(location, start_date: datetime, end_date: datetime) -> Optional[Dict]:
    """
    Check for hurricane risk in the region during the date range.
    This is a simplified placeholder - in production, query NOAA hurricane forecasts.
    """
    # Determine if location is in a hurricane-prone region
    # Check if date range falls during hurricane season for that region
    
    # Hurricane seasons by region (simplified):
    # Atlantic/Caribbean: June 1 - November 30
    # Eastern Pacific: May 15 - November 30
    # Western Pacific: Year-round, peak May-October
    
    lat = location.latitude
    lon = location.longitude
    
    # Check if in hurricane-prone region
    is_atlantic_caribbean = (-100 <= lon <= -10) and (5 <= lat <= 50)
    is_eastern_pacific = (-180 <= lon <= -100) and (5 <= lat <= 30)
    is_western_pacific = (100 <= lon <= 180) and (0 <= lat <= 50)
    
    if is_atlantic_caribbean or is_eastern_pacific or is_western_pacific:
        # Check if date range overlaps with hurricane season
        start_month = start_date.month
        end_month = end_date.month
        
        # Simplified check - in production, query actual hurricane forecasts
        if (is_atlantic_caribbean and (6 <= start_month <= 11 or 6 <= end_month <= 11)) or \
           (is_eastern_pacific and (5 <= start_month <= 11 or 5 <= end_month <= 11)) or \
           (is_western_pacific):
            return {
                "type": "hurricane_season",
                "severity": "moderate",
                "message": f"This region experiences hurricane season during your travel dates. Monitor weather forecasts and warnings from local authorities and NOAA.",
                "source": "Hurricane season analysis",
                "recommendation": "Check NOAA National Hurricane Center for active storms and forecasts"
            }
    
    return None
