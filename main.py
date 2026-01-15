from fastapi import FastAPI
from api.weather import get_city_weather  

app = FastAPI()

@app.get("/weather")
async def weather(query: str):
    """
    Get weather information for a location and date range.
    
    Args:
        query: Natural language query like "Costa rica 7/1-7/14" or "New York next week"
    
    Returns:
        Dictionary with weather information including summary, temperatures, and warnings
    """
    weather_data = await get_city_weather(query)
    return weather_data
    # if weather_data["near"] == 1:
    #     return weather_data["forecast"]
    # else:
    #     return weather_data["climatology"]
