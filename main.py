from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from llm.assistant import formulate_response

class DateRangeRequest(BaseModel):
    location: str
    country: str
    start_date: str
    end_date: str

class ParseDateRangeRequest(BaseModel):
    query: str
    country: str

app = FastAPI()

@app.get("/weather")
async def weather(request: ParseDateRangeRequest):
    query = request.query
    country = request.country
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    if not country.strip():
          raise HTTPException(status_code=400, detail="Country must not be empty")
    try:
        summary = formulate_response(query, country)
    except Exception as e:
        # TODO: add logging here if you want
        raise HTTPException(status_code=500, detail="Failed to generate weather summary")

    return {"summary": summary}

@app.post("/weather/range")
async def weather_range(request: DateRangeRequest):
    try:
        start = datetime.fromisoformat(request.start_date)
        end = datetime.fromisoformat(request.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in ISO format YYYY-MM-DD")

    if start > end:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    query = request.query
    country = request.country

    try:
        summary = formulate_response(query, country, start, end)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate weather summary")

    return {"summary": summary}
