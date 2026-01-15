# Initialize the model
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate

from api.weather import get_city_weather

model = init_chat_model('gpt-4o-mini', temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a weather assistant. Your job has three tasks: process the passed in weather information, "
    "reference your own data on the same requested date range, and finally combine the previous two into a helpful"
    "response for someone interested in visited said area during the provided date range."),
    ("user", "Location: {location}\nDate Range: {start_date} to {end_date}\n\nForecast Data: {forecast_data}\nClimatology Data: {climatology_data}\nWeather Events: {events_data}\n\nFormat this into a clear, helpful response with temperatures in both Celsius and Fahrenheit.")
])

# Single LLM call to format response
chain = prompt | model

def format_response(query: str):
    weather_data = get_city_weather(query)

    llmData = {
        
    }

    if weather_data["near"] == 1:


    response = chain.invoke(weather_data)
    
    return response