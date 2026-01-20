"""
Date parsing utilities for extracting date ranges from natural language queries.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from dateutil import parser as date_parser
import re


def extract_date_range(query: str) -> Tuple[Optional[str], Optional[datetime], Optional[datetime]]:
    """
    Extract location and date range from a natural language query.
    
    Args:
        query: User query like "Costa rica 7/1-7/14" or "New York next week"
    
    Returns:
        Tuple of (location, start_date, end_date)
        Returns None for dates if not found or cannot be parsed
    """
    # Try to extract date patterns
    # Pattern 1: "7/1-7/14" or "7/1/2024-7/14/2024"
    date_range_pattern = r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)'
    match = re.search(date_range_pattern, query)
    
    if match:
        start_str = match.group(1)
        end_str = match.group(2)
        try:
            # Parse dates, assume current year if not specified
            start_date = date_parser.parse(start_str, default=datetime.now().replace(month=1, day=1))
            end_date = date_parser.parse(end_str, default=datetime.now().replace(month=1, day=1))
            
            # Remove date portion from query to get location
            location = re.sub(date_range_pattern, '', query).strip()
            return location, start_date, end_date
        except (ValueError, TypeError):
            pass
    
    # Pattern 2: Single date or relative dates like "next week", "July 1-14"
    # Try to find month names and dates
    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:\s*-\s*(\d{1,2}))?'
    match = re.search(month_pattern, query, re.IGNORECASE)
    
    if match:
        month_name = match.group(1)
        start_day = int(match.group(2))
        end_day = int(match.group(3)) if match.group(3) else start_day
        
        # Get current year
        current_year = datetime.now().year
        month_num = datetime.strptime(month_name, "%B").month
        
        start_date = datetime(current_year, month_num, start_day)
        end_date = datetime(current_year, month_num, end_day)
        
        # Remove date portion from query
        location = re.sub(month_pattern, '', query, flags=re.IGNORECASE).strip()
        return location, start_date, end_date
    
    # Pattern 3: Relative dates like "next week", "in 2 weeks"
    relative_patterns = [
        (r'next\s+week', timedelta(weeks=1), timedelta(weeks=2)),
        (r'in\s+(\d+)\s+weeks?', lambda m: timedelta(weeks=int(m.group(1))), lambda m: timedelta(weeks=int(m.group(1))+1)),
    ]
    
    for pattern, start_delta_func, end_delta_func in relative_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            if callable(start_delta_func):
                start_delta = start_delta_func(match)
                end_delta = end_delta_func(match)
            else:
                start_delta = start_delta_func
                end_delta = end_delta_func
            
            today = datetime.now()
            start_date = today + start_delta
            end_date = today + end_delta
            
            location = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
            return location, start_date, end_date
    
    # No date found, return location only
    return query.strip(), None, None


def refine_date_range(start_date: Optional[datetime], end_date: Optional[datetime], days_threshold: int = 10) -> Tuple[Optional[str], Optional[Tuple[datetime, datetime]], Optional[Tuple[datetime, datetime]]]:
    """Split a date range into forecast and climatology sub-ranges when it overlaps.

    This is meant for the edge case where the start date is within the near-term
    forecast window (<= `days_threshold` days from today), but the end date extends
    beyond that window.

    Rules:
    - Forecast range includes dates from start_date up through the threshold day.
    - Climatology range starts the day AFTER the threshold day and runs through end_date.

    Args:
        start_date: Datetime obj start date
        end_date Datetime obj end date
        days_threshold: Near-term cutoff in days from today (default: 10).

    Returns:
        (forecast_range, climatology_range)

        Each range is either:
        - a tuple (start_datetime, end_datetime), or
        - None if that portion does not exist for the input range.

    Raises:
        ValueError: if the date range cannot be parsed.
    """

    # Normalize to date boundaries (midnight).
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    if end_date < start_date:
        raise ValueError("End date is before start date")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    threshold_date = today + timedelta(days=days_threshold)

    forecast_range: Optional[Tuple[datetime, datetime]] = None
    climatology_range: Optional[Tuple[datetime, datetime]] = None
    report_type: Optional[str] = None

    # Entirely in forecast window
    if end_date <= threshold_date:
        forecast_range = (start_date, end_date)
        return "hybrid", forecast_range, None

    # Entirely beyond forecast window (climatology)
    if start_date > threshold_date:
        climatology_range = (start_date, end_date)
        return "climatology", None, climatology_range

    # Overlapping (hybrid)
    forecast_end = min(end_date, threshold_date)
    forecast_range = (start_date, forecast_end)

    clim_start = threshold_date + timedelta(days=1)
    if clim_start <= end_date:
        climatology_range = (clim_start, end_date)

    return "hybrid", forecast_range, climatology_range


def format_date_for_api(date: datetime) -> str:
    """
    Format a datetime object for API calls (YYYY-MM-DD format).
    
    Args:
        date: Datetime object to format
    
    Returns:
        Formatted date string
    """
    return date.strftime("%Y-%m-%d")
