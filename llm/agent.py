from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
import requests

from api.geocode import geocodeCity
from api.climatology import get_climatology_data
from api.weather_events import get_weather_events
from utils.date_parser import extract_date_range, is_near_term, format_date_for_api

# load our env vars
load_dotenv()

@dataclass
class Context:
    user_id: str

@dataclass
class ResponseFormat:
    summary: str
    temperature_celsius: Optional[float] = None
    temperature_fahrenheit: Optional[float] = None
    humidity: Optional[float] = None
    climatology_info: Optional[str] = None
    weather_warnings: Optional[str] = None


@tool('get_forecast', description='Get current weather forecast for a city and date range. '
      'Use this tool ONLY if the requested date range is within 10 days of today. '
      'Parameters: city (string) - the city name, start_date (string in YYYY-MM-DD format) - start date, '
      'end_date (string in YYYY-MM-DD format) - end date. '
      'Returns detailed forecast data including temperatures, precipitation, and weather codes.',
      return_direct=False)
def get_forecast(city: str, start_date: str, end_date: str):
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
    
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data
    except requests.RequestException as e:
        return {"error": f"Failed to fetch forecast: {str(e)}"}


@tool('get_climatology', description='Get historical weather patterns (climatology) for a city and date range. '
      'Use this tool when the requested date range is MORE than 10 days away from today. '
      'This provides typical weather patterns based on historical data. '
      'Parameters: city (string) - the city name, start_date (string in YYYY-MM-DD format) - start date, '
      'end_date (string in YYYY-MM-DD format) - end date. '
      'Returns average temperatures, precipitation patterns, and typical weather conditions.',
      return_direct=False)
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


@tool('get_weather_events', description='Check for significant weather events, warnings, and long-range predictions '
      'that may affect a location during a date range. This includes hurricanes, El Niño/La Niña conditions, '
      'and other severe weather warnings. Use this tool for ANY date range to check for potential weather events. '
      'Parameters: city (string) - the city name, start_date (string in YYYY-MM-DD format) - start date, '
      'end_date (string in YYYY-MM-DD format) - end date. '
      'Returns warnings and predictions about significant weather events.',
      return_direct=False)
def get_weather_events_tool(city: str, start_date: str, end_date: str):
    """
    Get weather events and warnings for a city and date range.
    
    Args:
        city: City name
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        return get_weather_events(city, start_dt, end_dt)
    except ValueError as e:
        return {"error": f"Invalid date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch weather events: {str(e)}"}


# Initialize the model
model = init_chat_model('gpt-4o-mini', temperature=0.3)

# Checkpointer for conversation memory
checkpointer = InMemorySaver()

# Enhanced system prompt with tool selection logic
system_prompt = """You are a helpful and knowledgeable weather assistant. You help users understand weather conditions 
for locations and date ranges. You have access to three tools:

1. **get_forecast**: Use this for weather forecasts when the date range is within 10 days of today. This provides 
   accurate, detailed forecasts.

2. **get_climatology**: Use this for historical weather patterns when the date range is more than 10 days away. This 
   provides typical weather based on historical data.

3. **get_weather_events**: Always check this tool for any significant weather events, warnings, or long-range 
   predictions (hurricanes, El Niño, etc.) that might affect the location during the date range.

**Your workflow should be:**
1. Parse the user's query to extract the location and date range
2. Determine if the date range is within 10 days (use get_forecast) or further out (use get_climatology)
3. Always check get_weather_events for warnings and significant events
4. Synthesize all information into a clear, helpful response
5. If weather events or warnings are found, make sure to highlight them prominently

Be conversational, helpful, and informative. If you find warnings about hurricanes, El Niño, or other significant 
weather events, make sure to emphasize these in your response. Provide temperature information in both Celsius and 
Fahrenheit when available."""

# Create the agent with all tools
agent = create_agent(
    model=model,
    tools=[get_forecast, get_climatology, get_weather_events_tool],
    system_prompt=system_prompt,
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)


async def get_city_weather(query: str, user_id: str = "default") -> dict:
    """
    Main function to get weather information for a city based on a natural language query.
    
    Args:
        query: Natural language query like "Costa rica 7/1-7/14" or "New York next week"
        user_id: Optional user ID for conversation context
    
    Returns:
        Dictionary with weather information
    """
    # Extract location and date range from query
    location, start_date, end_date = extract_date_range(query)
    
    # Prepare the user message with parsed information
    if start_date and end_date:
        start_date_str = format_date_for_api(start_date)
        end_date_str = format_date_for_api(end_date)
        
        # Format a clear message for the agent with dates in ISO format
        user_message = f"What's the weather like in {location} from {start_date_str} to {end_date_str}?"
    else:
        # No dates found, use original query
        user_message = query
    
    # Use a unique thread ID per user for conversation memory
    config = {'configurable': {'thread_id': user_id}}
    
    # Invoke the agent
    response = agent.invoke(
        {
            'messages': [
                {'role': 'user', 'content': user_message}
            ]
        },
        config=config,
        context=Context(user_id=user_id)
    )
    
    # Extract structured response
    structured_response = response.get('structured_response')
    
    if structured_response:
        return {
            'summary': structured_response.summary,
            'temperature_celsius': structured_response.temperature_celsius,
            'temperature_fahrenheit': structured_response.temperature_fahrenheit,
            'humidity': structured_response.humidity,
            'climatology_info': structured_response.climatology_info,
            'weather_warnings': structured_response.weather_warnings,
        }
    else:
        # Fallback to messages if structured response not available
        messages = response.get('messages', [])
        if messages:
            last_message = messages[-1]
            return {
                'summary': last_message.get('content', 'No response available'),
                'temperature_celsius': None,
                'temperature_fahrenheit': None,
                'humidity': None,
                'climatology_info': None,
                'weather_warnings': None,
            }
        return {
            'summary': 'Unable to retrieve weather information',
            'temperature_celsius': None,
            'temperature_fahrenheit': None,
            'humidity': None,
            'climatology_info': None,
            'weather_warnings': None,
        }
