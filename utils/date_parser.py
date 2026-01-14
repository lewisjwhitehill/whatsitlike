"""
Date parsing utilities for extracting date ranges from natural language queries.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
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


def is_near_term(start_date: Optional[datetime], end_date: Optional[datetime], days_threshold: int = 10) -> bool:
    """
    Determine if a date range is "near-term" (within threshold days from today).
    
    Args:
        start_date: Start date of the range
        end_date: End date of the range
        days_threshold: Number of days to consider as "near-term" (default: 10)
    
    Returns:
        True if the date range is within the threshold, False otherwise
    """
    if start_date is None:
        return False
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    days_until_start = (start_date - today).days
    
    return 0 <= days_until_start <= days_threshold


def format_date_for_api(date: datetime) -> str:
    """
    Format a datetime object for API calls (YYYY-MM-DD format).
    
    Args:
        date: Datetime object to format
    
    Returns:
        Formatted date string
    """
    return date.strftime("%Y-%m-%d")
