from fastapi import FastAPI
from llm.agent import get_city_weather  # your LangChain-powered fn

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
    return await get_city_weather(query)